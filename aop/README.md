# Supplier Reconciliation & Claims Agent — Design

Design for a Duvo agent that automates Daily Basket Ltd's PO→GRN→Invoice reconciliation, so claim
recovery stops depending on one person (Jenny) catching what she happens to see.

- **The AOP (paste-ready):** [`reconciliation-agent.aop.md`](./reconciliation-agent.aop.md)
- **Scenario:** `data/` (PO, GRN, Invoice, Contracts, Claims tracker) + `data/email_thread.pdf`

## The problem (from the email thread)

Jenny Walsh (AP) reconciles by hand and only chases a claim "when a supplier emails us or something
looks obviously wrong." Paula Hart (Finance Ops) worries about *what we don't catch* — when Jenny was
out sick "a couple of credit windows nearly closed." Mark (Finance Director) asked "how much are we
actually recovering vs. how much is owed?" and nobody could answer. Jenny's own bet: the real money is
the **volume rebates she never gets to**. The agent is built to answer Mark's question and close that gap.

## What the agent found in Q1 (validated against the data)

This is the output the AOP produces — cross-checked against the existing tracker:

| # | Finding | € | Tracker | Verdict |
|---|---|--:|---|---|
| 1 | Greenfield short delivery, 150 kg (GRN-3002) | 375 | CLM-001 | Real — awaiting credit note |
| 2 | Sunrise rolls overcharge, €0.95 vs €0.80 | 750 | CLM-002 | Real |
| 3 | Prime Cuts chicken overcharge, €6.80 vs €6.50 | 450 | CLM-004 | Real |
| 4 | Prime Cuts — **duplicate** of #3 | −450 | CLM-006 | Remove double-count |
| 5 | Riverside **120 damaged cases** (GRN-3005) | **1,080** | — | **Missed** |
| 6 | Northgate **volume rebate** — €51,600 ≥ €50k @ 3% | **1,548** | — | **Missed** |
| 7 | Sunrise **promo co-funding** | **2,000** | — | **Missed / verify** |
| 8 | Meadowvale "price discrepancy" | 0 | CLM-003 | **False** — close |
| 9 | Sweet Treats short delivery | — | CLM-005 | **Unprovable** — no GRN |
| 10 | Greenfield tomato price query | 0 | CLM-008 | No claim (INV = PO) |

**Headline:** manual process logged ~€1,575 of genuine claims (and €450 of double-count + several
phantom rows). The agent additionally surfaces **~€4,628 in missed recoverable** (damaged + rebate +
promo) — money that was being left on the table exactly as Jenny predicted.

### The three traps the agent has to get right

- **Meadowvale (#8) — the unit/case trap.** Looks like a €99k discrepancy on raw unit price (6,000
  units @ €1.50 vs 500 cases @ €18.00). The contract note *"Prices quoted per case (12 units/case)"*
  resolves it: both totals are €9,000. **No claim.** This is why Jenny "couldn't get the numbers to
  line up" — there was nothing there. The agent must read `notes` and compare on line totals.
- **Sweet Treats (#9) — no evidence.** There is no GRN-3007. Without receipt evidence a shortage is
  unprovable; the agent must *not* invent a claim, and routes it to a human Question gate.
- **Prime Cuts (#4) — the duplicate.** CLM-004 and CLM-006 are the same €450 overcharge logged twice
  (different owners, inconsistent supplier spelling). The agent flags the pair instead of chasing €900.

## Key design decisions (and why)

| Decision | Choice | Why / docs |
|---|---|---|
| **Trigger** | Scheduled weekly sweep + quarter-end rebate run, **plus** file-drop on new invoice PDFs | Weekly catches discrepancies before credit windows close (Paula's risk); quarter-end is when rebates/promo crystallize; file-drop gives near-real-time intake. (Scheduling Agents; File-Drop Triggers) |
| **Compare on** | Line **total after unit normalization**, not raw unit price | Avoids the Meadowvale false positive; `uom` legitimately varies between PO and invoice |
| **Evidence rule** | No GRN ⇒ unprovable, never an auto-claim | Prevents fabricated claims (Sweet Treats); preserves auditability |
| **Tracker writes** | Append `Draft — agent-detected` rows freely; **gate** any edit/void/merge of a human row | HITL tiers: routine+reversible runs free; destructive-internal always gated (HITL Design) |
| **Outbound email** | Always gated, one-click approve, full body shown | Tier-1 irreversible external action (HITL Design) |
| **High-value claims** | Gate new agent claims > €1,000 (rebate, promo) | Tier-3 high-value transaction |
| **Memory** | `processed_invoices` (dedup) + `quarter_spend` (cumulative rebate tracking) | File-drop dedup pattern; rebates need cross-run cumulative state (Agent Memory) |
| **Data safety** | `data/` read-only; normalize into new fields; keep `status_raw` | Never destroy the human's ground truth |

## Connections required

ERP / Google Sheets (source data, read-only) · Claims tracker Sheet (read/write) · Intelligent
Document Reader + Email Attachments Reader (invoice PDFs) · Email / shared `claims@` mailbox (gated
send) · Slack (optional reporting) · Agent Memory.

## Human-in-the-loop summary

Gate **always:** outbound supplier emails (Tier 1); void/close/merge human tracker rows (Tier 2).
Gate **conditionally:** new claims > €1,000 (Tier 3); ambiguous damaged-goods eligibility and
unprovable claims (Tier 4, as Questions). **No gate:** status/name/date normalization and `Draft`
appends (Tier 5). Approvals time out before the credit window and escalate to Paula; two rejections
halt and flag for manual review.

## Documentation grounding

Built against the Duvo docs (index: <https://docs.duvo.ai/llms.txt>):
[AOP](https://docs.duvo.ai/user-guide/building-assignments/assignment-sop) ·
[Purchase Order Processing](https://docs.duvo.ai/user-guide/examples/purchase-order-processing) ·
[Designing HITL Workflows](https://docs.duvo.ai/user-guide/assignment-features/hitl-design) ·
[File-Drop Triggers](https://docs.duvo.ai/user-guide/assignment-features/file-drop-triggers) ·
[Scheduling](https://docs.duvo.ai/user-guide/assignment-features/scheduling-assignments) ·
[Agent Memory](https://docs.duvo.ai/user-guide/assignment-features/assignment-memory) ·
[Guardrails for High-Risk Automations](https://docs.duvo.ai/user-guide/security/high-risk-guardrails)

## Reproduce the analysis

The validation script lives in the session scratchpad (`recon.py`); it reads `data/` read-only and
prints the three-way match + rebate check. The findings table above is its output, hand-verified.
