# Proof Pack — Daily Basket Supplier Claims Agent

> Before/after, quantified in €. Fill `[€X]`-style placeholders once the CSVs are analyzed and the € numbers are agreed on the day.
> Sponsor: Paula Hart (Finance Ops) · Operator: Jenny Walsh · Economic buyer: Mark Bryant (Finance Director).

## Headline

**Daily Basket could not answer Mark's question — "how much are we recovering vs. how much is owed?" Now it can: €[X] owed, €[Y] already recovered, a [Z]% recovery rate, and €[A] in missed money the old process never caught.**

---

## BEFORE — the state we found

- **No recovery-rate visibility.** Mark asked *"how much are we actually recovering vs. how much is owed to us?"* and Finance Ops **had no answer** (email thread, 31 Mar 2026). The denominator — € owed — was never computed.
- **Key-person risk.** The entire claims process lived in one person's spreadsheet. When Jenny was out sick in Feb, *"nobody touched this sheet for two weeks and a couple of credit windows nearly closed on us"* (email thread). Resilience has hard € consequences.
- **Money never logged at all.** *"We don't track what we should have claimed, only what we happened to chase"* and *"I catch what I catch"* (Jenny, email thread). Claims were reactive — triggered only when a supplier emailed or something looked obviously wrong — so the un-claimed long tail was invisible.
- **Rebate entitlements never checked.** *"The suppliers with rebate deals — flour, the drinks one, packaging, dairy — I almost never check whether we've crossed the threshold. That's where I'd bet the real money is, and it's exactly the part I never get to"* (Jenny, email thread).

## AFTER — what the agent delivers

- **€ owed is computed.** The agent derives the claims that *should* exist from ERP exports (PO ↔ Goods Receipt ↔ Invoice) + contracts, independent of the spreadsheet: total justified Q1 claims = **€[X]**.
- **Recovery rate, finally answerable.** € already recovered (from the tracker) ÷ € owed = **[Z]%**, split into **missed / logged-correct / over-claimed**, each defensible by transparent line-math.
- **Missed money recovered.** **€[A]** the old process never caught — concentrated in rebate entitlements and the dairy UoM claim Jenny abandoned.
- **Runs without Jenny.** The end-to-end derivation + reconciliation + claim-pack runs whether or not she is in. Key-person risk eliminated; no more near-missed credit windows.

---

## Before / After — quantified

| Metric | Before | After |
|---|---|---|
| € owed (total justified Q1 claims) | Unknown — never computed | **€[X]** |
| € already recovered | Untracked / partial | **€[B]** |
| Recovery rate (recovered ÷ owed) | Unanswerable | **[Z]%** |
| Missed money (should-claim, never logged) | Invisible | **€[A]** |
| Over-claim / duplicate risk surfaced | None | **€[C]** flagged |
| Rebate entitlements checked | ~Never | **[N] suppliers, €[D]** |
| Claims process runs without Jenny | No (2-week gap in Feb) | Yes |
| Cycle time per claim (derive → claim pack) | [old: hours/days, ad hoc] | [new: minutes, on demand] |

> **Annualized run-rate:** Q1 recoverable €[X] × 4 ≈ **€[E]/yr** (seasonality caveat — Q1 only, confirm with Finance before quoting externally).

---

## Specific wins to feature

1. **Meadowvale Dairy (SUP-003) — the claim Jenny abandoned.** She *"couldn't get the numbers to line up, ran out of time."* The contract quotes **per case = 12 units**; the agent normalizes UoM before the price/qty comparison and surfaces a justified claim of **€[F]** that a human gave up on. Cleanest illustration of "money never logged at all." **Lead the demo here.**
2. **Prime Cuts Butchers — duplicate caught.** The meat claim Jenny *"logged in a rush, feeling it's in there twice."* Reconciliation flags the **duplicate tracker row** → over-claim risk of **€[G]** removed before it goes to the supplier.
3. **Rebate entitlements never checked.** Q1 volumes vs contract thresholds for **flour / drinks / packaging / dairy** → **€[D]** in earned-but-unclaimed rebate + promo funding. Where Jenny bet the real money was, and never got to.

> Supporting cases (reconciliation buckets, for the walkthrough): Greenfield Farm short delivery (logged-correct, open), Sunrise Bakery ~€750 overcharge (logged-correct, disputed), Sweet Treats (not claimable — no GR evidence; the agent does *not* fabricate a claim the data can't defend).

---

## How every € is defensible

Each claim in the pack carries: supplier, PO id, claim basis (short / damage / price-gap / rebate / promo), **€ amount**, the three source rows as evidence, explicit UoM normalization where applied, and a confidence flag. Transparent arithmetic a buyer can hold up in front of the supplier — not opaque inference. Human approves before any submission.
