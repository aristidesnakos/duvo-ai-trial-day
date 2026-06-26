# Auto-Handoff — making the two-agent loop self-advance

How to turn the Daily Basket reconciliation loop from a **human-driven turn-taker**
(`duvo runs start` … `duvo runs respond --approve` … `duvo runs start` …) into a
**self-advancing loop** that runs without someone firing each step.

This is a *design + runbook* document. Per the trial-day guardrails, nothing here has
been created, updated, or deleted — every command below is verified against
`--help` / `triggers types` but is presented for you to run, not run by me.

## The loop, as built today

Two agents share one Google Sheets workbook (the "surrogate ERP"). The handoff lives
in the **`Correspondence` tab**, whose `status` column flows:

```
awaiting_reply  ──(simulator answers)──▶  replied  ──(recon resolves)──▶  resolved
```

| Resource | ID |
|---|---|
| Reconciliation agent (grocer / "Jenny") | `eb165d7e-c8aa-43d3-84ff-055fbcc961e3` |
| Supplier Simulator (the 8 suppliers) | `e6e3b6e5-0037-4f88-a774-18abaa52dc0b` |
| Google Sheets connection | `0542cc25-…` |
| Workbook spreadsheet | `1GeJpvll8va5_KJE8BlbC8EBAwbdAmFoUZY15vJ9ya-g` |

**The handoff is already idempotent at the AOP level** — this is the precondition that
makes auto-advance safe:

- Each agent **writes only the other role's pending rows**: recon raises rows as
  `awaiting_reply`; the simulator acts *only* on `status = "awaiting_reply"` with blank
  response columns and a known `supplier_slug`; recon acts only on `replied` rows.
- Each agent **dedups on Agent Memory**: simulator keeps `processed_corr_ids` (one
  response per `corr_id`, the explicit "loop-breaker"); recon keeps `processed_invoices`
  + `quarter_spend`.
- Each write **flips the status flag**, so a re-read of the same tab does not reproduce
  work already done.

So the only thing missing for unattended operation is a **mechanism that fires the runs**
in place of the human. Three options follow.

---

## Option A — Schedules (polling)  ◀ RECOMMENDED for the demo

Each agent gets a recurring schedule. On every tick it opens the `Correspondence` tab,
finds the rows in *its* inbound status, processes them idempotently, and ends. No
message is needed — the work to do is discovered from the Sheet (see the Unattended-run
AOP addendum below).

**Verified flags** (`duvo agents schedules create --help`):

```
--frequency   every_5_minutes | every_15_minutes | hourly | daily | workday | weekly | monthly | custom
--timezone    IANA tz, e.g. Europe/Amsterdam
--time        HH:MM      (required for daily/workday/weekly/monthly)
--day         monday…sunday   (weekly)
--day-of-month 1-31           (monthly)
--cron        <expr>          (required for custom)
--disabled    create paused
--no-recurring  retire after first run
```

`every_5_minutes` / `every_15_minutes` take **no `--time`** — they just fire on that
cadence. (Note: an agent supports up to **5 concurrent schedules**.)

### Design

- **Simulator** on `every_5_minutes`: process any `status = awaiting_reply` rows; reply
  from the ledger; flip to `replied`; dedup on `processed_corr_ids`.
- **Reconciliation** on `every_5_minutes`, **offset** so the two don't collide: process
  `status = replied` rows (bank credits, post follow-ups, resolve), raise any new claims,
  flip to `resolved`. The published preset frequencies don't take an explicit offset,
  so to phase them apart use **`--frequency custom --cron`** on one agent (e.g.
  recon at minutes `2,7,12,…`) while the simulator stays on `every_5_minutes` (minutes
  `0,5,10,…`). On the small Q1 dataset a half-overlap is harmless because the status
  flags + memory make a double-read a no-op — the offset is a politeness/clarity measure,
  not a correctness requirement.

Idempotency is **already guaranteed by the AOPs** (`processed_corr_ids`, `processed_invoices`,
status flags). Schedules add nothing that breaks that — a tick with no pending rows just
ends.

### Exact create commands

```bash
# Simulator — answer awaiting_reply rows every 5 minutes
duvo agents schedules create e6e3b6e5-0037-4f88-a774-18abaa52dc0b \
  --frequency every_5_minutes \
  --timezone Europe/Amsterdam

# Reconciliation — process replied rows + resolve, offset by ~2 min via custom cron
duvo agents schedules create eb165d7e-c8aa-43d3-84ff-055fbcc961e3 \
  --frequency custom \
  --cron "2,7,12,17,22,27,32,37,42,47,52,57 * * * *" \
  --timezone Europe/Amsterdam
```

(If you prefer both on the simple preset and accept the harmless overlap, use
`--frequency every_5_minutes` on the recon agent too.)

### Cost, pause, delete

- **Cost = perpetual runs.** Two agents at `every_5_minutes` = ~576 runs/day **even when
  there is nothing to do** (each empty tick still spins up a run that reads the tab).
  For a short demo that's fine; for anything left running, drop to `every_15_minutes` or
  `hourly`, or pause when idle. This is the main downside of polling.
