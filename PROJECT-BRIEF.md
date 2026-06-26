# Project Brief — Daily Basket Supplier Claims

> One page. Success locked in € (computed from the Q1 2026 data). Items marked **`[confirm on day]`** depend on live discovery and are genuinely open until then; everything numeric is derived and fixed.

## Outcome

Recover supplier money Daily Basket is owed, and remove the single-person dependency — by **deriving claims from source systems** (ERP exports + contracts) and reconciling against the existing tracker, **not** by digitizing the spreadsheet as-is.

## Process boundary

- **In scope:** three-way match (PO/GR/Invoice) → discrepancy + contract-entitlement detection → **claim pack** with € and evidence → **human approval**.
- **Out of scope (MVP):** automated claim submission, supplier dispute handling, cash collection. `[confirm with Paula]`

## Systems & data in scope

| Source | Role | Use |
|---|---|---|
| `purchase_orders.csv` | agreed qty & price (ERP) | match input |
| `good_receipts.csv` | received qty + condition (GRN) | match input |
| `invoices.csv` | billed qty & price (AP) | match input |
| `supplier_contracts.csv` | prices, rebate thresholds, promo funding | match + entitlements |
| `supplier_claims_tracker.csv` | today's spreadsheet | **reconcile target** (not source of truth) |
| `email_thread.pdf` | how claims get triggered/handed off | trigger + human-gate context |

## Success criteria (in €) — *locked from Q1 2026 data*

Anchored on **Mark's actual question** (from the email thread): *"how much are we recovering vs. how much is owed?"* — which Finance currently **cannot answer**.

- **Answer to Mark's question:** **€6,203 owed · €0 recovered · 0% recovery rate**, split **missed / logged-correct / over-claimed**, each defensible by line-math.
- **Headline upside — missed money:** **€4,628** the current process never logged — Riverside damaged goods €1,080 + Northgate volume rebate €1,548 + Sunrise promo funding €2,000.
- **Risk surfaced:** **€450** over-claim (Prime Cuts logged twice, CLM-004 + CLM-006) caught before it reaches a supplier.
- **Run-rate:** annualized **€24,812** (Q1 × 4; seasonality caveat — confirm with Finance before quoting externally).
- **Resilience:** the process **runs end-to-end without Jenny** (Feb showed credit windows nearly closed when she was out — real € at stake).

> The € target is no longer a placeholder — it is the engine's verified output (`python3 -m agent.run`, 18/18 acceptance criteria). On the real day, validate the figure against live exports at the 10:30 scope check before committing it to Mark.

## Non-goals

- Not automating the spreadsheet as-is.
- Not auto-submitting claims without human approval (MVP).

## Guardrails

Read-only on ERP/contracts/tracker · the only write is a **human-gated, idempotent** (`po_id|claim_type`), value-capped claim submission (stubbed for demo) · transparent arithmetic · explicit UoM normalization (dairy = 12 units/case) · Q1-only (exclude Q4 row) · deterministic demo.

## Ship definition & timebox

- **MVP:** match + entitlements + reconciliation + claim pack on the Q1 data, € quantified. **Done — green.**
- **Iteration cap:** max **2 post-MVP cycles** (per the brief's rule). "Good enough to ship" = € total produced, top claims spot-checked correct, demo deterministic.
- **Packaged:** proof pack + reusable asset + 5-bullet case study + Duvo AOP design.

## Open items pending live discovery `[confirm on day]`

- Write boundary: identify-only vs human-gated submit for MVP (`[confirm with Paula]`).
- Tracker semantics: statuses, what "recovered" means (cash landed vs logged), when credit windows close.
- Rebate basis (gross/net, tiered) and promo trigger conditions; all supplier pack/case sizes (UoM traps beyond dairy); how damage is coded; multiple GRs per PO.
- Real claim-submission target + auth (to replace the stub) and who owns those secrets.
