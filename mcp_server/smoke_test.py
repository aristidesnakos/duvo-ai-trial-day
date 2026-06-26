"""Network-free smoke test for the reconciliation MCP wrapper.

Validates the *engine-wrapper logic* that `reconcile_period` exposes, WITHOUT
importing the `mcp` package and WITHOUT any network. It imports the engine
directly and rebuilds the exact payload the MCP tool returns, then asserts the
headline numbers (Q1-2026 owed = €6,203, etc.) so we know the wrapper hands the
Duvo agent the right audited roll-up.

    python -m mcp_server.smoke_test
    # or:  python mcp_server/smoke_test.py
"""
from __future__ import annotations

import json
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from agent.run import analyze
from agent.claimpack import build_claim_pack
from agent.models import to_jsonable


def reconcile_period_payload(period: str = "Q1-2026") -> dict:
    """Identical payload-build to mcp_server.server.reconcile_period, minus the
    @mcp.tool() decorator — so this exercises the same engine wrapper logic
    without needing the `mcp` package installed."""
    data, run_id, reconciled, orphans, rollup = analyze(period)
    packs = [build_claim_pack(r) for r in reconciled if r.claimable]
    payload = {
        "run_id": run_id,
        "period": data.period,
        "rollup": rollup,
        "claim_packs": packs,
        "orphan_tracker_rows": [
            {"claim_id": t.claim_id, "supplier": t.supplier,
             "status": t.status_raw, "reason": reason}
            for t, reason in orphans
        ],
    }
    return to_jsonable(payload)


# Expected headline numbers for Q1-2026 (source: agent/README.md "live" table).
EXPECTED = {
    "eur_owed_total": 6203.0,
    "eur_recovered_to_date": 0.0,
    "recovery_rate": 0.0,
    "missed_eur": 4628.0,
    "over_claim_risk_eur": 450.0,
    "annualized_run_rate_eur": 24812.0,
}


def main() -> int:
    payload = reconcile_period_payload("Q1-2026")

    # 1) JSON-serializable (the tool returns JSON to the Duvo agent).
    out = json.dumps(payload, indent=2, ensure_ascii=False)
    print(out)

    rollup = payload["rollup"]
    print("\n" + "=" * 60)
    print("SMOKE-TEST ASSERTIONS (Q1-2026)")
    print("=" * 60)

    ok = True
    for key, want in EXPECTED.items():
        got = rollup.get(key)
        match = (got == want)
        ok = ok and match
        flag = "OK " if match else "XX "
        print(f"  [{flag}] {key}: got {got!r}, expected {want!r}")

    n_packs = len(payload["claim_packs"])
    print(f"  [   ] claim_packs returned: {n_packs}")
    print(f"  [   ] run_id (deterministic): {payload['run_id']}")
    print(f"  [   ] orphan_tracker_rows: {len(payload['orphan_tracker_rows'])}")

    if ok:
        print("\nPASS — wrapper returns the expected audited roll-up.")
        return 0
    print("\nFAIL — roll-up did not match expected headline numbers.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
