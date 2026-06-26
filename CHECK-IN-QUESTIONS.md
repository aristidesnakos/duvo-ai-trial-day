# Daily Basket Claims Agent — Check-in Sheet

**Status:** MVP **green** — the engine answers Mark's question with defensible €, verified to the cent (13/13 acceptance tests, independent re-derivation). A live agent is deployed on Duvo Production; one provisioning fix (file delivery via run sandbox) away from a live end-to-end run.

**Headline to relay:**
> **€6,203 owed · €0 recovered · 0% recovery rate · €4,628 missed · €450 over-claim risk caught.**
> Missed money by confidence: **€2,628 high** (Northgate rebate €1,548 + Riverside damaged €1,080) · **€2,000 medium** (Sunrise promo — see Q1).

---

## A. Assumptions we're running on — *derived from the Q1 data; flag any that are wrong*

| # | Assumption | Basis | Confidence |
|---|---|---|---|
| A1 | **Recovered = €0 / 0%** | No Q1 tracker row is `Paid` (the only `Paid` row, CLM-007, is Q4 and excluded). True whether "recovered" means cash-landed or logged. | High |
| A2 | **Northgate rebate = €1,548** | Q1 spend 51,600 ≥ €50k threshold; all three POs OK with no credits, so net = gross; flat 3%. | High |
| A3 | **Dairy (12 units/case) is the only UoM trap** | Only invoice (Meadowvale DRY-101) that restates uom vs its PO; all others match. Normalizing it makes the apparent €99k gap vanish → no claim. | High (this dataset) |
| A4 | **One GRN + one invoice per PO** | No aggregation/partial-delivery cases in Q1 (GRN-3007 is the only *missing* receipt). | High |
| A5 | **Logged-correct claims tie out** | Greenfield short €375 (CLM-001), Sunrise overcharge €750 (CLM-002), Prime Cuts chicken €450 (CLM-004) — line-math matches the tracker. | High |
| A6 | **Tracker corrections** | CLM-006 duplicates CLM-004 (€450 over-claim risk); CLM-003 Meadowvale is a false positive; CLM-005 Sweet Treats unprovable (no GRN-3007); CLM-008 = no claim (invoice = PO). | High |

## B. Open questions — *need your input; ranked by € impact*

| # | Question | What it changes | € at stake |
|---|---|---|---|
| B1 | **Sunrise promo funding** — the contract **lapses 2026-02-28**, two-thirds into Q1. Claim the full €2,000, pro-rate (~€1,333), or void? Is promo automatic or activity-contingent? | Largest single swing in the missed total | **€2,000** (43% of missed) |
| B2 | **Riverside damaged goods** — Riverside's contract is **silent on damage credits** (only Greenfield's grants them). Confirm damaged-on-delivery is creditable as standard (we believe yes) or whether there's a carve-out. | Keeps or removes the €1,080 | **€1,080** |
| B3 | **Credit-window deadlines per supplier** — which claims expire when? We have `payment_terms_days` but not the claim-window rule. | Prioritization — this is the Feb "windows nearly closed" risk made concrete | timing of all €6,203 |
| B4 | **Write boundary for MVP** — identify-only (hand Jenny a claim pack) or human-gated auto-submit? | Defines the build's scope | scope |
| B5 | **Submission target + secrets owner** — what system raises credits, and who owns the auth? | Needed to replace the stubbed write for production | productionization |
| B6 | **GRN-3007** — genuinely missing, or just not in the export? | If the receipt exists, Sweet Treats (CLM-005) flips from unprovable to a real claim | unlocks/closes CLM-005 |

## C. Caveats to flag (not questions)

- **Run-rate €24,812** = Q1 × 4 with seasonality unconfirmed → keep internal unless Finance signs off.
- **"Net spend" VAT-inclusive vs exclusive** only matters for the Riverside near-miss (€2,600 under the €50k rebate threshold) — not for any booked number.

---
*Numbers are the engine's verified output (`python3 -m agent.run`). On the day, re-validate against live exports at the 10:30 scope check before committing the figure to Mark.*
