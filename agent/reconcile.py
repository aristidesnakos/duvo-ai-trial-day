"""reconcile_against_tracker — bucket each derived claim vs the existing sheet.

The tracker is the reconcile TARGET, not the source of truth. We map every
derived claim to a tracker row (by po/invoice ref) and assign a bucket:
  missed          — justified claim with no tracker row (recoverable upside)
  logged-correct  — justified claim already on the tracker, € agrees
  over-claimed    — tracker has a duplicate / amount the data doesn't support
  not-claimable   — no evidence (missing GRN, UoM reconciles to €0) -> never raised
We also scan the tracker for orphan rows the data does NOT substantiate.
"""
from __future__ import annotations

from typing import List

from .loader import PeriodData
from .models import DerivedClaim, ReconciledClaim


# Map a derived claim_type to the tracker's free-text claim_type vocabulary.
_TYPE_HINTS = {
    "short_delivery": ("short",),
    "damage": ("damag",),
    "price_gap": ("price", "overcharge"),
    "rebate": ("rebate", "volume"),
    "promo": ("promo",),
}


def _tracker_matches(claim: DerivedClaim, data: PeriodData):
    """Tracker rows that plausibly refer to the same underlying claim."""
    out = []
    po_id = claim.po_id
    inv_id = None
    if isinstance(claim.evidence, dict):
        inv = claim.evidence.get("invoice")
        if isinstance(inv, dict):
            inv_id = inv.get("invoice_id")
    hints = _TYPE_HINTS.get(claim.claim_type, ())
    for t in data.tracker:
        ref_match = (po_id and t.po_ref == po_id) or (inv_id and t.invoice_ref == inv_id)
        if not ref_match:
            continue
        type_match = (not hints) or any(h in t.claim_type.lower() for h in hints)
        if type_match:
            out.append(t)
    return out


def reconcile_against_tracker(derived: List[DerivedClaim],
                              data: PeriodData) -> List[ReconciledClaim]:
    reconciled: List[ReconciledClaim] = []

    for claim in derived:
        # Non-claims: missing evidence, UoM reconciles to zero, near-miss rebates.
        if claim.claim_type == "no_evidence":
            reconciled.append(ReconciledClaim(
                claim=claim, bucket="not-claimable", tracker_claim_id=None,
                tracker_status=None, delta_vs_tracker_eur=0.0, duplicate_of=None,
                claimable=False,
                not_claimable_reason="No goods-receipt evidence — cannot substantiate."))
            continue
        if claim.claim_type == "rebate_below_threshold":
            reconciled.append(ReconciledClaim(
                claim=claim, bucket="not-claimable", tracker_claim_id=None,
                tracker_status=None, delta_vs_tracker_eur=0.0, duplicate_of=None,
                claimable=False,
                not_claimable_reason="Q1 spend below rebate threshold — nothing earned."))
            continue
        if claim.eur_amount <= 0:
            reconciled.append(ReconciledClaim(
                claim=claim, bucket="not-claimable", tracker_claim_id=None,
                tracker_status=None, delta_vs_tracker_eur=0.0, duplicate_of=None,
                claimable=False,
                not_claimable_reason="Reconciles to €0 once normalized — no discrepancy."))
            continue

        matches = _tracker_matches(claim, data)
        if not matches:
            reconciled.append(ReconciledClaim(
                claim=claim, bucket="missed", tracker_claim_id=None, tracker_status=None,
                delta_vs_tracker_eur=claim.eur_amount, duplicate_of=None,
                claimable=True, not_claimable_reason=None))
            continue

        primary = matches[0]
        logged_total = sum(m.claim_amount_eur or 0.0 for m in matches)
        delta = round(claim.eur_amount - logged_total, 2)
        # Multiple tracker rows for one derived claim => duplicate / over-claim.
        if len(matches) > 1:
            dupes = ", ".join(m.claim_id for m in matches[1:])
            reconciled.append(ReconciledClaim(
                claim=claim, bucket="over-claimed", tracker_claim_id=primary.claim_id,
                tracker_status=primary.status_norm,
                delta_vs_tracker_eur=delta, duplicate_of=dupes, claimable=True,
                not_claimable_reason=None))
        else:
            reconciled.append(ReconciledClaim(
                claim=claim, bucket="logged-correct", tracker_claim_id=primary.claim_id,
                tracker_status=primary.status_norm,
                delta_vs_tracker_eur=delta, duplicate_of=None, claimable=True,
                not_claimable_reason=None))

    return reconciled


def orphan_tracker_rows(derived: List[DerivedClaim], data: PeriodData):
    """Tracker rows the derived analysis does NOT support (noise / to investigate).

    Returns (row, reason) pairs. A row is an orphan if no in-period derived claim
    referenced it. Blank-amount rows are flagged as placeholders/non-claims.
    """
    referenced = set()
    for c in derived:
        if c.po_id:
            referenced.add(("po", c.po_id))
        inv = c.evidence.get("invoice") if isinstance(c.evidence, dict) else None
        if isinstance(inv, dict) and inv.get("invoice_id"):
            referenced.add(("inv", inv["invoice_id"]))

    orphans = []
    for t in data.tracker:
        hit = ("po", t.po_ref) in referenced or ("inv", t.invoice_ref) in referenced
        if t.claim_amount_eur is None:
            orphans.append((t, "blank amount — placeholder / not a substantiated claim"))
        elif not hit:
            orphans.append((t, "no matching derived claim — investigate or close"))
    return orphans
