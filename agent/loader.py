"""load_period_data — read + validate the 5 CSVs and scope them to a period.

Read-only on data/. Fails loud on a schema mismatch (SPEC guardrail: the CSVs
were not provided when the spec was written, so we validate columns up front).
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from typing import List

from . import config
from .models import (
    Contract, GoodsReceipt, Invoice, PurchaseOrder, TrackerRow,
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

REQUIRED_COLUMNS = {
    "purchase_orders.csv": {"po_id", "supplier_id", "sku", "uom", "qty_ordered",
                             "unit_price_eur", "po_total_eur", "order_date"},
    "good_receipts.csv": {"grn_id", "po_id", "supplier_id", "sku", "uom",
                           "qty_received", "condition", "notes"},
    "invoices.csv": {"invoice_id", "supplier_id", "po_id", "sku", "uom",
                     "qty_invoiced", "unit_price_eur", "invoice_total_eur"},
    "supplier_contracts.csv": {"supplier_id", "volume_bonus_threshold_eur_qtr",
                               "volume_bonus_pct", "promo_funding_eur_qtr", "notes"},
    "supplier_claims_tracker.csv": {"claim_id", "supplier", "invoice_ref",
                                     "po_ref", "claim_type", "claim_amount_eur",
                                     "status", "owner", "notes"},
}


@dataclass
class PeriodData:
    period: str
    purchase_orders: List[PurchaseOrder]
    goods_receipts: List[GoodsReceipt]
    invoices: List[Invoice]
    contracts: List[Contract]
    tracker: List[TrackerRow]          # all rows, with in_period flag
    excluded_tracker: List[TrackerRow] # out-of-period rows, for transparency

    def contract_by_supplier(self):
        return {c.supplier_id: c for c in self.contracts}


def _read(filename: str):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        cols = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS[filename] - cols
        if missing:
            raise ValueError(f"{filename}: missing required columns {sorted(missing)}")
        return list(reader)


def _f(row, key, default=0.0):
    v = (row.get(key) or "").strip()
    return float(v) if v else default


def load_period_data(period: str = config.PERIOD_LABEL) -> PeriodData:
    pos = [PurchaseOrder(
        po_id=r["po_id"], supplier_id=r["supplier_id"], supplier_name=r.get("supplier_name", ""),
        order_date=r["order_date"], sku=r["sku"], description=r.get("description", ""),
        uom=r["uom"], qty_ordered=_f(r, "qty_ordered"), unit_price_eur=_f(r, "unit_price_eur"),
        po_total_eur=_f(r, "po_total_eur"),
    ) for r in _read("purchase_orders.csv")]

    grns = [GoodsReceipt(
        grn_id=r["grn_id"], po_id=r["po_id"], supplier_id=r["supplier_id"],
        receipt_date=r.get("receipt_date", ""), sku=r["sku"], uom=r["uom"],
        qty_received=_f(r, "qty_received"), condition=r["condition"], notes=r.get("notes", ""),
    ) for r in _read("good_receipts.csv")]

    invs = [Invoice(
        invoice_id=r["invoice_id"], supplier_id=r["supplier_id"], supplier_name=r.get("supplier_name", ""),
        invoice_date=r.get("invoice_date", ""), po_id=r["po_id"], sku=r["sku"], uom=r["uom"],
        qty_invoiced=_f(r, "qty_invoiced"), unit_price_eur=_f(r, "unit_price_eur"),
        invoice_total_eur=_f(r, "invoice_total_eur"), date_received=r.get("date_received", ""),
    ) for r in _read("invoices.csv")]

    contracts = [Contract(
        supplier_id=r["supplier_id"], supplier_name=r.get("supplier_name", ""),
        contract_start=r.get("contract_start", ""), contract_end=r.get("contract_end", ""),
        payment_terms_days=int(_f(r, "payment_terms_days")),
        volume_bonus_threshold_eur_qtr=_f(r, "volume_bonus_threshold_eur_qtr"),
        volume_bonus_pct=_f(r, "volume_bonus_pct"),
        promo_funding_eur_qtr=_f(r, "promo_funding_eur_qtr"),
        notes=r.get("notes", ""),
        units_per_case=config.units_per_case_from_note(r.get("notes", "")),
    ) for r in _read("supplier_contracts.csv")]

    tracker_all, excluded = [], []
    for r in _read("supplier_claims_tracker.csv"):
        amt = (r.get("claim_amount_eur") or "").strip()
        d = config.parse_date(r.get("date_logged", ""))
        # Q4 row: dated before the period, references an invoice not in this period.
        within = config.in_period(d)
        row = TrackerRow(
            claim_id=r["claim_id"], date_logged=r.get("date_logged", ""),
            supplier=r["supplier"], invoice_ref=r.get("invoice_ref", ""),
            po_ref=r.get("po_ref", ""), claim_type=r["claim_type"],
            claim_amount_eur=float(amt) if amt else None,
            status_raw=r["status"], status_norm=config.normalize_status(r["status"]),
            owner=r.get("owner", ""), notes=r.get("notes", ""), in_period=within,
        )
        tracker_all.append(row)
        if not within:
            excluded.append(row)

    return PeriodData(
        period=period,
        purchase_orders=[p for p in pos if config.in_period(config.parse_date(p.order_date))],
        goods_receipts=grns,
        invoices=invs,
        contracts=contracts,
        tracker=[t for t in tracker_all if t.in_period],
        excluded_tracker=excluded,
    )
