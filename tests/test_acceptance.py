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


def test_damage_extraction_is_anchored_not_first_int():
    """Damage qty must bind to the unit/keyword, not grab a stray year/number."""
    from agent.config import damage_qty_from_note
    assert damage_qty_from_note("120 cases bottles leaking/crushed", "case") == (120, "high")
    # The trap: a year appears before the real quantity — must NOT return 2026.
    qty, conf = damage_qty_from_note("delivered 2026, 120 cases damaged", "case")
    assert qty == 120, f"anchored parser grabbed {qty}, expected 120"
    # No quantity stated → no fabricated number.
    assert damage_qty_from_note("fully damaged, see photos", "case")[0] is None


def test_riverside_damage_high_confidence():
    """The €1,080 damage claim is high-confidence (qty anchored to '120 cases')."""
    _, _, reconciled, _, _ = _setup()
    r = _by_supplier(reconciled, "Riverside", "damage")[0]
    assert r.claim.confidence == "high"


def test_duplicate_invoices_flagged_do_not_pay():
    """The 3 duplicate invoices are flagged do-not-pay totaling €29,200."""
    _, _, reconciled, _, rollup = _setup()
    dupes = [r for r in reconciled if r.claim.claim_type == "duplicate_invoice"]
    assert len(dupes) == 3, f"expected 3 duplicates, got {len(dupes)}"
    assert all(r.bucket == "do-not-pay" for r in dupes)
    assert round(sum(r.claim.eur_amount for r in dupes), 2) == 29200.00
    assert rollup["duplicate_billing_blocked_eur"] == 29200.00
    assert rollup["n_duplicate_invoices"] == 3
    # Individual at-risk totals.
    by_amt = sorted(r.claim.eur_amount for r in dupes)
    assert by_amt == [3000.00, 10000.00, 16200.00]


def test_duplicate_invoices_not_claimable():
    """None of the duplicates appear as claimable/recoverable claims."""
    _, _, reconciled, _, rollup = _setup()
    dupes = [r for r in reconciled if r.claim.claim_type == "duplicate_invoice"]
    assert all(not r.claimable for r in dupes)
    # They must not leak into the owed/missed/recovery totals.
    assert rollup["eur_owed_total"] == 6203.00
    assert rollup["missed_eur"] == 4628.00
    assert rollup["over_claimed_eur"] == 450.00
    # No claimable claim should carry the duplicate type.
    claimable = [r for r in reconciled if r.claimable]
    assert all(r.claim.claim_type != "duplicate_invoice" for r in claimable)


def test_duplicate_does_not_inflate_three_way_match():
    """The 2nd invoice on PO-1019/PO-1017/PO-1022 must NOT create short/price gaps."""
    _, _, reconciled, _, _ = _setup()
    # Riverside PO-1019 and Greenfield PO-1017 had clean deliveries; the only
    # finding tied to those POs should be the duplicate, not a short/price gap.
    for po in ("PO-1019", "PO-1017"):
        polluting = [r for r in reconciled
                     if r.claim.po_id == po
                     and r.claim.claim_type in ("short_delivery", "price_gap")]
        assert polluting == [], f"{po} produced a spurious claim from the duplicate"


def test_inv2031_carries_overcharge_note():
    """INV-2031 duplicate names both the €10,000 do-not-pay and the €400 price delta."""
    _, _, reconciled, _, _ = _setup()
    nm = _by_supplier(reconciled, "Northgate", "duplicate_invoice")
    assert len(nm) == 1
    r = nm[0]
    assert r.claim.eur_amount == 10000.00
    assert "INV-2022" in r.claim.line_math      # names the original
    assert "€400.00" in r.claim.line_math       # the embedded overcharge
    assert "€12.50" in r.claim.line_math and "€12.00" in r.claim.line_math


def test_inv2099_dangling_reference_flagged():
    """CLM-007 cites INV-2099 (not in invoices.csv) → flagged 'reference not found'."""
    _, _, _, orphans, _ = _setup()
    hits = [(t, reason) for t, reason in orphans
            if t.claim_id == "CLM-007" and "reference not found" in reason]
    assert hits, "INV-2099 dangling reference was not flagged"
    assert "INV-2099" in hits[0][1]


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
