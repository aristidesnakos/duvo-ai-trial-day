"""build_claim_pack + period_rollup.

A claim pack is the human-readable, auditable unit a buyer approves. The roll-up
is the answer to the Finance Director's question: € owed vs € recovered.
"""
from __future__ import annotations

from typing import List

from .models import ClaimPack, ReconciledClaim


def build_claim_pack(rc: ReconciledClaim) -> ClaimPack:
    c = rc.claim
    return ClaimPack(
        idempotency_key=c.idempotency_key,
        supplier_name=c.supplier_name,
        po_id=c.po_id,
        claim_type=c.claim_type,
        eur_amount=c.eur_amount,
        line_math=c.line_math,
        evidence_rows=[c.evidence],
        confidence=c.confidence,
        bucket=rc.bucket,
    )


def period_rollup(reconciled: List[ReconciledClaim], data) -> dict:
    """Answer Mark's question with transparent, de-duplicated totals."""
    claimable = [r for r in reconciled if r.claimable]

    owed = round(sum(r.claim.eur_amount for r in claimable), 2)

    by_bucket = {"missed": 0.0, "logged-correct": 0.0, "over-claimed": 0.0}
    for r in claimable:
        by_bucket[r.bucket] = round(by_bucket.get(r.bucket, 0.0) + r.claim.eur_amount, 2)

    # € already recovered = in-period tracker rows marked PAID.
    recovered = round(sum(t.claim_amount_eur or 0.0
                          for t in data.tracker if t.status_norm == "PAID"), 2)

    # Over-claim risk = duplicate tracker amounts that would be paid twice.
    over_claim_risk = round(sum(-r.delta_vs_tracker_eur for r in reconciled
                                if r.bucket == "over-claimed" and r.delta_vs_tracker_eur < 0), 2)

    # Prevent-loss: duplicate invoices blocked before payment. This is DISTINCT
    # from recovery — it is money kept in the bank, not clawed back. Kept as its
    # own line so owed/recovered/missed are never polluted by it.
    duplicate_blocked = [r for r in reconciled if r.bucket == "do-not-pay"]
    duplicate_billing_blocked = round(
        sum(r.claim.eur_amount for r in duplicate_blocked), 2)

    return {
        "period": data.period,
        "eur_owed_total": owed,
        "eur_recovered_to_date": recovered,
        "recovery_rate": round(recovered / owed, 4) if owed else 0.0,
        "missed_eur": by_bucket["missed"],
        "logged_correct_eur": by_bucket["logged-correct"],
        "over_claimed_eur": by_bucket["over-claimed"],
        "over_claim_risk_eur": over_claim_risk,
        "duplicate_billing_blocked_eur": duplicate_billing_blocked,
        "n_duplicate_invoices": len(duplicate_blocked),
        "annualized_run_rate_eur": round(owed * 4, 2),
        "n_claimable": len(claimable),
        "n_missed": sum(1 for r in claimable if r.bucket == "missed"),
    }
