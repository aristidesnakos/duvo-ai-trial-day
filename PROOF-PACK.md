# Proof Pack — Daily Basket Supplier Claims Agent

> Before/after, quantified in €. **Read the Summary; the Technical Addendum is there if you want to check the arithmetic.**
> Sponsor: Paula Hart (Finance Ops) · Operator: Jenny Walsh · Economic buyer: Mark Bryant (Finance Director) · Period: Q1 2026 (closed).
> Every figure is engine output (`python3 -m agent.run`, run `run-Q1-2026-70ce31ef`), re-checkable by hand from the source rows.

---

## Summary — for the Finance Director

### The situation (before)

- **No recovery-rate visibility.** Mark asked *"how much are we actually recovering vs. how much is owed to us?"* and Finance **had no answer** — the denominator (€ owed) was never computed.
- **Key-person risk.** The whole claims process lived in one spreadsheet. When Jenny was out sick in February, *"nobody touched this sheet for two weeks and a couple of credit windows nearly closed."*
- **Money never logged at all.** *"We don't track what we should have claimed, only what we happened to chase."* Claims were reactive, so the un-claimed tail was invisible.
- **Rebate entitlements never checked.** *"The suppliers with rebate deals — flour, drinks, packaging, dairy — I almost never check whether we've crossed the threshold."*

### What the agent changes (after)

- **Computes € owed from source.** Derives the claims that *should* exist from PO ↔ Goods Receipt ↔ Invoice + contracts — independent of the spreadsheet.
- **Answers the recovery-rate question.** € recovered ÷ € owed, split missed / logged-correct / over-claimed, each defensible by line-math.
- **Surfaces missed money and catches over-claims.** Finds what was never logged; flags a claim logged twice before it's double-chased.
- **Prevents loss in the other direction.** Flags duplicate supplier invoices **"DO NOT PAY"** before AP pays them.
- **Runs without Jenny.** End-to-end, deterministic, every run leaves an audit trail. Key-person risk removed.

### What it's worth

| Metric | Before | After |
|---|---|---|
| € owed (total justified Q1 claims) | Unknown — never computed | **€6,203** |
| Missed money (should-claim, never logged) | Invisible | **€4,628** (3 claims) |
| Over-claim / duplicate risk surfaced | None | **€450** (Prime Cuts logged twice) |
| Duplicate billing blocked (do-not-pay) | Paid blind | **€29,200** (3 invoices) |
| **Total money protected** | — | **€35,403** |
| € recovered to date (Q1) | Untracked | **€0** — claims *identified*, not yet collected |
| Recovery rate | Unanswerable | **0%** (the honest starting point) |
| Claims process runs without Jenny | No (2-week gap in Feb) | Yes — one autonomous run |

> **Headline:** the agent turns an unanswerable question into **€6,203 owed, €4,628 of it never logged, and €29,200 of double-billing blocked — €35,403 protected in one quarter** (annualized ≈ **€24,812/yr** recoverable, seasonality caveat). Recovery to date is **0%**: these claims are now *identified and packaged*, not yet *collected*. The end-to-end recovery loop has been **demonstrated live on Duvo** (see addendum) — the next step is running it against real suppliers.

---

## Technical Addendum — check the arithmetic

### How every € is defensible

Each claim carries supplier, PO id, basis, € amount, the source rows as evidence, explicit UoM normalization where applied, and a confidence flag. Six claim packs, €6,203 total:

| Claim | Supplier | Basis | € | Bucket | Line-math |
|---|---|--:|---|---|
| PO-1002 | Greenfield Farm | short delivery | 375 | logged-correct | 150 kg invoiced-not-received × €2.50 |
| PO-1004 | Sunrise Bakery | price gap | 750 | logged-correct | (€0.95 − €0.80) × 5,000 units |
| PO-1005 | Riverside Beverages | damage | 1,080 | **missed** | 120 damaged cases × €9.00 (GRN-3005, photos) |
| PO-1006 | Prime Cuts Butchers | price gap | 450 | **over-claimed** | (€6.80 − €6.50) × 1,500 kg — logged twice |
| SUP-001 | Northgate Mills | rebate | 1,548 | **missed** | Q1 spend €51,600 ≥ €50k → 3% |
| SUP-004 | Sunrise Bakery | promo | 2,000 | **missed** (med) | €2,000/qtr promo — contract lapses 2026-02-28 |

