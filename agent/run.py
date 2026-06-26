"""Autonomous runner — the agent's end-to-end task, runnable without Jenny.

  python -m agent.run                 # full reconciliation report (read-only)
  python -m agent.run --json          # machine-readable roll-up + claims
  python -m agent.run --approve KEY --approver "Paula Hart"   # gate a write
  python -m agent.run --submit        # submit only already-approved claims

The run derives claims from source, reconciles vs the tracker, prints the answer
to Mark's question, and leaves a trace + audit record joinable by run_id. The one
write (submit_claim) never fires without a persisted human approval.
"""
from __future__ import annotations

import argparse
import sys

from . import config
from .claimpack import build_claim_pack, period_rollup
from .entitlements import compute_entitlements
from .loader import load_period_data
from .matcher import three_way_match
from .models import to_jsonable
from .observability import make_run_id, write_records
from .reconcile import orphan_tracker_rows, reconcile_against_tracker
from . import submit as submit_mod

BUCKET_ORDER = ["missed", "logged-correct", "over-claimed", "do-not-pay", "not-claimable"]


def analyze(period: str = config.PERIOD_LABEL):
    data = load_period_data(period)
    run_id = make_run_id(data)
    derived = three_way_match(data) + compute_entitlements(data)
    reconciled = reconcile_against_tracker(derived, data)
    orphans = orphan_tracker_rows(derived, data)
    rollup = period_rollup(reconciled, data)
    return data, run_id, reconciled, orphans, rollup


def _print_report(data, run_id, reconciled, orphans, rollup):
    e = config.eur
    print(f"\n{'='*72}\n SUPPLIER-CLAIMS RECONCILIATION — {rollup['period']}   run_id={run_id}\n{'='*72}")

    print("\n>> MARK'S QUESTION: how much are we recovering vs. how much is owed?\n")
    print(f"   € owed (Q1, justified, de-duplicated) : {e(rollup['eur_owed_total'])}")
    print(f"   € recovered to date                   : {e(rollup['eur_recovered_to_date'])}")
    print(f"   RECOVERY RATE                         : {rollup['recovery_rate']*100:.0f}%")
    print(f"   ── missed (never logged)              : {e(rollup['missed_eur'])}  "
          f"({rollup['n_missed']} claims)")
    print(f"   ── logged-correct (already on it)     : {e(rollup['logged_correct_eur'])}")
    print(f"   ── over-claimed (real, but logged 2x) : {e(rollup['over_claimed_eur'])}")
    print(f"   over-claim RISK (would double-pay)    : {e(rollup['over_claim_risk_eur'])}")
    print(f"   annualized run-rate (×4, seasonality) : {e(rollup['annualized_run_rate_eur'])}")
    print(f"\n   PREVENT-LOSS (separate from recovery):")
    print(f"   ── duplicate billing BLOCKED (do-not-pay): {e(rollup['duplicate_billing_blocked_eur'])}  "
          f"({rollup['n_duplicate_invoices']} duplicate invoices)")

    for bucket in BUCKET_ORDER:
        rows = [r for r in reconciled if r.bucket == bucket]
        if not rows:
            continue
        print(f"\n{'-'*72}\n {bucket.upper()}  ({len(rows)})\n{'-'*72}")
        for r in rows:
            c = r.claim
            tag = f" [tracker {r.tracker_claim_id}/{r.tracker_status}]" if r.tracker_claim_id else ""
            dup = f" DUPLICATE_OF={r.duplicate_of}" if r.duplicate_of else ""
            head = f" • {c.supplier_name} — {c.claim_type} — {e(c.eur_amount)}{tag}{dup}"
            print(head)
            print(f"     {c.line_math}")
            if r.not_claimable_reason:
                print(f"     reason: {r.not_claimable_reason}")

    if orphans:
        print(f"\n{'-'*72}\n TRACKER ROWS TO CLEAN UP ({len(orphans)})\n{'-'*72}")
        for t, reason in orphans:
            print(f" • {t.claim_id} ({t.supplier}, status '{t.status_raw}'): {reason}")

    if data.excluded_tracker:
        print(f"\n PERIOD DISCIPLINE — excluded {len(data.excluded_tracker)} out-of-period row(s): "
              + ", ".join(t.claim_id for t in data.excluded_tracker))
    print()


def _build_records(run_id, reconciled, orphans, rollup, data):
    packs = [build_claim_pack(r) for r in reconciled if r.claimable]
    trace = {
        "run_id": run_id, "period": data.period,
        "counts": {"pos": len(data.purchase_orders), "grns": len(data.goods_receipts),
                   "invoices": len(data.invoices), "tracker_rows": len(data.tracker),
                   "excluded_rows": len(data.excluded_tracker)},
        "reconciled": reconciled,
        "orphan_tracker_rows": [{"claim_id": t.claim_id, "reason": reason} for t, reason in orphans],
    }
    audit = {
        "run_id": run_id, "period": data.period, "rollup": rollup,
        "claim_packs": packs,
    }
    return trace, audit


def main(argv=None):
    p = argparse.ArgumentParser(description="Daily Basket supplier-claims agent")
    p.add_argument("--period", default=config.PERIOD_LABEL)
    p.add_argument("--json", action="store_true", help="emit machine-readable roll-up + claims")
    p.add_argument("--approve", metavar="KEY", help="record human approval for one idempotency key")
    p.add_argument("--approver", default="Paula Hart", help="approver name for --approve")
    p.add_argument("--approved-at", default="2026-04-08", help="approval date (YYYY-MM-DD)")
    p.add_argument("--submit", action="store_true", help="submit all approved claims (the only write)")
    args = p.parse_args(argv)

    data, run_id, reconciled, orphans, rollup = analyze(args.period)

    # --- The human-approval gate (records a decision; no write yet). ---
    if args.approve:
        submit_mod.record_approval(args.approve, args.approver, args.approved_at)
        print(f"APPROVED {args.approve} by {args.approver} @ {args.approved_at}")
        return 0

    # --- The only write: submit claims that already carry a human approval. ---
    if args.submit:
        packs = [build_claim_pack(r) for r in reconciled if r.claimable]
        any_submitted = False
        for pack in packs:
            if submit_mod.is_approved(pack.idempotency_key):
                result = submit_mod.submit_claim(pack, run_id)
                print(f"{result['status']:>22}  {pack.idempotency_key}  "
                      f"{config.eur(pack.eur_amount)}  -> {result.get('submission_id','')}")
                any_submitted = True
        if not any_submitted:
            print("No approved claims to submit. Approve first: "
                  "--approve '<po_id|claim_type>' --approver '<name>'")
        return 0

    trace, audit = _build_records(run_id, reconciled, orphans, rollup, data)
    out_dir = write_records(run_id, trace, audit)

    if args.json:
        import json
        print(json.dumps(to_jsonable(audit), indent=2, ensure_ascii=False))
    else:
        _print_report(data, run_id, reconciled, orphans, rollup)
        print(f" trace + audit written to {out_dir}/{run_id}.*.json\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
