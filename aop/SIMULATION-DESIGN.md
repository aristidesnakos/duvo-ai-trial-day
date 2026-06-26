# Surrogate ERP — Simulation Design, Gaps, and the Fix

How the Daily Basket claims simulation works from scratch, where the current design is too thin,
and the change that makes it a faithful two-party reconciliation.

## 1. The mental model: two parties, two sources of truth, one channel

A grocer and a supplier never share a database. Each keeps its **own books** and they reconcile
across a boundary by correspondence:

```
   DAILY BASKET (grocer)                 │  CHANNEL  │            SUPPLIER
   what WE believe                       │           │            what THEY believe
   ─────────────────────                 │           │            ─────────────────────
   PurchaseOrders  (what we ordered)     │           │   their sales order / dispatch note
   GoodReceipts    (what we received)    │  claims → │   their record of what they shipped
   Invoices        (what we were billed) │  ← credit │   their invoice + pricelist
   Contracts       (our copy of terms)   │   notes   │   their copy of terms + prior credits
   ClaimsTracker   (what we're chasing)  │           │   their dispute log
```

A claim is **us asserting a discrepancy from our data**. A resolution is the supplier checking it
**against their data** and either agreeing (credit note) or disagreeing (dispute). The interesting
behaviour — credits, stalls, denials — should *emerge from the two datasets disagreeing*, not from a
script.

## 2. The cast (two Duvo agents)

| Agent | Plays | Reads | Writes |
|---|---|---|---|
| **Reconciliation agent** (`eb165d7e…`) | Daily Basket / Jenny | grocer ERP tabs + Correspondence | ClaimsTracker, Correspondence (claims) |
| **Supplier Simulator** (`e6e3b6e5…`) | all 8 suppliers | *(should be:)* supplier books + Correspondence | Correspondence (responses) |

Both run as `ari.nakos@duvo.ai` on one Google Sheets connection — fine for a demo, but see Gap #4.

## 3. The current design (what we built)

One workbook, "Daily Basket - Surrogate ERP", with tabs:
`PurchaseOrders · GoodReceipts · Invoices · Contracts · ClaimsTracker · Correspondence`.

The **Correspondence** tab is the channel (the message bus that replaced email):
`corr_id | claim_id | supplier | supplier_slug | request_summary | amount_requested_eur | requested_at | status | response_type | amount_credited_eur | supplier_note | responded_at | resolution | resolved_at`

The closed loop:
1. Reconciliation agent reconciles the grocer tabs → writes findings to ClaimsTracker → appends a
   claim row to Correspondence (`status = awaiting_reply`).
2. Simulator reads `awaiting_reply` rows → writes a response (`credit_full` / `dispute` / `stall` /
   `deny`) → `status = replied`.
3. Reconciliation agent reads `replied` rows → updates ClaimsTracker (Recovered / Disputed-escalated)
   and reports owed-vs-recovered.

## 4. Gaps in the current design

- **G1 — One source of truth.** The supplier has *no independent data*. Everything lives in our
  workbook, so the simulator can't reconcile "their books" against our claim — there are no "their
  books." This is the core unrealism you flagged.
- **G2 — The simulator is omniscient/scripted.** Its AOP hardcodes the ground-truth verdicts
  (Greenfield €375, Sweet Treats deny, etc.). A real supplier doesn't know our answer; it reasons
  from *its* records. As written, the simulator can never legitimately be wrong, surprised, or
  partially right — so it isn't really a counterparty, it's an answer key.
- **G3 — Disputes aren't data-grounded.** Sweet Treats "we delivered in full," Sunrise "let me check
  with finance," the promo lapse — these are *positions* that should sit in the supplier's data and
  drive the reply. Right now they're narrative instructions, so the demo can't show a genuine
  data-vs-data reconciliation (which is the whole point of the product).
- **G4 — No privacy boundary.** Both agents share one workbook and one Google account, so either can
  read/write the other's "private" tabs. Acceptable for a single-machine demo; note it as a
  simplification, not the real architecture.
- **G5 — No turn-taking trigger.** Nothing makes the simulator run *after* the grocer raises claims.
  Today we run them in sequence by hand. In production this is a **Status-Change trigger or a Queue**
  (grocer posts → simulator wakes → grocer wakes on reply). Worth stating as the productionization path.
- **G6 — Double-counting risk.** ClaimsTracker is seeded with the existing human claims *and* the
  agent re-derives claims; the AOP's bucketing (matched / missed / duplicate) handles this, but it's
  the most error-prone seam and should be watched in the demo.

## 5. The fix — give the supplier its own books (Level 1, recommended)

Add **one tab the simulator alone reasons from**, representing each supplier's private view:

**`SupplierLedger`** (the supplier's truth):
`supplier_slug | po_ref | sku | qty_they_shipped | unit_price_they_billed | unit_basis | their_terms_note | prior_credits | stance`

Then change the rules of the game:
- The **simulator reads ONLY `SupplierLedger` + the incoming Correspondence claim** — never our GRN,
  never the answer key. It compares our claim against *its* row and decides: agree → credit; its
  number differs → dispute with its figure; no record → deny; terms lapsed → partial.
- Disputes now **emerge from data**. We author the ledger so it mostly corroborates our claims (the
  recoverable money is real) but **intentionally diverges** in the instructive cases:
  - *Greenfield*: ledger also shows 850 kg shipped (driver noted the shortage) → agrees → credit €375.
  - *Sweet Treats*: ledger shows gummy bears **shipped in full** → genuinely denies; our missing
    GRN-3007 means neither side can prove it → stalemate (the honest outcome).
  - *Meadowvale*: ledger shows **per-case** pricing → explains the unit basis → no credit (our false
    positive, now refuted by their data, not by a script).
  - *Sunrise*: ledger shows the promo **contract end 2026-02-28** → offers the pro-rated €1,333, not
    €2,000; the rolls overcharge is real in their pricelist → concedes €750 after the finance check.
  - *Prime Cuts*: ledger shows one €450 line → credits once, disputes the duplicate as "already
    raised."
- The reconciliation agent never sees `SupplierLedger`; the simulator never sees `GoodReceipts`. The
  Correspondence tab is the only thing they share — a real boundary.

This is a small change (one tab + a simulator-AOP rewrite to "reason from your ledger, don't use an
answer key") but it converts the demo from *scripted theatre* into a *genuine two-source
reconciliation* — which is exactly the capability we're selling.

## 6. Boundaries & safety (unchanged)

- No real email, ever — all contact is Correspondence rows.
- Source/ERP tabs are read-only to the grocer agent; SupplierLedger is read-only to the simulator.
- HITL gates stay: the grocer escalates genuine disputes (Sweet Treats stalemate, Sunrise promo) to a
  human rather than conceding or fabricating.
- One reply per claim (Agent-Memory dedup) prevents loops.

## 7. Recommended next step

Implement Level 1: add the `SupplierLedger` tab to the seed, rewrite the simulator AOP to reason from
it (drop the answer-key matrix), and keep the grocer agent as-is. Then run the loop and watch real
agreements and disputes fall out of the data. Two separate workbooks / accounts (full privacy) is a
later upgrade and not needed to prove the point.
