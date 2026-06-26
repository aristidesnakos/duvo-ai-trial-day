"""normalize_uom + three_way_match.

The three-way match is the heart of the analysis: PO -> GRN -> Invoice joined on
po_id + sku. UoM is normalized to a common base unit BEFORE any euro comparison,
so the SUP-003 dairy case (priced per case = 12 units) reconciles instead of
firing a phantom price gap.
"""
from __future__ import annotations

from typing import List, Optional

from . import config
from .loader import PeriodData
from .models import DerivedClaim


def normalize_uom(qty: float, unit_price: float, uom: str, units_per_case: int):
    """Convert a (qty, unit_price) line to base units.

    Returns (base_qty, base_unit_price, note). For a 'case' line under a contract
    that quotes N units/case, qty is multiplied and unit price divided by N, so
    the two sides of a comparison are denominated identically.
    """
    if uom.lower() == "case" and units_per_case > 1:
        base_qty = qty * units_per_case
        base_price = unit_price / units_per_case
        note = f"{qty:g} case × {units_per_case} units = {base_qty:g} units @ {config.eur(base_price)}/unit"
        return base_qty, base_price, note
    return qty, unit_price, f"{qty:g} {uom} @ {config.eur(unit_price)}"


def _grns_for(po_id: str, grns) -> list:
    return [g for g in grns if g.po_id == po_id]


def _invoices_for(po_id: str, invoices) -> list:
    return [i for i in invoices if i.po_id == po_id]


def _weaker(*confidences) -> str:
    """Return the weakest confidence among the inputs (low < medium < high)."""
    rank = {"low": 0, "medium": 1, "high": 2}
    return min(confidences, key=lambda c: rank.get(c, 0))