Missed = 1,080 + 1,548 + 2,000 = **€4,628**; logged-correct = **€1,125**; over-claimed = **€450**. High-confidence missed money is **€2,628** (Riverside + Northgate); the **€2,000 Sunrise promo carries a caveat** — its contract runs 2025-03-01 → 2026-02-28, lapsing two-thirds into Q1, so the agent flags *pro-rate or confirm before quoting to a supplier*.

### The three traps the engine gets right

1. **UoM normalization (a false positive closed).** Meadowvale Dairy quotes per case (12 units). A naive unit-price compare flags a phantom ~€99k gap; normalized, INV-2003 (6,000 units @ €1.50) reconciles **exactly** to PO-1003 (500 cases @ €18.00) = €9,000 → **no claim**. This is why Jenny *"couldn't get the numbers to line up."* The honest answer is €0 — so they stop chasing it.
2. **No evidence, no claim.** Sweet Treats (PO-1007) has no goods-receipt row → the shortage is unprovable → routed to a human, **not invented**.
3. **Duplicate detection.** Prime Cuts' real €450 overcharge was logged twice (CLM-004 + CLM-006, different owners/spelling) → flagged so Daily Basket doesn't double-chase or double-pay.

### Prevent loss — €29,200 duplicate billing blocked (do-not-pay)

Three new supplier invoices re-bill POs already received once (one GRN) and invoiced once — double-billing. The agent flags each **"DO NOT PAY"** to AP, does **not** raise them as recovery claims (wrong direction), and does **not** let them pollute the recovery numbers.

| New invoice | PO | Already invoiced | Duplicate says | Exposure |
|---|---|---|---|--:|
| INV-2032 Riverside | PO-1019 | INV-2019 1,800 @ €9.00 = €16,200 | identical | 16,200 |
| INV-2033 Greenfield | PO-1017 | INV-2017 1,200 @ €2.50 = €3,000 | identical | 3,000 |
| INV-2031 Northgate | PO-1022 | INV-2022 800 @ €12.00 = €9,600 | 800 @ €12.50 = €10,000 | 10,000 |

> Total blocked = **€29,200**. The discriminator vs. a legitimate second shipment: **count the GRNs** — a 2nd invoice on a PO with only one goods receipt is a double-bill. **Dangling-reference guard:** tracker row CLM-007 cites invoice INV-2099, which exists nowhere in the data → flagged **"reference not found"** rather than acted on.

### The live Duvo closed-loop demonstration (recovery path)

To prove the recovery path end-to-end, the agent ran a **two-agent closed loop on Duvo** over a Google Sheets surrogate ERP: the reconciliation agent raises and chases claims; a **Supplier Simulator** role-plays the 8 suppliers from their own private ledger (so credits and disputes are data-driven, not scripted). In that demonstration, recovery went **0% → 89.2%** (€5,536 of €6,203) with one human approval.

> **This is a demonstration, not realized customer cash.** The supplier responses are simulated and the ERP is a surrogate Sheet (no real suppliers, no email). It proves the loop *works* end-to-end; the €5,536 is not money in Daily Basket's bank. Setup + IDs: [`aop/DEPLOYMENT.md`](aop/DEPLOYMENT.md); design + honest gaps: [`aop/SIMULATION-DESIGN.md`](aop/SIMULATION-DESIGN.md).

### Provenance & trust

Deterministic (same inputs → same output), stdlib-only, read-only on ERP/contracts/tracker. The only write — `submit_claim` — is human-gated, idempotent (`po_id|claim_type`), and capped to the derived € amount. Every run leaves a `run_id`-joinable trace + audit record (`out/run-Q1-2026-70ce31ef.{trace,audit}.json`). 18/18 acceptance criteria pass. Transparent arithmetic a buyer can hold up in front of a supplier — not opaque inference.
