# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

FDE trial-day deliverable: a **supplier-claims reconciliation agent** for "Daily Basket"
(a food/hospitality business). It answers the Finance Director's question — *how much do
suppliers owe us vs. how much have we recovered?* — that the manual, single-owner
spreadsheet (`supplier_claims_tracker.csv`) could not.

The thesis (`README.md`, `PROJECT-BRIEF.md`): **don't automate the tracker — replace it as
the source of truth.** The agent *derives* the claims that *should* exist from ERP exports
(PO ↔ Goods Receipt ↔ Invoice) + contracts, then uses the tracker only as a
**reconciliation target**, bucketing every claim into **missed / logged-correct /
over-claimed / not-claimable**. Behind every euro is re-checkable line-math, never inference.

The headline numbers (€6,203 owed, €4,628 missed, 0% recovered, etc.) are **asserted in the
test suite** — they are contracts, not prose. If you change the engine and a number moves,
either the change is wrong or the docs that quote it must be updated in lockstep.

## Commands

```bash
python3 -m agent.run                 # full reconciliation report (read-only)
python3 -m agent.run --json          # machine-readable roll-up + claim packs
python3 tests/test_acceptance.py     # zero-dependency acceptance runner (must stay green)
python3 -m pytest tests/ -q          # same tests, if pytest is installed

# The ONLY write — human-gated, idempotent on (po_id|claim_type), value-capped, stubbed:
python3 -m agent.run --approve "SUP-001:Q1-2026|rebate" --approver "Mark Bryant"
python3 -m agent.run --submit        # fires only for already-approved claims
```

Python 3.7+, **stdlib only, no dependencies**. Deterministic. `data/` is read-only input;
all output goes to `out/` (`<run_id>.trace.json` engineer trace + `<run_id>.audit.json`
business audit, joinable by `run_id`; plus `approvals.json` / `submissions.json`).

## Engine architecture (`agent/`)

`run.py` orchestrates a deterministic pipeline; each module is a clean tool surface (the
documented next step is to expose these as an MCP server driven by a Claude Agent SDK agent
that sits *on top of* the arithmetic, never inside it). Flow:

`loader` (load+validate 5 CSVs, scope to period, split out the Q4 row) →
`matcher` (`normalize_uom` + `three_way_match`: short / damage / price-gap) +
`entitlements` (volume rebate only if threshold crossed; promo funding) →
`reconcile` (bucketing, duplicate detection, orphan-tracker-row scan) →
`claimpack` (per-claim pack + Mark's-question roll-up) →
`submit` (the one write — gated, idempotent, capped, stubbed) ·
`observability` (deterministic `run_id`, trace/audit records).

`config.py` holds all period bounds and shared parsing (status normalization, date formats,
UoM extraction) — no magic numbers in the logic. `models.py` has the dataclasses + `to_jsonable`.
See `agent/README.md` for the per-module responsibility table and `SPEC.md` for the behavioral
source of truth.

### Three traps the engine must keep getting right (these are encoded as tests)

1. **UoM normalization** — Meadowvale Dairy (SUP-003) quotes per case (12 units/case). A naive
   compare reports a phantom gap; normalized, INV-2003 reconciles *exactly* to PO-1003 → **€0,
   no claim**. The pack size is read from the contract note, not hard-coded.
2. **No evidence, no claim** — Sweet Treats has no goods-receipt row, so the shortage is
   unprovable → routed to a human, not invented.
3. **Duplicate detection** — Prime Cuts' real €450 overcharge was logged twice (CLM-004 +
   CLM-006, different owners/spelling) → flagged so Daily Basket doesn't double-chase or double-pay.

## Data model (`data/` — read-only inputs)

Files join on `po_id`, `supplier_id`, `sku`, and invoice refs (`invoice_id` / `invoice_ref`).

- **`purchase_orders.csv`** — ordered: `qty_ordered`, `unit_price_eur`, `po_total_eur`.
- **`good_receipts.csv`** (GRN) — physically arrived: `qty_received`, `condition` (`OK`/`Short`/…),
  free-text `notes` documenting discrepancies.
- **`invoices.csv`** — billed: `qty_invoiced`, `unit_price_eur`, `invoice_total_eur`.
- **`supplier_contracts.csv`** — per-supplier terms: `payment_terms_days`, volume-rebate
  threshold/pct, promo funding, free-text `notes` describing how credits/rebates apply.
- **`supplier_claims_tracker.csv`** — manually-logged disputes (`claim_id`, `claim_type`,
  `claim_amount_eur`, `status`, `owner`). The human ground truth of what's *already* been caught —
  the reconciliation target, not the source.
- **`email_thread.pdf`** — narrative scenario context (2 pages), not structured data.

**The three-way match (PO → GRN → Invoice on `po_id`+`sku`) is the heart:** quantity
discrepancies (ordered vs received vs invoiced), price discrepancies (invoice vs PO unit price),
and contract overlays (rebates/promo/credits) determine what should be claimed back.

### Data quirks the engine handles (don't regress these)

- **Inconsistent `status` values** in the tracker (`Open` vs `in progress`, mixed casing) →
  normalized to a 3-value vocabulary in `config.normalize_status`.
- **Mixed date formats** — most are `YYYY-MM-DD`, but CLM-003 uses `DD/MM/YYYY`; `config.parse_date`
  handles both.
- **Critical detail lives in free-text `notes`** (GRN shortage amounts, contract credit rules) —
  parsed *anchored to context* (`damage_qty_from_note`), never a naive first-integer grab.
- **Period discipline** — only `Q1-2026` (2026-01-01..03-31) is in scope; the loader splits out
  the out-of-period (Q4) tracker row. All amounts EUR.
- Row counts are small (~20/CSV) — hand-checkable; favor correctness and clear discrepancy
  explanations over scale.

## Guardrails (enforced by hooks in `.claude/`)

- **`data/` is read-only ground truth.** A PreToolUse hook (`protect-data.sh`) **denies** any
  Edit/Write under `data/` (canonicalizes paths so `../data/` can't sneak past). Every claim
  number derives from those inputs — if a source value looks genuinely wrong, raise it with the
  user; don't edit the input.
- **Acceptance tests gate engine changes.** A Stop hook (`run-acceptance-tests.sh`) hashes
  `agent/*.py` + `tests/*.py`; on change it runs `tests/test_acceptance.py` and **blocks** if it
  fails (so engine edits can't silently break the deliverable numbers). Green → silent.
- Operating principles: smallest safe surface (one write), transparent over clever, bounded
  blast radius, human-in-the-loop, observable, no fabrication.

## Deliverables & companion material (mostly docs)

`SPEC.md` is the behavioral source of truth. `PROJECT-BRIEF.md` / `README.md` frame the outcome;
`PROOF-PACK.md` / `CASE-STUDY.md` quantify before/after; `TALK-TRACK.md` + `presentation/index.html`
are the pitch. `aop/` holds the Duvo-platform-native agent design (AOP + deployment record + supplier
simulator). `prep/` has discovery/strategy/the reusable recovery-pattern asset. **Numbers quoted in
any of these must match the engine output / tests** — update them together.
