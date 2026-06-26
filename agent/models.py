"""Typed records for the supplier-claims reconciliation agent.

Every shape here mirrors SPEC.md section 6. Kept as plain dataclasses (stdlib
only) so the whole engine is dependency-free and the arithmetic stays auditable.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Source rows (one dataclass per CSV) — loaded verbatim, lightly typed.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PurchaseOrder:
    po_id: str
    supplier_id: str
    supplier_name: str
    order_date: str
    sku: str
    description: str
    uom: str
    qty_ordered: float
    unit_price_eur: float
    po_total_eur: float


@dataclass(frozen=True)
class GoodsReceipt:
    grn_id: str
    po_id: str
    supplier_id: str
    receipt_date: str
    sku: str
    uom: str
    qty_received: float
    condition: str
    notes: str


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    supplier_id: str
    supplier_name: str
    invoice_date: str
    po_id: str
    sku: str
    uom: str
    qty_invoiced: float
    unit_price_eur: float
    invoice_total_eur: float
    date_received: str


@dataclass(frozen=True)
class Contract:
    supplier_id: str
    supplier_name: str
    contract_start: str
    contract_end: str
    payment_terms_days: int
    volume_bonus_threshold_eur_qtr: float
    volume_bonus_pct: float
    promo_funding_eur_qtr: float
    notes: str
    # Derived from the free-text note (e.g. "12 units/case"); 1 if not stated.
    units_per_case: int = 1


@dataclass(frozen=True)
class TrackerRow:
    claim_id: str
    date_logged: str            # raw, may be DD/MM/YYYY or YYYY-MM-DD
    supplier: str               # raw, inconsistent spelling/casing
    invoice_ref: str
    po_ref: str
    claim_type: str
    claim_amount_eur: Optional[float]   # None when blank
    status_raw: str
    status_norm: str            # normalized: OPEN | IN_PROGRESS | PAID
    owner: str
    notes: str
    in_period: bool             # False for the Q4 row


# ---------------------------------------------------------------------------
# Derived / reconciled shapes (SPEC §6).
# ---------------------------------------------------------------------------

@dataclass
class DerivedClaim:
    po_id: Optional[str]
    supplier_id: str
    supplier_name: str
    claim_type: str             # short_delivery | damage | price_gap | rebate | promo
    eur_amount: float
    line_math: str              # human-readable arithmetic a buyer can re-check
    evidence: dict              # the source rows backing this claim
    uom_normalized: bool
    confidence: str             # high | medium | low
    period: str

    @property
    def idempotency_key(self) -> str:
        anchor = self.po_id or f"{self.supplier_id}:{self.period}"
        return f"{anchor}|{self.claim_type}"


@dataclass
class ReconciledClaim:
    claim: DerivedClaim
    bucket: str                 # missed | logged-correct | over-claimed | not-claimable
    tracker_claim_id: Optional[str]
    tracker_status: Optional[str]
    delta_vs_tracker_eur: float
    duplicate_of: Optional[str]
    claimable: bool
    not_claimable_reason: Optional[str]


@dataclass
class ClaimPack:
    idempotency_key: str
    supplier_name: str
    po_id: Optional[str]
    claim_type: str
    eur_amount: float
    line_math: str
    evidence_rows: list
    confidence: str
    bucket: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


def to_jsonable(obj):
    """Recursively convert dataclasses/containers to JSON-serializable values."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj
