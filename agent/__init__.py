"""Daily Basket supplier-claims reconciliation agent.

Deterministic, dependency-free engine. The arithmetic is transparent (every € is
re-checkable line-math); the only side effect is the human-gated submit_claim.
"""
from .loader import load_period_data
from .matcher import three_way_match, normalize_uom
from .entitlements import compute_entitlements
from .reconcile import reconcile_against_tracker, orphan_tracker_rows
from .claimpack import build_claim_pack, period_rollup

__all__ = [
    "load_period_data", "three_way_match", "normalize_uom",
    "compute_entitlements", "reconcile_against_tracker", "orphan_tracker_rows",
    "build_claim_pack", "period_rollup",
]
