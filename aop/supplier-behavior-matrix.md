# Supplier Behavior Matrix — Supplier Simulator

The Supplier Simulator agent role-plays all 8 Daily Basket Ltd suppliers in the
closed-loop demo. It operates the `ari.nakos@duvo.ai` mailbox, watches for claim
emails addressed to `ari.nakos+<supplier>@duvo.ai` with subject `[DB-CLAIM <claim_id>]`,
and replies once per thread (subject prefixed `[SUPPLIER-REPLY]`) in character.

Each reply is **grounded in ground truth** so the reconciliation agent's correct
claims get validated and its mistakes get pushed back on. Ground-truth verdicts
are from the validated Q1 findings (`aop/README.md`) and the source data
(`data/supplier_contracts.csv`, `data/supplier_claims_tracker.csv`).

| Supplier | Alias (`ari.nakos+…`) | Claim type | Ground-truth verdict | Simulated reply behavior | Expected end state |
|---|---|---|---|---|---|
| Northgate Mills (flour) | `+northgate` | Volume rebate | **Owed €1,548** — Q1 net spend €51,600 ≥ €50k @ 3% | Acknowledge rebate is due; confirm a credit note will issue for Q1 | Rebate **confirmed**, credit note promised |
| Greenfield Farm (tomatoes) | `+greenfield` | Short delivery (CLM-001) | **Valid €375** — 150 kg short, GRN-3002 evidence | Agree against GRN; issue €375 credit note | Short delivery **credited €375** |
| Greenfield Farm (tomatoes) | `+greenfield` | Price query (CLM-008) | **No discrepancy** — invoice price = PO price | Explain prices match; nothing to credit | Price query **closed**, no credit |
| Meadowvale Dairy | `+meadowvale` | Price discrepancy (CLM-003) | **No claim** — prices per case (12 units/case); €18/case = €1.50/unit, totals tie to €9,000 | If wrongly claimed: politely explain unit/case convention, show totals match, decline. If not claimed: nothing to do | Claim **declined / not raised** (false positive avoided) |
| Sunrise Bakery | `+sunrise` | Rolls overcharge (CLM-002) | **Valid €750** — billed €0.95 vs agreed €0.80 | Role-play "Harry": **stall** first ("check with finance", delay); **concede** only after a follow-up | Overcharge **conceded €750** after one nudge |
| Sunrise Bakery | `+sunrise` | Promo co-funding | **Disputed** — promo contract lapsed 2026-02-28, full quarter not due | Dispute / pro-rate; push back, offer ~€1,333 not €2,000 | Promo **pro-rated** (~€1,333), full €2,000 refused |
| Riverside Beverages | `+riverside` | Damaged goods | **Valid €1,080** — 120 damaged cases, photos/GRN-3005 exist | Accept; issue credit note (consistent with their Q4 damaged-goods credit) | Damaged goods **credited €1,080** |
| Prime Cuts Butchers | `+primecuts` | Chicken overcharge (CLM-004) | **Valid €450** — €6.80 vs €6.50/kg pricelist | Credit one €450 | Overcharge **credited €450 once** |
| Prime Cuts Butchers | `+primecuts` | Duplicate overcharge (CLM-006) | **Duplicate** — same €450 line as CLM-004 | Dispute: same invoice line already being credited; decline duplicate | Duplicate **declined** (no double credit) |
| Sweet Treats Co | `+sweettreats` | Short delivery (CLM-005) | **Unprovable** — GRN-3007 missing, no receipt evidence | Insist delivered in full; ask Daily Basket for their GRN/proof | **No credit** — unprovable, no evidence |
| EcoPack Ltd | `+ecopack` | Packaging rebate | **Not owed** — Q1 net spend €35,700 < €60k threshold | Explain quarterly threshold not reached; no rebate this quarter | Rebate **declined**, threshold not met |

## How to read this

- **Validated by the simulator** (agent did the right thing): Northgate rebate,
  Greenfield €375, Sunrise rolls €750 (after a nudge), Riverside €1,080, Prime
  Cuts one €450. Total genuine recoverable the simulator confirms ≈ €4,253 plus
  the pro-rated Sunrise promo (~€1,333).
- **Pushed back on** (agent should NOT have claimed, or over-claimed): Meadowvale
  unit/case false positive, Sweet Treats no-GRN, Prime Cuts CLM-006 duplicate,
  EcoPack threshold not met, Sunrise full €2,000 promo.

## Loop guarantees

- **One reply per claim thread.** Processed message ids and `(supplier, claim_id)`
  pairs are tracked in Agent Memory; a re-read never produces a second reply.
- **Sunrise is the only two-touch supplier:** stall first, concede on follow-up.
  Memory records whether CLM-002 has been stalled vs conceded so the concession
  fires exactly once and no third reply is sent.
- **Routing safety:** replies stay on-thread, from `ari.nakos@duvo.ai`, never to
  any external/real domain. Unclassifiable suppliers or claims escalate to HITL
  instead of guessing.
