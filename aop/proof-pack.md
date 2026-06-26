# Proof Pack — Supplier-Claims Reconciliation, Q1 2026

> Deterministic ground-truth oracle for the Duvo reconciliation agent. Every
> number below is computed directly from the read-only CSVs in `data/` by
> [`validate_expected.py`](../) (session scratchpad) and is reproducible:
> same input -> same euro every run. Run it to regenerate; exit code `0` means
> all five acceptance cases pass and the roll-up is self-consistent.
>
> **Scope:** Q1 2026 only. The single Q4 row (**CLM-007 / INV-2099**, Riverside
> "Damaged goods" €600, already Paid 18/12) is **excluded** from all Q1 totals.

---

## Headline (Mark's question, answered)

> *"How much are we recovering vs. how much is owed?"* — now has a denominator.

| Metric | Value |
|---|--:|
| **€ owed (total genuine, evidence-backed claims)** | **€6,203.00** |
| &nbsp;&nbsp;— missed (derived, never logged) | €4,628.00 |
| &nbsp;&nbsp;— logged-correct (already in the tracker) | €1,575.00 |
| **€ recovered to date** (status = Paid, in Q1 scope) | **€0.00** |
| **Recovery rate** (recovered / owed) | **0.0%** |
| Over-claimed (duplicate) flagged for removal | €450.00 |
| **Annualized run-rate** (Q1 × 4) | **€24,812.00** |

**Caveat on run-rate:** the ×4 annualization is naive — it assumes Q1 is
representative. Grocery procurement is seasonal (produce volumes, promo calendars,
rebate thresholds crystallize quarterly), so treat €24,812 as an order-of-magnitude
ceiling, not a forecast. The honest read: ~€6.2k of recoverable money sits in a
single quarter, of which **74% (€4,628) was never on anyone's radar**, and **€0
has actually been collected** within the quarter.

---

## The missed money (what the manual process never logged)

These are derived from PO ↔ GRN ↔ Invoice + contracts, and have **no matching
tracker row**. This is the long tail Jenny predicted.

| Finding | Basis (line math) | € |
|---|---|--:|
| **Riverside — 120 damaged cases** | GRN-3005 condition=Damaged, "120 cases bottles leaking/crushed"; 120 × €9.00/case | **€1,080.00** |
| **Northgate — volume rebate earned** | Q1 net spend €51,600 ≥ €50,000 threshold; 3% × €51,600 | **€1,548.00** |
| **Sunrise — promo co-funding owed** | Contract: €2,000/qtr promo co-funding, Q1 not yet claimed | **€2,000.00** |
| | **Total missed** | **€4,628.00** |

Rebate threshold check (all four rebate suppliers, for transparency):

| Supplier | Q1 net spend | Threshold | Verdict |
|---|--:|--:|---|
| Northgate (SUP-001) | €51,600 | €50,000 | **MET → €1,548 @ 3%** |
| Meadowvale (SUP-003) | €31,200 | €80,000 | below by €48,800 — no rebate |
| Riverside (SUP-005) | €47,400 | €50,000 | below by €2,600 — no rebate |
| EcoPack (SUP-008) | €35,700 | €60,000 | below by €24,300 — no rebate |

---

## Corrections to the existing tracker

The agent doesn't just add money — it cleans the human's ground truth.

| Tracker row | Issue | Correction |
|---|---|---|
| **CLM-006** | Duplicate of CLM-004 — same €450 Prime Cuts chicken overcharge (INV-2006), logged twice by a different owner (M. Shaw) under an inconsistent supplier spelling ("Prime Cuts butchers"). | **Over-claimed.** Remove double-count; do not chase a second €450. |
| **CLM-003** | Meadowvale "price discrepancy" — raw unit price looks like a €99,000 gap (6,000 units @ €1.50 vs 500 cases @ €18.00). Contract note *"Prices quoted per case (12 units/case)"* reconciles both totals to €9,000. | **False positive.** No claim. Close the row. This is the line Jenny "couldn't get to line up" — there was nothing there. |
| **CLM-005** | Sweet Treats "short delivery?" — **no GRN-3007 exists.** No receipt evidence. | **Not-claimable / unprovable.** Do not fabricate a claim; route to a human Question gate. |

The genuine logged claims that **reconcile correctly** (kept):

| Tracker row | Claim | € | Status |
|---|---|--:|---|
| CLM-001 | Greenfield short delivery, 150 kg (GRN-3002) | €375.00 | Open |
| CLM-002 | Sunrise rolls overcharge, €0.95 vs €0.80 × 5,000 | €750.00 | in progress |
| CLM-004 | Prime Cuts chicken overcharge, €0.30/kg × 1,500 | €450.00 | Open |
| | **Total logged-correct** | **€1,575.00** | |

---

## Acceptance cases (SPEC §8) — all PASS

| # | Case | Expected verdict | Result |
|---|---|---|:--:|
| A | **Meadowvale UoM** (SUP-003) — per-case (12 u) normalization | NOT flagged as a discrepancy; negative control (unnormalized) shows the false €99,000 gap | **PASS** |
| B | **Greenfield short** (PO-1002) | short-delivery €375 (150 kg × €2.50), bucket **logged-correct**, matches **CLM-001** | **PASS** |
| C | **Sunrise price** (PO-1004) | price-gap **≈ €750** ((0.95−0.80) × 5,000), bucket **logged-correct**, matches **CLM-002** | **PASS** |
| D | **Prime Cuts duplicate** | **over-claimed**; CLM-006 = duplicate of CLM-004; no second claim raised | **PASS** |
| E | **Sweet Treats no-evidence** | **not-claimable** (no GRN); CLM-005 flagged; **zero** claims derived for SUP-007 | **PASS** |

Negative control for Case A is explicit in the oracle: without UoM normalization
the Meadowvale line shows a spurious **€99,000** gap; with normalization (12
units/case) the price gap is **none** and PO total = invoice total = €9,000.

---

## Data-quality issues found

These are real defects in the source data the agent must absorb without breaking:

- **Inconsistent `status` values** in `supplier_claims_tracker.csv`: `Open`,
  `in progress`, `WIP`, `Pending`, `open`, `Paid` — mixed casing and wording for
  the same underlying states. Normalized to `open / paid / disputed` before any
  grouping.
- **Mixed date formats**: tracker uses both `2026-01-15` (ISO) and `25/01/2026`
  (DD/MM/YYYY, CLM-003). PO/GRN/Invoice files are uniformly ISO `YYYY-MM-DD`.
- **Supplier name variants** for the same `supplier_id`: "Prime Cuts Butchers"
  vs "Prime Cuts butchers" (SUP-006), "Meadowvale Dairy Ltd" vs "Meadowvale
  Dairy" (SUP-003) — match on `supplier_id`, never on display name.
- **Blank `claim_amount_eur`** on unquantified rows (CLM-003, CLM-005, CLM-008) —
  must be treated as null, not €0, so they don't silently dilute totals.
- **Missing GRN** for PO-1007 (Sweet Treats, no GRN-3007) — the evidence gap that
  makes CLM-005 unprovable. The chain has a hole; do not fabricate.
- **UoM mismatch between PO and invoice** on Meadowvale dairy (PO in `case`,
  invoice in `unit`) — the trap that drove the false €99k discrepancy. Compare on
  line totals after normalization, never on raw unit price.

---

*Generated by `validate_expected.py`. To reproduce: run the script against `data/`
(read-only); it prints the three-way match, entitlements, reconciliation buckets,
the five PASS/FAIL cases, and this roll-up, then exits 0 on full pass.*
