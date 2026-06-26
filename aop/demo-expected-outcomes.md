# Demo Expected Outcomes — Closed-Loop Oracle

> The **oracle** for the closed-loop demo: a reconciliation Duvo agent (role-playing **Jenny Walsh**, AP) emails a
> supplier-simulator Duvo agent (role-playing all 8 suppliers) over Gmail, reconciling **Q1 2026** supplier claims and
> driving each discrepancy to a defined final state.
>
> This file is the expected-outcomes contract. Every number is fixed from the validated Q1 analysis
> (`aop/README.md`, `PROOF-PACK.md`, `SPEC.md §8`). **Do not recompute or round** — match exactly.
>
> **Ground-truth Q1 roll-up:** €6,203 owed · €0 recovered initially · €4,628 missed · €450 over-claim risk.
> - Missed: Riverside damaged €1,080 + Northgate rebate €1,548 + Sunrise promo €2,000 *(medium confidence — contract lapsed)*.
> - Over-claim: Prime Cuts CLM-006 is a duplicate of CLM-004 (€450 logged twice).
> - False / close: CLM-003 Meadowvale (unit/case trap), CLM-005 Sweet Treats (no GRN-3007).
> - Logged-correct: Greenfield €375, Sunrise overcharge €750, Prime Cuts €450.

---

## Per-supplier expected outcomes (all 8)

| # | Supplier (id) | Claim(s) the agent should raise | Email the agent should send | Simulator's expected reply | Correct final tracker state |
|---|---|---|---|---|---|
| 1 | **Greenfield Farm** (SUP-002) | **CLM-001 — short delivery €375** (150 kg short, GRN-3002, billed undelivered × €2.50). *Logged-correct, already open.* | Chase the open CLM-001: "150 kg short on PO-1002 / GRN-3002, billed in full on INV-2002 — please issue a €375 credit note." | Acknowledges short delivery against GRN evidence; **issues €375 credit note** (contract: "short or damaged deliveries credited against GRN evidence"). | **Credit-received €375** (Open → Credit-received) |
| 2 | **Sunrise Bakery** (SUP-004) | **(a) CLM-002 — price-gap €750** (rolls €0.95 vs €0.80 agreed × 5,000). *Logged-correct, in progress.* **(b) Promo co-funding €2,000/qtr — MISSED, medium confidence (see flag).** | (a) Chase CLM-002 overcharge: "INV-2004 billed €0.95 vs agreed €0.80 pricelist — €750 due." (b) **Separately** request the €2,000 Q1 promo co-funding **and ask the simulator to confirm the promo rule for Q1** given the contract end date. | (a) Concedes the pricelist overcharge; **issues €750 credit**. (b) **Disputes / qualifies the €2,000**: contract ran 2025-03-01 → **2026-02-28** (lapsed two-thirds into Q1) — supplier proposes pro-rated (~€1,333) or €0, or asks Finance to confirm the rule. | (a) **Credit-received €750** (in progress → Credit-received). (b) **Disputed / escalated** — promo `€2,000 [medium]`, route to human (Paula/Finance) to confirm pro-rate vs full vs €0. |
| 3 | **Prime Cuts Butchers** (SUP-006) | **CLM-004 — chicken overcharge €450** (€6.80 vs €6.50 pricelist × 1,500 kg). Real **once**. The agent must **flag CLM-006 as a duplicate of CLM-004** and **not** raise a second €450 claim. | Chase CLM-004 once: "INV-2006 chicken billed €6.80 vs €6.50 pricelist — €450 credit due." **No second email** for CLM-006. | Concedes the €0.30/kg overcharge; **issues a single €450 credit**. (Supplier would query / reject a second identical claim — which is why we never send it.) | **CLM-004: Credit-received €450** (once). **CLM-006: Disputed/Voided as duplicate** (`duplicate_of=CLM-004`, internal close, gated). Over-claim risk €450 avoided. |
| 4 | **Riverside Beverages** (SUP-005) | **Damaged goods €1,080 — MISSED, high confidence** (GRN-3005 logged **120 damaged cases** × €9.00, full 2,000 invoiced, nothing claimed). Rebate: Q1 spend €2,600 **below** €50k threshold → **no rebate**, recorded €0. CLM-007 is a **Q4** claim already Paid 18/12 — out of scope, do not reopen. | New claim email: "GRN-3005 records 120 damaged cases; INV billed all 2,000 — please credit 120 × €9.00 = €1,080." | Acknowledges the GRN damage record; **issues €1,080 credit**. | **Credit-received €1,080** (— → new claim → Credit-received). CLM-007 untouched (Q4, Paid). |
| 5 | **Northgate Mills** (SUP-001) | **Volume rebate €1,548 — MISSED, high confidence** (Q1 net spend **€51,600 ≥ €50,000** threshold @ **3%**). Only rebate supplier of four that qualifies. | New claim email: "Q1 net spend €51,600 crossed the €50,000 quarterly rebate threshold at 3% — €1,548 rebate due." (High-value > €1,000 → gate before send.) | Confirms cumulative Q1 spend crossed threshold; **issues €1,548 rebate credit**. | **Credit-received €1,548** (— → new claim → Credit-received) |
| 6 | **Meadowvale Dairy** (SUP-003) | **No claim — CLM-003 is the unit/case trap.** Contract: "Prices quoted per case (12 units/case)." INV-2003 (6,000 units @ €1.50) = PO-1003 (500 cases @ €18.00) = **€9,000 both sides**. €0 discrepancy. Rebate threshold €80k not crossed → €0. | **No email sent** to supplier. Internal-only: close CLM-003 with the per-case normalization shown. | **(No outbound email.)** If anything, an internal note documenting the UoM math. | **Closed — no claim** (WIP → Closed-no-claim; reason: UoM normalized, totals match exactly). |
| 7 | **Sweet Treats Co** (SUP-007) | **No claim — not substantiable.** PO-1007 has **no GRN-3007**; a shortage cannot be proven on evidence. Agent must **not fabricate** a claim. | **No claim email.** Route to a human Question gate (Tom/Jenny): "PO-1007 shortage alleged but no goods-receipt evidence — cannot substantiate." | **(No outbound supplier email.)** Optionally a clarifying internal request for the missing GRN. | **Closed — no claim** (Pending → Closed-no-claim; reason: no GRN evidence). Escalated to human as a Question, not a claim. |
| 8 | **EcoPack Ltd** (SUP-008) | **No claim.** Rebate supplier (threshold €60k @ 2%) but **Q1 spend below threshold** → €0 rebate; no PO/GRN/invoice discrepancy. | **No email sent.** | **(No outbound email.)** | **Closed — no claim** (no tracker row; recorded €0 rebate transparently). |

