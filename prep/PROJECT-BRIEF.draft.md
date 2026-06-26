# Project Brief (DRAFT) — Daily Basket Supplier Claims

> One page. Finalize **after discovery (by 11:30)**; lock the € number before writing code.
> `[bracketed]` = confirm on the day.

## Outcome

Recover supplier money Daily Basket is owed, and remove the single-person dependency — by **deriving claims from source systems** (ERP exports + contracts) and reconciling against the existing tracker, **not** by digitizing the spreadsheet as-is.

## Process boundary

- **In scope:** three-way match (PO/GR/Invoice) → discrepancy + contract-entitlement detection → **claim pack** with € and evidence → **human approval**.
- **Out of scope (MVP):** automated claim submission, supplier dispute handling, cash collection. `[confirm with Paula]`

## Systems & data in scope

| Source | Role | Use |
|---|---|---|
| `purchase_orders.csv` | agreed qty & price (ERP) | match input |
| `goods_receipts.csv` | received qty + condition (ERP/GRN) | match input |
| `invoices.csv` | billed qty & price (AP/portal) | match input |
| `supplier_contracts.csv` | prices, rebate thresholds, promo funding | match + entitlements |
| `supplier_claims_tracker.csv` | today's spreadsheet | **reconcile target** (not source of truth) |
| `email_thread.pdf` | how claims get triggered/handed off | trigger + human-gate context |

## Success criteria (in €) — *agree before building*

Anchor on **Mark's actual question** (from the email thread): *"how much are we recovering vs. how much is owed?"* — which Finance currently **cannot answer**.

- **Primary — answer Mark's question:** produce the **€ owed** (total justified Q1 claims) and the **recovery rate** = € already recovered ÷ € owed, split into **missed / logged-correct / over-claimed**, each defensible by line-math.
- **Headline upside:** **€[X] in un-claimed money** the current process never caught — concentrated in **rebate entitlements** (flour/drinks/packaging/dairy) and the **dairy UoM claim Jenny abandoned**.
- **Run-rate:** annualized **€[Y]** (Q1 × 4, seasonality caveat).
- **Resilience:** the process **runs end-to-end without Jenny** (Feb showed credit windows nearly closed when she was out — real € at stake).
- `[Agree exact €X target with Mark/Paula at the 10:30 scope check.]`

## Non-goals

- Not automating the spreadsheet as-is.
- Not auto-submitting claims without human approval (MVP).

## Guardrails

Read-only on ERP/contracts/tracker · the only write is a **human-gated, idempotent** claim submission (stubbed for demo) · transparent arithmetic · explicit UoM normalization (SUP-003 = 12 units/case) · Q1-only (exclude Q4 row) · deterministic demo.

## Ship definition & timebox

- **MVP (by ~15:15):** match + entitlements + reconciliation + claim pack on **live sandbox data**, € quantified.
- **Iteration cap:** max **2 post-MVP cycles** (per the brief's rule). "Good enough to ship" = € total produced, top claims spot-checked correct, demo deterministic.
- **Packaged by 16:45:** proof pack + reusable asset + 5-bullet case study.