- **Pause** (keeps the schedule, stops firing):
  ```bash
  duvo agents schedules list <agent-id>                          # find <schedule-id>
  duvo agents schedules update <agent-id> <schedule-id> --disable
  ```
  Re-enable with `--enable`. (You can also create paused with `--disabled`.)
- **Delete** (remove entirely):
  ```bash
  duvo agents schedules delete <agent-id> <schedule-id> -y
  ```

---

## Option B — Event-driven via `google_drive_item_event`

Instead of polling, fire each agent when the **workbook file changes** in Drive. The
trigger type exists and is confirmed available on these agents.

**Verified** (`duvo agents triggers types <agent>` and `… set --help`):

- Integration slug: `googledrive`; trigger type: `google_drive_item_event`
  ("When a file or folder is created, updated, renamed, moved, or trashed in Drive").
- `duvo agents triggers set --integration <slug> --trigger-type <type> --filter-config <json>`
  ( `--disabled` to pause). **The integration must already be connected to the agent.**
- Filter schema (verified) requires `event_type` and `item_kind`, and supports
  `scopes` (file/folder URIs, max 25), `mime_type`, `filename_glob`:
  ```json
  {
    "event_type": ["updated"],
    "item_kind":  ["file"],
    "mime_type":  ["application/vnd.google-apps.spreadsheet"],
    "scopes":     ["https://docs.google.com/spreadsheets/d/1GeJpvll8va5_KJE8BlbC8EBAwbdAmFoUZY15vJ9ya-g"]
  }
  ```

### ⚠ The loop-storm risk

Both agents **write the same Sheet**. A Drive "updated" event doesn't know *which*
cells changed or *who* changed them. So:

- Recon writes a new `awaiting_reply` row → Sheet "updated" → **fires the simulator**
  (intended) **and re-fires recon itself** (not intended).
- Simulator writes `replied` → Sheet "updated" → **fires recon** (intended) **and
  re-fires the simulator** (not intended).

Without a guard this is a **self-sustaining storm**: every write triggers more runs,
each of which may write again, ad infinitum — far worse than polling's bounded tick rate.

### Required guards (all three, together)

1. **Act only on the other role's pending rows.** A fired run must first check whether
   any rows in *its* inbound status exist (`awaiting_reply` for the simulator, `replied`
   for recon). If none, **end immediately, writing nothing.** This is already how the
   AOPs are written — it's what stops a self-fired run from doing work.
2. **Dedup on memory.** `processed_corr_ids` / `processed_invoices` ensure that even a
   spurious fire on an already-handled row is a no-op.
3. **Ignore self-writes.** The cleanest structural fix is to **split the surface**: have
   each agent write to a tab/file the *other* watches, not the one it watches — e.g. two
   files (recon→file, sim→file) so an agent never triggers itself. With a single workbook
   that isn't possible at file granularity (the trigger is per-*file*, not per-*tab*), so
   you must lean on guards (1)+(2). If the trigger payload exposes the editor identity,
   add "skip if last editor == self"; **mark this uncertain — the verified filter schema
   does not expose an editor/last-modifier filter**, so don't assume it.

### Command shape (if you choose B)

```bash
# Simulator: fire on workbook update
duvo agents triggers set e6e3b6e5-0037-4f88-a774-18abaa52dc0b \
  --integration googledrive \
  --trigger-type google_drive_item_event \
  --filter-config '{"event_type":["updated"],"item_kind":["file"],"mime_type":["application/vnd.google-apps.spreadsheet"],"scopes":["https://docs.google.com/spreadsheets/d/1GeJpvll8va5_KJE8BlbC8EBAwbdAmFoUZY15vJ9ya-g"]}'

# Reconciliation: same trigger on the same file
duvo agents triggers set eb165d7e-c8aa-43d3-84ff-055fbcc961e3 \
  --integration googledrive \
  --trigger-type google_drive_item_event \
  --filter-config '{"event_type":["updated"],"item_kind":["file"],"mime_type":["application/vnd.google-apps.spreadsheet"],"scopes":["https://docs.google.com/spreadsheets/d/1GeJpvll8va5_KJE8BlbC8EBAwbdAmFoUZY15vJ9ya-g"]}'
```

**Uncertain bits to verify before relying on B:** (a) whether the Google Sheets
connection (`googlesheets` slot) satisfies the `googledrive` trigger's "integration must
already be connected" requirement, or whether a separate Drive connection is needed;
(b) the debounce/coalescing behavior of "updated" events on a spreadsheet (a single agent
edit can emit several cell-level updates); (c) whether the payload carries a last-editor
field for a self-write filter. These are the reasons B is **not** the demo choice.

---

## Option C — Case queue (producer / consumer)  ◀ production-grade target

The documented Duvo multi-agent pattern (Multi-Agent Process Decomposition; Case Queues):
model each claim as a **Case** in a **Queue**.

- **Reconciliation = producer.** It identifies discrepancies and **adds one Case per
  claim** to the queue (with `corr_id`/`invoice_ref` as the lineage / correlation ID).
