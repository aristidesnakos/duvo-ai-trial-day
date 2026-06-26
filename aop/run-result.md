# Duvo Agent Run Result — Supplier Reconciliation & Claims Co-Pilot

> **⚠️ SUPERSEDED — this records an early, failed approach, kept for the honest debugging trail.**
> This run used the knowledge-base-file upload (`config.data.files`), which **did not mount the data
> in the run sandbox**, so the agent couldn't read the CSVs and produced no reconciliation. The fix
> was to move the data into a **Google Sheets** workbook. The working **two-agent closed loop** then
> recovered **€5,536 of €6,203 owed (0% → 89.2%)** — see [`DEPLOYMENT.md`](./DEPLOYMENT.md) (run
> record) and [`../PROOF-PACK.md`](../PROOF-PACK.md). Read those, not the "€0 / not produced" below.

## Run metadata

| Field | Value |
|---|---|
| Run ID | `f0b1829c-4cf7-4500-84fc-d17974d020de` |
| Agent ID | `eb165d7e-c8aa-43d3-84ff-055fbcc961e3` |
| Build ID | `27f142e4-9882-4f10-8596-e93d72f420c2` (rebuild with 6 files claimed attached) |
| Sandbox ID | `iatodgj5ugjq50gbs5rs2` |
| Status | **`completed`** (terminal) |
| Created | 2026-06-26T11:00:04.324Z |
| Started | 2026-06-26T11:00:14.448Z |
| Completed | 2026-06-26T11:02:17.109Z |
| Duration | ~2 min |

> Polled `duvo runs get` at ~15s intervals; run went `running` → `completed` at poll 7 (~13:02 local). No human-in-the-loop pause this time.

## Outcome: the agent still could NOT read the input files — no Recovery Reconciliation Report produced

This run included an explicit operator instruction (build 27f142e4) telling the agent the data was attached and to read it directly:

> "Your input data is ATTACHED to this build as knowledge-base files in your workspace: purchase_orders.csv, good_receipts.csv, invoices.csv, supplier_contracts.csv, supplier_claims_tracker.csv, and email_thread.pdf. Read these files DIRECTLY … do NOT ask for Google Sheet IDs or use sample data … Scope: PERIOD = Q1 2026 … exclude CLM-007 / INV-2099. IDENTIFY-ONLY run … OUTPUT the full Recovery Reconciliation Report … as text in your final message."

### Did the agent read the attached files THIS time? NO.

The six files were **not present anywhere in the sandbox filesystem**. The agent searched exhaustively and could not find them:

- `Glob /workspace/**/*.{csv,pdf}` → "No files found"
- `find /workspace -type f` → only `/workspace/.claude/learnings/.placeholder`
- `find / -name "purchase_orders.csv"` and broad `*.csv` scan → only unrelated `node_modules` license CSVs
- `find / -name "purchase_orders*" -o -name "supplier_contracts*" -o -name "invoices*" -o -name "good_r*"` → no output
- Checked `/app/`, `/data/`, `/files/`, `/input/` → none contained the data
- Full-filesystem `*.csv`/`*.pdf` scan → only the `google-sheets` skill's bundled example data (`customers/data/Clients_*.csv`, `Deliveries_data.csv`)

**Conclusion: the rebuild did NOT actually deliver the 6 files into the agent's sandbox.** The data-access blocker is unresolved. The coordinator's claim that "the data-access issue is fixed" is not borne out by what the agent observed at runtime.

### Agent's final message (verbatim)

> The six input files are not present anywhere in the workspace filesystem — I've searched all accessible paths. Before I can run the reconciliation I need the actual data.
>
> Could you provide the files? Options:
> 1. **Upload them directly** into this conversation (paste CSV content or upload the PDF)
> 2. **Drop them into `/workspace/`** if you have filesystem access to the container, then re-run
>
> The AOP's worked examples (Meadowvale unit-conversion trap, Riverside near-miss, CLM-007 exclusion) are instructional references, not the dataset itself — so I can't use them as a substitute for the real files, per your "no sample data" instruction.
>
> Once the files are accessible I'll proceed immediately through all nine reconciliation steps and deliver the full report.

Note: the agent behaved correctly and safely — it did **not** hallucinate numbers from the AOP's illustrative examples, and explicitly refused to substitute them for the real dataset. The failure is environmental (files not mounted), not a reasoning error.

### Message timeline (22 messages)

1. `user` — AOP/purpose prompt (9,830 chars).
2. `user` — explicit "files are attached, read directly, identify-only, output report as text" instruction (804 chars).
3. `session_started`.
4. `tool_call mcp__agentic-memory__memory (list)` → "No memory files found."
5. `tool_call Glob /workspace/**/*.{csv,pdf}` → "No files found."
6. `tool_call Bash find /workspace` → only `.placeholder`.
7–9. `tool_call Bash` filesystem-wide searches for the named CSVs → nothing relevant.
10. `assistant` — "The source files aren't in the filesystem — let me do one more thorough scan before concluding."
11. `tool_call Bash` final broad scan + `/app /data /files /input` checks → only google-sheets skill example data.
12. `assistant` — final message: files not present, requests upload, declines to use AOP examples as data.
13. `session_completed`.

## Validation vs. ground truth

The agent produced **no numbers**, so item-by-item comparison is impossible. Every oracle item is **MISSED (not attempted)** due to the data-access failure. Critically, **no values were hallucinated** — the agent did not fabricate figures from the AOP examples.

| Expected item | Oracle value | Agent result |
|---|---|---|
| € owed total | €6,203 | Not produced (no data access) |
| € recovered | €0 | Not produced |
| Recovery rate | 0% | Not produced |
| Missed: Riverside 120 damaged cases | €1,080 | Not attempted |
| Missed: Northgate volume rebate | €1,548 | Not attempted |
| Missed: Sunrise promo | €2,000 | Not attempted |
| Missed total | €4,628 | Not attempted |
| Logged-correct: Greenfield short (CLM-001) | €375 | Not attempted |
| Logged-correct: Sunrise overcharge (CLM-002) | €750 | Not attempted |
| Logged-correct: Prime Cuts chicken (CLM-004) | €450 | Not attempted |
| Over-claim/duplicate: CLM-006 dup of CLM-004 | €450 | Not attempted |
| False/close: CLM-003 Meadowvale unit/case nets to €9,000 → NO claim | — | Not attempted (trap not reached) |
| False/close: CLM-005 Sweet Treats no GRN-3007 → unprovable | — | Not attempted (trap not reached) |
| False/close: CLM-008 Greenfield tomato INV=PO → no claim | — | Not attempted (trap not reached) |

**Hallucinated / wrong numbers:** None. The agent correctly identified the AOP's worked examples (Meadowvale, Riverside, CLM-007) as instructional references and refused to use them as data.

**Overall verdict: DIVERGED — incomplete (data-access failure persists).** Despite build 27f142e4 and an explicit "files are attached, read them directly" instruction, the 6 knowledge-base files were still not present in the agent's sandbox. The run reached `completed` status, but with no reconciliation output. The fix did not take effect at the sandbox level. None of the three oracle traps (Meadowvale unit/case, Sweet Treats no-GRN, Prime Cuts duplicate) were exercised. The agent's behavior was correct and safe given a broken environment; the blocker is on the provisioning/file-mount side, not the agent's reasoning.
