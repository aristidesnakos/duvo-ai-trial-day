# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is a trial-day exercise repository. It currently contains **only data** — no application code, build system, dependencies, or tests exist yet. Any solution code, scripts, or tooling is expected to be added as part of the exercise.

The dataset describes a **supplier procurement & invoice reconciliation** scenario for a food/hospitality business. The core task implied by the data is to reconcile what was ordered vs. received vs. invoiced, surface discrepancies (short deliveries, price mismatches, missing credits), and tie them to contract terms and the claims being tracked.

## Data model

All files live in `data/`. They join on a small set of shared keys: `po_id`, `supplier_id`, `sku`, and invoice references (`invoice_id` / `invoice_ref`).

- **`purchase_orders.csv`** — what was ordered. Keys: `po_id`, `supplier_id`, `sku`. Has `qty_ordered`, `unit_price_eur`, `po_total_eur`.
- **`good_receipts.csv`** (GRN = Goods Receipt Note) — what physically arrived. Keys: `grn_id`, `po_id`, `supplier_id`, `sku`. Has `qty_received` and a `condition` field (`OK` / `Short` / etc.) plus free-text `notes` documenting discrepancies.
- **`invoices.csv`** — what the supplier billed. Keys: `invoice_id`, `po_id`, `supplier_id`, `sku`. Has `qty_invoiced`, `unit_price_eur`, `invoice_total_eur`.
- **`supplier_contracts.csv`** — agreed terms per `supplier_id`: `payment_terms_days`, volume-rebate thresholds/percentages (`volume_bonus_threshold_eur_qtr`, `volume_bonus_pct`), promo funding, and free-text `notes` describing how credits/rebates apply.
- **`supplier_claims_tracker.csv`** — manually-logged disputes (`claim_id`) referencing `invoice_ref` / `po_ref`, with `claim_type`, `claim_amount_eur`, `status`, and `owner`. This is the human-maintained ground truth of what's already been caught.
- **`email_thread.pdf`** — narrative context for the scenario (2 pages). Supplementary background, not structured data.

### Reconciliation chain

The three-way match is the heart of the analysis: **PO → GRN → Invoice**, joined on `po_id` + `sku`.
- Quantity discrepancies: `qty_ordered` vs `qty_received` vs `qty_invoiced` (e.g. billed for ordered qty when delivery was short).
- Price discrepancies: invoice `unit_price_eur` vs PO `unit_price_eur` (and vs contract terms).
- Contract overlays: volume rebates, promo funding, and credit eligibility from `supplier_contracts.csv` notes determine what should be claimed back.
- The `supplier_claims_tracker.csv` is the existing partial record — findings should be cross-checked against it (which discrepancies are already logged vs missed).

## Data quirks to watch for

- **`status` values are inconsistent** in `supplier_claims_tracker.csv` (e.g. `Open` vs `in progress` — mixed casing/wording). Normalize before grouping.
- Important details are buried in **free-text `notes`** fields (GRN shortage explanations, contract credit rules) — these are not machine-structured and must be read, not just aggregated.
- All monetary amounts are in EUR; dates are `YYYY-MM-DD`.
- Row counts are small (~20 rows per CSV) — this is a hand-checkable dataset, so favor correctness and clear discrepancy explanations over scale/performance.

## Working in this repo

There are no commands to build, lint, or test yet — establish the language/tooling with the user before assuming one. When adding analysis code, keep `data/` as read-only inputs.