- **Supplier Simulator = consumer.** It has a **case trigger** on that queue; when a new
  Case arrives the trigger automatically dispatches it to claim and process the Case, then
  explicitly **completes / postpones / fails / escalates** it. (Only one agent holds the
  active trigger per queue.)

Cases move `Pending → In Progress → Completed/Failed/Postponed`. This is the most robust,
genuinely event-driven design: no polling cost, no loop-storm (the queue, not a shared
file, is the handoff surface, so writes don't re-trigger), and built-in backpressure +
audit lineage.

**Cost:** it's a **bigger change** — claims must be re-modeled as Cases rather than rows
in the `Correspondence` tab, the queue must be created and the consumer's case trigger
wired, and both AOPs rewritten to produce/consume Cases instead of reading/writing the
Sheet. Worth it for production; too much surface change to introduce mid-demo.

Docs: *Multi-Agent Process Decomposition*
(`/user-guide/building-assignments/process-decomposition`) and *Case Queues*
(`/user-guide/assignment-features/case-queue`).

---

## Recommendation

**Use Option A (Schedules) for the demo.** It is predictable, has **no loop-storm**
(a tick reads, acts, ends — it never re-triggers anything), is trivial to **pause**
(`--disable`) or **delete**, and rides on the idempotency the AOPs already have. The
only cost — perpetual empty ticks — is negligible at demo scale and easily throttled.

**Hold Option C (case queue) as the production target.** Once the loop needs to run
unattended for real, re-model claims as Cases and let a case trigger drive the consumer:
event-driven, no polling cost, no storm, with lineage tracking for audit. **Avoid
Option B** unless A/C are unavailable — the shared-file re-trigger problem makes it the
fragile choice here.

---

## Unattended-run AOP addendum

A scheduled (or triggered) run arrives with **no human message**. Both AOPs need a few
lines so a no-message run knows to **detect pending work from the `Correspondence` tab
and process it idempotently** — and knows what to do when a human gate would normally
block but no human is present.

### Reconciliation agent

- **No message ⇒ poll mode.** If started with no instruction, open the `Correspondence`
  tab. Collect rows where `status = "replied"` (supplier has answered) and any newly
  reconcilable invoices. If none, end the run without writing.
- For each `replied` row: bank credits, post a follow-up if the supplier stalled, and set
  `status = "resolved"` once settled. Raise any new claims as new `awaiting_reply` rows.
- Dedup on Agent Memory (`processed_invoices`, `quarter_spend`); never re-process a
  `corr_id`/invoice already recorded. Status flags + memory make a repeat tick a no-op.

### Supplier Simulator

- **No message ⇒ poll mode.** Open the `Correspondence` tab. Collect rows where
  `status = "awaiting_reply"`, response columns blank, `supplier_slug` is one of the 8.
  If none, end the run without writing.
- Answer each from the `SupplierLedger`, set the response columns + `status = "replied"`,
  dedup on `processed_corr_ids` (one response per `corr_id`; concede a stall exactly once).

### KEY DESIGN DECISION — gated items in an unattended run

> **An unattended run must never auto-approve work that the tier model says requires a
> human.** When a Tier-2/Tier-3 (or ambiguous Tier-4 Question) gate would block and **no
> human is present** to answer it, the agent applies **only what is auto-allowed** —
> sub-threshold, routine, reversible actions (Tier-5; e.g. normalizing statuses,
> appending `Draft — agent-detected` rows below €1,000, banking a clearly-corroborated
> credit) — and **leaves every gated item queued for the next attended run** rather than
> approving it itself.

Concretely, in an unattended recon run:

- **Apply automatically:** Tier-5 routine writes, and agent-detected claims **below
  €1,000** written as `Draft — agent-detected`.
- **Leave queued (do NOT act):** closing a human-owned claim row (Tier-2), logging a new
  claim **above €1,000** (Tier-3, e.g. the rebate €1,548 / promo €2,000 cases), and any
  ambiguous damaged-goods / `NO_GRN` / unprovable item (Tier-4 Question). Mark these with
  a status such as `Pending human review` (or leave the existing `Draft`/`awaiting_reply`
  state intact) and **report them** so the next attended run — where `duvo runs respond
  --approve` is available — clears them.

> ⚠ **Flag:** the unattended loop is intentionally **partial**. It advances the routine,
> sub-threshold majority of the work and **stops at every human gate** — it does not
> substitute its own approval for a human's. Closing the high-value and ambiguous items
> still requires an attended run with a real approver.

---

## Quick reference — what to run for the recommended path

```bash
# RECOMMENDED: Option A, two schedules (offset)
duvo agents schedules create e6e3b6e5-0037-4f88-a774-18abaa52dc0b \
  --frequency every_5_minutes --timezone Europe/Amsterdam

duvo agents schedules create eb165d7e-c8aa-43d3-84ff-055fbcc961e3 \
  --frequency custom --cron "2,7,12,17,22,27,32,37,42,47,52,57 * * * *" \
  --timezone Europe/Amsterdam

# Pause when idle
duvo agents schedules list   <agent-id>
duvo agents schedules update <agent-id> <schedule-id> --disable
# Remove
duvo agents schedules delete <agent-id> <schedule-id> -y
```
