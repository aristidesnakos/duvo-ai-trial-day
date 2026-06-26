# Proof Pack — Daily Basket Supplier Claims Agent

> Before/after, quantified in €. Numbers are live engine output (`python3 -m agent.run`), cross-verified by 4 independent analysis passes and re-checkable by hand.
> Sponsor: Paula Hart (Finance Ops) · Operator: Jenny Walsh · Economic buyer: Mark Bryant (Finance Director) · Period: Q1 2026 (closed).

## Headline

**Daily Basket could not answer Mark's question — "how much are we recovering vs. how much is owed?" Now it can: €6,203 owed, €0 recovered, a 0% recovery rate, and €4,628 in missed money the old process never logged — plus a €450 double-count caught before it reached a supplier.**

---

## BEFORE — the state we found

- **No recovery-rate visibility.** Mark asked *"how much are we actually recovering vs. how much is owed to us?"* and Finance Ops **had no answer** (email thread, 31 Mar 2026). The denominator — € owed — was never computed.
- **Key-person risk.** The whole process lived in one spreadsheet. When Jenny was out sick in Feb, *"nobody touched this sheet for two weeks and a couple of credit windows nearly closed on us."*
- **Money never logged at all.** *"We don't track what we should have claimed, only what we happened to chase… I catch what I catch."* Claims were reactive, so the un-claimed tail was invisible.
- **Rebate entitlements never checked.** *"The suppliers with rebate deals — flour, the drinks one, packaging, dairy — I almost never check whether we've crossed the threshold. That's where I'd bet the real money is."*

## AFTER — what the agent delivers

- **€ owed is computed from source.** Derives the claims that *should* exist from PO ↔ Goods Receipt ↔ Invoice + contracts, independent of the spreadsheet: **€6,203** of justified Q1 claims.
- **Recovery rate, finally answerable.** € recovered ÷ € owed = **0%** (nothing logged in Q1 has been recovered yet), split **missed / logged-correct / over-claimed**, each defensible by transparent line-math.
- **Missed money surfaced.** **€4,628** the old process never logged — Riverside damaged goods, the Northgate rebate, and Sunrise promo funding.
- **Runs without Jenny.** End-to-end derivation + reconciliation + claim-pack runs whether or not she is in. Key-person risk eliminated.

---

## Before / After — quantified

| Metric | Before | After |
|---|---|---|
| € owed (total justified Q1 claims) | Unknown — never computed | **€6,203** |
| € already recovered (Q1) | Untracked | **€0** |
| Recovery rate (recovered ÷ owed) | Unanswerable | **0%** |
| Missed money (should-claim, never logged) | Invisible | **€4,628** (3 claims) |
| Over-claim / duplicate risk surfaced | None | **€450** (Prime Cuts logged twice) |
| Rebate entitlements checked | ~Never | **4 suppliers tested → €1,548 earned** (+ €2,000 promo) |
| Claims process runs without Jenny | No (2-week gap in Feb) | Yes — one autonomous run |
| Tracker hygiene | 8 rows, 3 real | 3 placeholder rows + 1 Q4 row + 1 duplicate flagged |

> **Annualized run-rate:** Q1 €6,203 × 4 ≈ **€24,812/yr** (seasonality caveat — Q1 only; rebate/promo recur quarterly, discrepancies vary. Confirm with Finance before quoting externally.)

---

## Specific wins to feature

1. **Meadowvale Dairy (SUP-003) — the claim Jenny abandoned, resolved honestly.** She *"couldn't get the numbers to line up."* The contract quotes **per case = 12 units**; the agent normalizes UoM and proves INV-2003 (6,000 units @ €1.50) reconciles **exactly** to PO-1003 (500 cases @ €18.00) = €9,000 → **no claim exists**. The hero isn't fabricated money — it's *closing a question that ate her time*, with the per-case math shown. **Lead the demo here:** "the agent does the unit conversion that defeated a human, and the honest answer is €0 — so you stop chasing it."
2. **Riverside Beverages — €1,080 missed.** GRN-3005 logged **120 damaged cases**, but the full 2,000 were invoiced and **nothing was claimed**. Largest single missed item; pure recoverable upside.
3. **Northgate Mills — €1,548 rebate, missed.** Q1 spend €51,600 crossed the €50,000 threshold at 3%. **Only 1 of 4 rebate suppliers actually qualifies** — Jenny's instinct that "rebates are where the money is" was *directionally* right but the agent shows exactly *which* supplier, so effort goes where it pays.
4. **Prime Cuts Butchers — €450 double-count caught.** A real €450 chicken overcharge logged **twice** (CLM-004 + CLM-006, different owners/spelling). The agent flags the duplicate so Daily Basket doesn't chase — or get paid — twice and damage the supplier relationship.

> Supporting cases: Greenfield short delivery €375 (logged-correct, open), Sunrise €750 overcharge (logged-correct, in progress), Sweet Treats (not claimable — **no goods receipt**, the agent refuses to fabricate a claim).

---

## How every € is defensible

Each claim carries: supplier, PO id, basis (short / damage / price-gap / rebate / promo), **€ amount**, the source rows as evidence, explicit UoM normalization where applied, and a confidence flag. The only write — `submit_claim` — is **human-gated, idempotent, and capped to the derived € amount**; nothing is submitted without a recorded approval. Every run leaves a `run_id`-joinable trace + audit record. Transparent arithmetic a buyer can hold up in front of a supplier — not opaque inference.
