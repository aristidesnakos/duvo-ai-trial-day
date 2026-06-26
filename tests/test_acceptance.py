"""Acceptance criteria from SPEC.md §8, runnable as tests.

Each test encodes one named case from the email thread / scope check. Run:
    python3 -m pytest tests/ -q        (if pytest installed)
    python3 tests/test_acceptance.py   (zero-dependency fallback runner)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.run import analyze
from agent import submit as submit_mod


def _setup():
    return analyze("Q1-2026")


def _by_supplier(reconciled, name, claim_type=None):
    out = [r for r in reconciled
           if name.lower() in r.claim.supplier_name.lower()
           and (claim_type is None or r.claim.claim_type == claim_type)]
    return out


def test_marks_question_rollup():
    """Run produces € owed, € recovered, recovery rate, buckets, run-rate."""
    _, _, _, _, rollup = _setup()
    assert rollup["eur_owed_total"] == 6203.00
    assert rollup["eur_recovered_to_date"] == 0.00
    assert rollup["recovery_rate"] == 0.0
    assert rollup["missed_eur"] == 4628.00
    assert rollup["logged_correct_eur"] == 1125.00
    assert rollup["over_claimed_eur"] == 450.00
    assert rollup["annualized_run_rate_eur"] == 24812.00


def test_meadowvale_uom_negative_control():
    """SUP-003 dairy reconciles to €0 once UoM normalized — NO claim raised."""
    _, _, reconciled, _, _ = _setup()
    # No price_gap or short claim should exist for Meadowvale.
    bad = [r for r in _by_supplier(reconciled, "Meadowvale")
           if r.claim.claim_type in ("price_gap", "short_delivery", "damage")]
    assert bad == [], "Dairy must not produce a fabricated claim"


def test_greenfield_short_logged_correct():
    """150 kg short → €375, reconciles to open tracker row CLM-001."""
    _, _, reconciled, _, _ = _setup()
    r = _by_supplier(reconciled, "Greenfield", "short_delivery")[0]
    assert r.claim.eur_amount == 375.00
    assert r.bucket == "logged-correct"
    assert r.tracker_claim_id == "CLM-001"


def test_sunrise_price_gap():
    """Rolls €0.95 vs €0.80 → €750 price gap, logged-correct (in progress)."""
    _, _, reconciled, _, _ = _setup()
    r = _by_supplier(reconciled, "Sunrise", "price_gap")[0]
    assert r.claim.eur_amount == 750.00
    assert r.bucket == "logged-correct"


def test_riverside_damage_missed():
    """120 damaged cases × €9 = €1,080 — not in tracker → MISSED."""
    _, _, reconciled, _, _ = _setup()
    r = _by_supplier(reconciled, "Riverside", "damage")[0]
    assert r.claim.eur_amount == 1080.00
    assert r.bucket == "missed"


def test_prime_cuts_duplicate_over_claimed():
    """€450 chicken overcharge logged twice → over-claimed, duplicate flagged."""
    _, _, reconciled, _, _ = _setup()
    r = _by_supplier(reconciled, "Prime Cuts", "price_gap")[0]
    assert r.claim.eur_amount == 450.00
    assert r.bucket == "over-claimed"
    assert r.duplicate_of and "CLM-006" in r.duplicate_of


def test_sweet_treats_not_claimable():
    """No GRN for PO-1007 → not-claimable, no fabrication."""
    _, _, reconciled, _, _ = _setup()
    r = _by_supplier(reconciled, "Sweet Treats", "no_evidence")[0]
    assert r.bucket == "not-claimable"
    assert not r.claimable


def test_northgate_rebate_only_one_crosses():
    """Only Northgate crosses a rebate threshold → €1,548 earned, MISSED."""
    _, _, reconciled, _, _ = _setup()
    rebates = [r for r in reconciled if r.claim.claim_type == "rebate"]
    assert len(rebates) == 1
    assert rebates[0].claim.supplier_name.startswith("Northgate")
    assert rebates[0].claim.eur_amount == 1548.00
    assert rebates[0].bucket == "missed"


def test_q4_row_excluded():
    """The Q4-2025 tracker row (CLM-007) is excluded from the Q1 period."""
    data, _, _, _, _ = _setup()
    assert any(t.claim_id == "CLM-007" for t in data.excluded_tracker)
    assert all(t.claim_id != "CLM-007" for t in data.tracker)


def test_determinism():
    """Same input → same run_id and same € every run."""
    _, run_id1, _, _, rollup1 = _setup()
    _, run_id2, _, _, rollup2 = _setup()
    assert run_id1 == run_id2
    assert rollup1 == rollup2


def test_submit_gated_without_approval(tmp_path=None):
    """submit_claim refuses to write without a persisted human approval."""
    _, run_id, reconciled, _, _ = _setup()
    from agent.claimpack import build_claim_pack
    pack = build_claim_pack([r for r in reconciled if r.claimable][0])
    # Use a key guaranteed not approved.
    pack.idempotency_key = "TEST|never-approved"
    result = submit_mod.submit_claim(pack, run_id)
    assert result["status"] == "BLOCKED_NEEDS_APPROVAL"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL  {fn.__name__}: {exc}")
        except Exception as exc:  # noqa
            print(f"ERROR {fn.__name__}: {exc}")
    print(f"\n{passed}/{len(fns)} acceptance criteria passed")
    sys.exit(0 if passed == len(fns) else 1)