def three_way_match(data: PeriodData) -> List[DerivedClaim]:
    """Derive short-delivery, damage and price-gap claims for every PO."""
    claims: List[DerivedClaim] = []
    contracts = data.contract_by_supplier()

    for po in data.purchase_orders:
        contract = contracts.get(po.supplier_id)
        upc = contract.units_per_case if contract else 1
        grns_matched = _grns_for(po.po_id, data.goods_receipts)
        invs_matched = _invoices_for(po.po_id, data.invoices)

        # Missing GRN => cannot substantiate receipt; never fabricate a claim.
        if not grns_matched:
            inv_id = invs_matched[0].invoice_id if invs_matched else None
            claims.append(DerivedClaim(
                po_id=po.po_id, supplier_id=po.supplier_id, supplier_name=po.supplier_name,
                claim_type="no_evidence", eur_amount=0.0,
                line_math=f"No goods-receipt row exists for {po.po_id}; receipt unverifiable — not claimable.",
                evidence={"po": po.po_id, "grn": None, "invoice": inv_id},
                uom_normalized=False, confidence="high", period=data.period,
            ))
            continue

        # Multiple GRNs/invoices per PO (partial deliveries) => aggregate qty and
        # lower confidence rather than silently using only the first row.
        multi = len(grns_matched) > 1 or len(invs_matched) > 1
        base_conf = "medium" if multi else "high"

        # PO ordered outside its contract window => terms may not apply; flag it.
        c_start = config.parse_date(contract.contract_start) if contract else None
        c_end = config.parse_date(contract.contract_end) if contract else None
        po_date = config.parse_date(po.order_date)
        out_of_contract = (po_date is not None and
                           ((c_start and po_date < c_start) or (c_end and po_date > c_end)))
        if out_of_contract:
            base_conf = _weaker(base_conf, "medium")
        contract_caveat = (f" ⚠ PO ordered {po.order_date} outside contract window "
                           f"{contract.contract_start}→{contract.contract_end}") if out_of_contract else ""

        grn = grns_matched[0]  # representative row for condition/notes
        normalized = (po.uom.lower() == "case" and upc > 1)
        po_qty, po_price, po_note = normalize_uom(po.qty_ordered, po.unit_price_eur, po.uom, upc)
        grn_qty = sum(normalize_uom(g.qty_received, 0.0, g.uom, upc)[0] for g in grns_matched)

        if invs_matched:
            inv = invs_matched[0]  # representative for unit price
            inv_qty = sum(normalize_uom(i.qty_invoiced, 0.0, i.uom, upc)[0] for i in invs_matched)
            _, inv_price, inv_note = normalize_uom(inv.qty_invoiced, inv.unit_price_eur, inv.uom, upc)
        else:
            inv = None
            inv_qty = inv_price = 0.0
            inv_note = "no invoice"

        evidence = {
            "po": {"po_id": po.po_id, "qty": po.qty_ordered, "uom": po.uom,
                   "unit_price_eur": po.unit_price_eur, "normalized": po_note},
            "grn": {"grn_ids": [g.grn_id for g in grns_matched], "qty_received_total": grn_qty,
                    "condition": grn.condition, "notes": grn.notes},
            "invoice": ({"invoice_ids": [i.invoice_id for i in invs_matched],
                         "invoice_id": inv.invoice_id, "qty_total": inv_qty, "uom": inv.uom,
                         "unit_price_eur": inv.unit_price_eur, "normalized": inv_note}
                        if inv else None),
        }

        disp = "units" if normalized else po.uom  # label the arithmetic in real units

        # --- Short delivery: billed for more than was received. ---
        if inv is not None and inv_qty > grn_qty + 1e-9:
            short_units = inv_qty - grn_qty
            amount = short_units * po_price
            claims.append(DerivedClaim(
                po_id=po.po_id, supplier_id=po.supplier_id, supplier_name=po.supplier_name,
                claim_type="short_delivery", eur_amount=round(amount, 2),
                line_math=(f"Invoiced {inv_qty:g} {disp} but GRN received {grn_qty:g} "
                           f"({grn.notes or 'short'}); billed for {short_units:g} undelivered "
                           f"× {config.eur(po_price)} = {config.eur(amount)}{contract_caveat}"),
                evidence=evidence, uom_normalized=normalized, confidence=base_conf, period=data.period,
            ))

        # --- Damage: GRN flagged Damaged with a quantity ANCHORED in the notes. ---
        if grn.condition.strip().lower() == "damaged":
            dmg_qty, dmg_conf = config.damage_qty_from_note(grn.notes, grn.uom)
            if dmg_qty:
                # Damage qty is stated in the GRN's own uom; price in same uom.
                amount = dmg_qty * po.unit_price_eur
                claims.append(DerivedClaim(
                    po_id=po.po_id, supplier_id=po.supplier_id, supplier_name=po.supplier_name,
                    claim_type="damage", eur_amount=round(amount, 2),
                    line_math=(f"GRN condition Damaged: {dmg_qty} {grn.uom} "
                               f"({grn.notes}) × {config.eur(po.unit_price_eur)}/{grn.uom} "
                               f"= {config.eur(amount)}{contract_caveat}"),
                    evidence=evidence, uom_normalized=normalized,
                    confidence=_weaker(base_conf, dmg_conf), period=data.period,
                ))

        # --- Price gap: invoice unit price above agreed (PO/contract) price. ---
        if inv is not None and inv_price > po_price + 1e-9:
            amount = (inv_price - po_price) * inv_qty
            claims.append(DerivedClaim(
                po_id=po.po_id, supplier_id=po.supplier_id, supplier_name=po.supplier_name,
                claim_type="price_gap", eur_amount=round(amount, 2),
                line_math=(f"Invoice {config.eur(inv_price)}/{disp} vs agreed {config.eur(po_price)}/{disp} "
                           f"= {config.eur(inv_price - po_price)} × {inv_qty:g} {disp} invoiced "
                           f"= {config.eur(amount)}{contract_caveat}"),
                evidence=evidence, uom_normalized=normalized, confidence=base_conf, period=data.period,
            ))

    return claims
