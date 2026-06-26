# Live Demo Script — Supplier-Claims Reconciliation Agent

> ~3 minutes · deterministic · every command below was run live and the output confirmed.

## Pre-flight checklist

| Item | Action | Confirmed value |
|---|---|---|
| **Reset demo state** | `rm -f out/approvals.json out/submissions.json` | leaves only `run-Q1-2026-4f8c1843.*.json` |
| **Nothing pre-approved** | after reset, `--submit` says *"No approved claims to submit"* | so the "blocked" beat fires |
| **Working dir** | `cd ~/Documents/duvo-ai-trial-day` | run-as-module needs repo root |
| **Terminal font** | ~18–20pt, window ≥ 80 cols | report uses 72-char banners |
| **run_id (memorize)** | `run-Q1-2026-4f8c1843` | deterministic |
| **submission_id** | `SUB-1230272` (Northgate rebate) | deterministic |

## The sequence

| # | Type | Point at | Say (one line) |
|---|---|---|---|
| **0** | `python3 tests/test_acceptance.py` | `13/13 acceptance criteria passed` | "Before a single number — proof the logic is correct: 13 named cases from the email thread, all green." |
| **1** | `python3 -m agent.run` | `€ owed … €6,203.00 · € recovered … €0.00 · RECOVERY RATE … 0%` | "The question Mark asked and Finance couldn't answer: owed €6,203, recovered zero, 0% recovery." |
| **2** | *(scroll to)* `MISSED (3)` | `Riverside — damage — €1,080` · `Northgate — rebate — €1,548` | "€4,628 was never even logged — damaged stock fully invoiced, a rebate threshold nobody checked." |
| **3 (HERO)** | `python3 -c "from agent.matcher import normalize_uom; print(normalize_uom(500,18.00,'case',12))"` then point at the `NOT-CLAIMABLE` Meadowvale line | one-liner prints `500 case × 12 units = 6000 units @ €1.50/unit`; report shows Meadowvale at **€0** | "The dairy claim Jenny gave up on. 500 cases at €18 = 6,000 units at €1.50 — ties to the invoice exactly. Honest answer: no claim. Stop chasing it." |
| **4** | *(scroll to)* `OVER-CLAIMED (1)` | `Prime Cuts — price_gap — €450 [CLM-004] DUPLICATE_OF=CLM-006` | "Catches a real €450 overcharge logged twice under two owners — so we don't pay, or chase, it twice." |
| **5a (GATE)** | `python3 -m agent.run --submit` | `No approved claims to submit…` | "The only thing that writes. Submit with no approval — it refuses." |
| **5b** | `python3 -m agent.run --approve "SUP-001:Q1-2026\|rebate" --approver "Mark Bryant"` | `APPROVED … by Mark Bryant @ 2026-04-08` | "A human approves one specific claim — Mark, the Northgate rebate." |
| **5c** | `python3 -m agent.run --submit` | `SUBMITTED  SUP-001:Q1-2026\|rebate  €1,548.00  -> SUB-1230272` | "Now it submits — that one claim, capped to the €1,548 the math supports." |
| **5d** | `python3 -m agent.run --submit` | `ALREADY_SUBMITTED … SUB-1230272` | "Run it again — idempotent. Same ID, no double-write. Blast radius is one approved claim." |
| **6** | `cat out/submissions.json` | record carries `run_id`, `approved_by`, `submission_id` | "Every run leaves an auditable record, joinable by run_id — who approved what, end to end." |

## ⚠ Three things to know before you demo

1. **Step 3 — the UoM math is NOT in the report.** The win is the *absence* of a claim, so there's no €9,000 line to point at. Show it via the `normalize_uom` one-liner (or the test name `test_meadowvale_uom_negative_control`). Don't promise a visible dairy line.
2. **Step 5a prints `No approved claims to submit`, not `BLOCKED_NEEDS_APPROVAL`.** That literal status is the function-level guard in `submit.py`; the CLI never reaches it with zero approvals. Say "it refuses," not "watch it say BLOCKED."
3. **Trust the live output (13/13).** Docs are synced, but if anything on screen still says 11, the runner is ground truth.

## Fallback (if the terminal fails)

- Pre-capture all commands to screenshots in step order; numbers are deterministic so a captured run is byte-identical (`run_id` and `SUB-1230272` never change).
- One safety-net slide: the full `python3 -m agent.run` report covers Steps 1–4.
- The gate story in one image: `No approved…` → `APPROVED` → `SUBMITTED … SUB-1230272` → `ALREADY_SUBMITTED`.
- If Python itself is down: open `out/run-Q1-2026-4f8c1843.audit.json` + `submissions.json` in an editor for Step 6.
