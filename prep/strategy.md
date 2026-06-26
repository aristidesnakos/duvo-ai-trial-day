# Daily Basket — Angle of Attack (pre-day prep)

> Scenario: FDE trial, Daily Basket (online grocer, ~€180M GMV). Embedded with Finance Ops.
> Sponsor **Paula Hart** (Finance Ops Lead) · operator **Jenny Walsh** · economic buyer **Mark Bryant** (Finance Director — "numbers that move").

## One-sentence frame

> Finance Ops is owed money by suppliers (short/damaged deliveries, prices above contract, earned volume rebates & promo funding) but the claims process lives in one person's spreadsheet — so money that was never logged is never recovered. We ship an agent that **independently derives the claims that *should* exist** from the ERP exports + contracts, **reconciles them against the tracker**, and surfaces **recoverable € with an auditable, human-gated claim pack** — and runs whether or not Jenny is in.

## Archetype match (field kit)

- **Primary:** Cross-system reconciliation — the three-way match `PO ↔ Goods Receipt ↔ Invoice`.
- **Secondary:** Contract entitlement (rebates/promo) — derive earned-but-unclaimed money from Q1 volumes vs contract thresholds.
- **Tertiary:** Completion / chasing loop — the un-logged long tail nobody gets to ("money never claimed at all").

## The push-back (consultants, not order-takers)

Stated ask: *"Automate our supplier-claims spreadsheet."* **Don't digitize the sheet as-is.** Reasons to bring to discovery:

1. **The spreadsheet is the failure mode, not the system of record.** Single-owner (stops when Jenny's out), holds errors and omissions, and — per the data note — *money that should have been claimed was never logged at all*. Automating it forward-propagates the gaps.
2. **Truth lives upstream.** PO/GR/Invoice (ERP) + contracts are the source. The agent should **derive** claims from source, then use the tracker only as a **reconciliation target**: what we caught vs. what we missed vs. what we logged wrong.
3. **Reframe the outcome** from "digitize sheet" → "**recover the money we're owed and remove the single-person dependency**." That is the € Mark can feel.

## What the agent does (smallest safe slice, end-to-end)

1. **Three-way match** per `po_id`: PO (agreed qty/price) ↔ GR (received qty + condition) ↔ Invoice (billed qty/price). Flag **short delivery, damage, price-above-contract**.
   - **UoM guard:** SUP-003 (dairy) quotes **per case = 12 units**. Normalize units before any price-gap comparison. Assume other UoM traps exist until proven otherwise.
2. **Contract entitlements:** per supplier, compute **earned volume rebate** (Q1 volume vs threshold) and **promo funding** owed.
3. **Reconcile derived vs tracker** → three buckets:
   - **(a) Missed** — should-claim, not logged → *recoverable upside, the headline*.
   - **(b) Logged-correct** — already on it.
   - **(c) Logged-wrong / over-claimed** — risk / cleanup.
4. **Claim pack** per justified claim: supplier, PO, basis, **€ amount**, evidence (the three source rows), confidence. **Human approves before "submit."**
5. **Output:** recoverable € (Q1) + annualized run-rate; key-person risk eliminated.

## Guardrails (non-negotiable)

- **System of record = ERP exports + contracts (read).** Tracker = reconcile target (read). **Claim submission is the only write** — human-gated, idempotent per `(po_id, claim_type)`.
- **Transparent arithmetic, not opaque inference** — every € is defensible line-math a buyer can hold up in front of a supplier.
- **UoM normalization is explicit** in the logic and the evidence.
- **Period discipline:** Q1 2026 is closed as of early Apr 2026 → claimable. Exclude the Q4 row from Q1 totals.
- **Mock-first, deterministic.** "Submit claim" stubbed for the demo; same input → same € every run.

## Success in € (framework — agree exact numbers on the day, before building)

- **Recoverable Q1 €** = Σ justified (short + damage + price-gap) claims + Σ earned-but-unclaimed (rebate + promo) − already-correctly-claimed.
- **Headline = "missed money"** — what today's process never caught.
- **Run-rate** = Q1 × 4 (annualized; caveat seasonality).
- **Secondary:** single-person risk removed (runs without Jenny); cycle time per claim; over-claim risk surfaced.

## Risks & data traps to probe early

- UoM beyond SUP-003 (per-case vs per-unit). Pack/case sizes per supplier.
- How "damaged" is coded in goods receipts; partial deliveries / multiple GRs per PO.
- Rebate threshold basis: gross vs net, per-period, tiered? Promo funding trigger conditions.
- Tracker statuses (open/paid/disputed) — what "claimed" actually means and when cash lands.
- The single Q4 row — out of period, exclude from Q1 €.
- `email_thread.pdf` — who triggers a claim and how it's handed off → informs the human gate and the chasing loop.

## Sequence on the day (maps to the 09:00–17:45 schedule)

1. **Discovery (09:30–10:30):** run the decomposition frame out loud; ask the questions in `discovery-questions.md`; make the push-back case; get one real example of each claim type.
2. **Brief + scope check (10:30–11:30):** finalize `PROJECT-BRIEF.md`, lock € success criteria, confirm the write boundary (identify-only vs submit).
3. **Build (11:30–15:15):** three-way match → entitlements → reconciliation → claim pack, mock-first then against live data. One capable agent.
4. **Ship + package (15:15–16:45):** proof pack (before/after €), reusable asset (the match/reconcile runbook or template), 5-bullet case study. **Packaged by 16:45.**
5. **Present (17:00):** demo the agent, walk the proof pack, point to the asset + case study, give the "where this account goes next" read.
