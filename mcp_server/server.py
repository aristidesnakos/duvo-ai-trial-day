"""MCP server exposing the deterministic reconciliation engine as callable tools.

The engine (`agent/`) does GUARANTEED arithmetic: it derives every supplier
claim from the ERP exports + contracts, reconciles them against the existing
tracker, and produces an audited roll-up where every euro is re-checkable
line-math. This server is a *thin, read-only wrapper* over that engine so a Duvo
agent can CALL for the numbers instead of reasoning the euros itself.

Design rules (mirror the engine's constitution):
  - Read-only: we import and call the engine's pure analysis functions. We never
    touch `submit_claim` (the engine's one write) or anything under `out/`.
  - Deterministic: same inputs -> same `run_id`, same totals. No inference here.
  - JSON-safe: every payload goes through the engine's own `to_jsonable`.

Transport: Duvo requires MCP's *Streamable HTTP* transport over a public HTTPS
URL (stdio / HTTP+SSE are not accepted). FastMCP serves streamable-http; see
mcp_server/README.md for hosting + registration. For local development you can
also run plain stdio.

Run locally:
    pip install -r mcp_server/requirements.txt
    # stdio (for `mcp dev` / a local MCP client):
    python -m mcp_server.server
    # streamable-http (what Duvo needs, behind a public HTTPS URL):
    python -m mcp_server.server --http --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import argparse
import os
import sys

# --- Make the sibling `agent` package importable regardless of cwd. ----------
# This file lives at <repo>/mcp_server/server.py; the engine is at <repo>/agent.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from mcp.server.fastmcp import FastMCP  # noqa: E402

# Import the engine's public surface (read-only analysis only — NOT submit). ---
from agent import config  # noqa: E402
from agent.run import analyze  # noqa: E402
from agent.claimpack import build_claim_pack, period_rollup  # noqa: E402
from agent.entitlements import compute_entitlements as _compute_entitlements  # noqa: E402
from agent.loader import load_period_data  # noqa: E402
from agent.matcher import three_way_match as _three_way_match  # noqa: E402
from agent.reconcile import reconcile_against_tracker  # noqa: E402
from agent.models import to_jsonable  # noqa: E402


mcp = FastMCP("duvo-reconciliation")


# ---------------------------------------------------------------------------
# Headline tool: the full audited roll-up + claim packs.
# ---------------------------------------------------------------------------
@mcp.tool()
def reconcile_period(period: str = config.PERIOD_LABEL) -> dict:
    """Run the deterministic three-way reconciliation for a period and return the
    full audited roll-up plus every claim pack.

    This is the headline tool: a Duvo agent calls it to get GUARANTEED euros
    (owed / recovered / recovery rate / by-bucket) with a re-checkable claim pack
    behind each one — instead of reasoning the arithmetic itself.

    Args:
        period: Period label, e.g. "Q1-2026" (the engine's default).

    Returns a JSON-safe dict:
        run_id            deterministic id for this run (joins trace+audit)
        period
        rollup            owed total, recovered, recovery_rate, by-bucket
                          (missed/logged-correct/over-claimed), over-claim risk,
                          duplicate-billing blocked, annualized run-rate, counts
        claim_packs       list of {idempotency_key, supplier_name, po_id,
                          claim_type, eur_amount, line_math, evidence_rows,
                          confidence, bucket} — only the claimable ones
        orphan_tracker_rows  tracker rows the data does NOT substantiate
                          (claim_id + reason), for cleanup
    """
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


# ---------------------------------------------------------------------------
# Finer-grained tools (same engine, narrower slice).
# ---------------------------------------------------------------------------
@mcp.tool()
def three_way_match(period: str = config.PERIOD_LABEL) -> dict:
    """Derive the PO -> GRN -> Invoice three-way-match claims for a period.

    Short-delivery, damage, price-gap and duplicate-invoice findings derived from
    the matched source rows, BEFORE reconciliation against the tracker. Use this
    when you want the raw discrepancies and their line-math, not the buckets.

    Returns: {period, n_claims, claims: [DerivedClaim ...]} (JSON-safe).
    """
    data = load_period_data(period)
    claims = _three_way_match(data)
    return to_jsonable({
        "period": data.period,
        "n_claims": len(claims),
        "claims": claims,
    })


@mcp.tool()
def compute_entitlements(period: str = config.PERIOD_LABEL) -> dict:
    """Compute per-supplier contract entitlements (volume rebate + promo funding).

    A rebate is only owed if cumulative period spend actually crosses the
    contract threshold; promo funding is owed when the contract states a
    per-quarter amount (confidence dropped + caveated if the contract does not
    cover the full period). Near-miss rebates are emitted at €0 for transparency.

    Returns: {period, n_claims, claims: [DerivedClaim ...]} (JSON-safe).
    """
    data = load_period_data(period)
    claims = _compute_entitlements(data)
    return to_jsonable({
        "period": data.period,
        "n_claims": len(claims),
        "claims": claims,
    })


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Duvo reconciliation MCP server")
    p.add_argument("--http", action="store_true",
                   help="serve over Streamable HTTP (what Duvo requires) "
                        "instead of stdio")
    p.add_argument("--host", default="127.0.0.1",
                   help="bind host for --http (use 0.0.0.0 behind a tunnel/host)")
    p.add_argument("--port", type=int, default=8000, help="bind port for --http")
    args = p.parse_args(argv)

    if args.http:
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