---

## Demo success criteria (checklist)

### Should end as **Credit-received** (valid credits that land)
- [ ] **Greenfield Farm — €375** (CLM-001, short delivery)
- [ ] **Riverside Beverages — €1,080** (damaged goods, was MISSED)
- [ ] **Northgate Mills — €1,548** (volume rebate, was MISSED, high-value gated)
- [ ] **Sunrise Bakery — €750** (price-gap overcharge, CLM-002)
- [ ] **Prime Cuts Butchers — €450** (chicken overcharge, CLM-004 — **once only**)

**Credits landed = €375 + €1,080 + €1,548 + €750 + €450 = €4,203.**

### Should end as **Disputed / escalated**
- [ ] **Sunrise Bakery promo — €2,000 `[medium confidence]`** — contract lapsed 2026-02-28; simulator disputes/qualifies. Escalate to Finance: full €2,000 vs pro-rated ~€1,333 vs €0. **Not counted in landed recovery.**
- [ ] **Prime Cuts duplicate — CLM-006 €450** — flagged as duplicate of CLM-004, voided/closed internally (gated). **Not a second credit.**

### Should end as **Closed — no claim**
- [ ] **Meadowvale Dairy (CLM-003)** — unit/case trap, €0, no supplier email.
- [ ] **Sweet Treats Co (CLM-005)** — no GRN-3007, unprovable, routed to human Question.
- [ ] **EcoPack Ltd** — below rebate threshold, €0 (no discrepancy).

### End-state recovery number (IF all valid credits land)
```
Owed (Q1 justified)                              €6,203
  − Sunrise promo €2,000   [disputed/uncertain — contract lapsed, NOT landed]
  ──────────────────────────────────────────────────────
End-state recovery (valid credits landed)        €4,203
```
- **€4,203 recovered** (= owed €6,203 − the €2,000 Sunrise promo that is genuinely uncertain/disputed).
- Recovery rate at end-state: **€4,203 / €6,203 ≈ 67.8%** (up from €0 / 0% at start).
- **€450 over-claim avoided** — Prime Cuts CLM-006 duplicate is never sent, so Daily Basket neither chases nor gets paid twice.
- The €2,000 Sunrise promo is the **only** open item: if Finance confirms the full promo (or the supplier concedes), recovery rises to €6,203; if pro-rated, ~€5,536 (€4,203 + ~€1,333); if €0, stays €4,203. **Demo should leave this explicitly flagged, not silently booked.**

### The 3 'trap' behaviors the demo MUST visibly demonstrate
1. **Meadowvale unit/case trap** — the agent reads the contract note ("per case, 12 units/case"), normalizes UoM, proves INV = PO = €9,000, and **closes CLM-003 with €0 and no supplier email**. (Shows it doesn't chase a phantom €99k discrepancy — the very claim Jenny abandoned.)
2. **Sweet Treats no-evidence trap** — PO-1007 has **no GRN-3007**, so the agent **refuses to fabricate** a shortage claim and routes it to a human Question instead of emailing the supplier. (Shows evidence discipline.)
3. **Prime Cuts duplicate trap** — CLM-004 and CLM-006 are the **same €450 overcharge** logged twice (different owners, inconsistent "Butchers"/"butchers" spelling). The agent raises it **once**, flags CLM-006 as a duplicate, and **does not send a second claim**. (Shows dedup + relationship protection.)

---

## Notes for the demo operator
- **Numbers are fixed** — owed €6,203, missed €4,628, over-claim €450, end-state recovery **€4,203**. Do not re-derive on the fly.
- **Gating is part of the story:** high-value new claims (Northgate €1,548) and the Sunrise promo escalate to a human; all outbound supplier emails are gated/approved before the simulator sees them.
- **Out of scope:** Riverside CLM-007 (Q4, already Paid 18/12) and Greenfield CLM-008 (tomato price query — INV = PO, no claim) — leave untouched.
- **The honest read wins the demo:** surfacing €4,628 missed while *qualifying* the €2,000 promo (rather than overstating it) is the credibility moment.
