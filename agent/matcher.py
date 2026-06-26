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


def _grn_for(po_id: str, grns) -> Optional[object]:
    matches = [g for g in grns if g.po_id == po_id]
    return matches[0] if matches else None


def _invoice_for(po_id: str, invoices) -> Optional[object]:
    matches = [i for i in invoices if i.po_id == po_id]
    return matches[0] if matches else None


def three_way_match(data: PeriodData) -> List[DerivedClaim]:
    """Derive short-delivery, damage and price-gap claims for every PO."""
    claims: List[DerivedClaim] = []
    contracts = data.contract_by_supplier()

    for po in data.purchase_orders:
        contract = contracts.get(po.supplier_id)
        upc = contract.units_per_case if contract else 1
        grn = _grn_for(po.po_id, data.goods_receipts)
        inv = _invoice_for(po.po_id, data.invoices)

        # Missing GRN => cannot substantiate receipt; never fabricate a claim.
        if grn is None:
            claims.append(DerivedClaim(
                po_id=po.po_id, supplier_id=po.supplier_id, supplier_name=po.supplier_name,
                claim_type="no_evidence", eur_amount=0.0,
                line_math=f"No goods-receipt row exists for {po.po_id}; receipt unverifiable — not claimable.",
                evidence={"po": po.po_id, "grn": None, "invoice": inv.invoice_id if inv else None},
                uom_normalized=False, confidence="high", period=data.period,
            ))
            continue

        # Normalize PO, GRN, Invoice to base units.
        po_qty, po_price, po_note = normalize_uom(po.qty_ordered, po.unit_price_eur, po.uom, upc)
        grn_qty, _, _ = normalize_uom(grn.qty_received, 0.0, grn.uom, upc)
        normalized = (po.uom.lower() == "case" and upc > 1)

        if inv is not None:
            inv_qty, inv_price, inv_note = normalize_uom(
                inv.qty_invoiced, inv.unit_price_eur, inv.uom, upc)
        else:
            inv_qty = inv_price = 0.0
            inv_note = "no invoice"

        evidence = {
            "po": {"po_id": po.po_id, "qty": po.qty_ordered, "uom": po.uom,
                   "unit_price_eur": po.unit_price_eur, "normalized": po_note},
            "grn": {"grn_id": grn.grn_id, "qty_received": grn.qty_received,
                    "condition": grn.condition, "notes": grn.notes},
            "invoice": ({"invoice_id": inv.invoice_id, "qty": inv.qty_invoiced, "uom": inv.uom,
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
                           f"× {config.eur(po_price)} = {config.eur(amount)}"),
                evidence=evidence, uom_normalized=normalized, confidence="high", period=data.period,
            ))

        # --- Damage: GRN flagged Damaged with a quantity in notes. ---
        if grn.condition.strip().lower() == "damaged":
            dmg_units_raw = config.first_int(grn.notes)
            if dmg_units_raw:
                # Damage qty is stated in the GRN's own uom; price in same uom.
                amount = dmg_units_raw * po.unit_price_eur
                claims.append(DerivedClaim(
                    po_id=po.po_id, supplier_id=po.supplier_id, supplier_name=po.supplier_name,
                    claim_type="damage", eur_amount=round(amount, 2),
                    line_math=(f"GRN condition Damaged: {dmg_units_raw} {grn.uom} "
                               f"({grn.notes}) × {config.eur(po.unit_price_eur)}/{grn.uom} "
                               f"= {config.eur(amount)}"),
                    evidence=evidence, uom_normalized=normalized, confidence="high", period=data.period,
                ))

        # --- Price gap: invoice unit price above agreed (PO/contract) price. ---
        if inv is not None and inv_price > po_price + 1e-9:
            amount = (inv_price - po_price) * inv_qty
            claims.append(DerivedClaim(
                po_id=po.po_id, supplier_id=po.supplier_id, supplier_name=po.supplier_name,
                claim_type="price_gap", eur_amount=round(amount, 2),
                line_math=(f"Invoice {config.eur(inv_price)}/{disp} vs agreed {config.eur(po_price)}/{disp} "
                           f"= {config.eur(inv_price - po_price)} × {inv_qty:g} {disp} invoiced "
                           f"= {config.eur(amount)}"),
                evidence=evidence, uom_normalized=normalized, confidence="high", period=data.period,
            ))

    return claims
