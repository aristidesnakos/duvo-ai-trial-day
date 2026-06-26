# Supplier-Claims Reconciliation Agent

Deterministic, dependency-free Python agent for Daily Basket Finance Ops. It
**derives** the supplier claims that *should* exist from ERP exports + contracts,
**reconciles** them against the existing tracker, and answers the Finance
Director's question — *how much are we recovering vs. how much is owed?* — with a
human-gated, auditable claim pack behind every euro.

Source of truth for behaviour: [`../SPEC.md`](../SPEC.md).

## Run it

```bash
python3 -m agent.run                 # full reconciliation report (read-only)
python3 -m agent.run --json          # machine-readable roll-up + claim packs
python3 tests/test_acceptance.py     # 18/18 acceptance criteria (no deps)
```

The one write (`submit_claim`) is gated on a recorded human approval:

```bash
python3 -m agent.run --approve "SUP-001:Q1-2026|rebate" --approver "Mark Bryant"
python3 -m agent.run --submit        # fires only for approved claims; idempotent
```

Requires Python 3.7+. No third-party packages. `data/` is read-only input; all
output goes to `out/` (`<run_id>.trace.json`, `<run_id>.audit.json`,
`approvals.json`, `submissions.json`).

## What it computes (Q1 2026, live)

| Answer to Mark | € |
|---|--:|
| Owed (justified, de-duplicated) | **6,203** |
| Recovered to date | **0** |
| Recovery rate | **0%** |
| Missed (never logged) | **4,628** |
| Over-claim risk (logged twice) | **450** |
| Annualized run-rate (×4) | **24,812** |

## How it's safe (constitution mapping)

- **Smallest safe surface** — 7 tools; exactly **one write** (`submit_claim`).
- **Transparent over clever** — every € is re-checkable line-math, no inference on the trust-critical path.
- **Bounded blast radius** — the write is single-claim, capped to the derived €, idempotent on `(po_id|claim_type)`.
- **Human-in-the-loop** — `submit_claim` returns `BLOCKED_NEEDS_APPROVAL` until an approval is persisted.
- **Observable** — deterministic `run_id`; engineer trace + business audit, joinable by run_id; no secrets logged.
- **No fabrication** — missing GRN → not-claimable; UoM that reconciles → €0, no claim.

## Architecture & next step

Today the **autonomous CLI runner** (`run.py`) orchestrates the deterministic
engine end-to-end. The engine is structured as a clean tool surface
(`loader`/`matcher`/`entitlements`/`reconcile`/`claimpack`/`submit`), so the
documented next step is to expose it as an **MCP server** and drive it with a
**Claude Agent SDK** agent — the LLM sits on top of the deterministic tools and
never touches the arithmetic. Then: schedule recurring runs, widen UoM/contract
coverage, and wire the real claim-submission endpoint behind the existing gate.

## Module map

| Module | Responsibility |
|---|---|
| `loader.py` | load + validate the 5 CSVs, scope to period, split out the Q4 row |
| `config.py` | period bounds, status normalization, UoM/date parsing helpers |
| `matcher.py` | `normalize_uom` + `three_way_match` (short / damage / price-gap) |
| `entitlements.py` | volume rebate (only if threshold crossed) + promo funding |
| `reconcile.py` | bucketing, duplicate detection, orphan-tracker-row scan |
| `claimpack.py` | per-claim pack + Mark's-question roll-up |
| `submit.py` | the only write — human-gated, idempotent, capped, stubbed |
| `observability.py` | deterministic run_id + trace/audit records |
| `run.py` | autonomous end-to-end runner / CLI |
