# HANDOFF — Daily Basket FDE Trial prep

> Read this first to resume. Working dir: `~/fde-trial/`. Today (in-scenario) = early April 2026; data period = Q1 2026.

## The task

Preparing for an **FDE (Forward-Deployed Engineer) trial day at Duvo**. Scenario: embed with **Daily Basket** (online grocer, ~€180M GMV) **Finance Ops** and ship an agent against their **supplier-claims** process. On the day: discovery → Project Brief with €-success → build agent on Duvo sandbox → proof pack + reusable asset + 5-bullet case study → present to co-founder + hiring manager at 17:00. Brief says **no need to build beforehand**; goal of this prep is to walk in with the numbers and a brief.

**Sources:**
- Scenario brief + Data README: Notion (pasted into the original thread; private).
- Methodology: `aristidesnakos/fde-field-kit` (GitHub), cloned **read-only** to `~/fde-trial/.reference/fde-field-kit` — NOT a remote/submodule (user wants their eventual project repo to keep a single remote).

## The core thesis (our differentiator)

**Don't automate the spreadsheet — replace it as the source of truth.** The tracker is the failure mode (single-owner Jenny; errors; money never logged). Derive claims from the **ERP exports + contracts** via a **three-way match (PO ↔ Goods Receipt ↔ Invoice)** + **contract entitlements (rebates/promo)**, then use the tracker only as a **reconciliation target** → bucket into **missed / logged-correct / over-claimed**. Headline outcome = **recoverable € (esp. rebates)** + answering Mark's question.

**Mark's (Finance Director) actual success metric**, from the email: *"how much are we recovering vs. how much is owed?"* — Finance can't answer it today. Frame success as **€ owed + recovery rate**, with the un-claimed money as the upside.

## Stakeholders

- **Paula Hart** — Finance Ops Lead (sponsor).
- **Jenny Walsh** — operator; runs the spreadsheet; on leave (key-person risk).
- **Mark Bryant** — Finance Director; economic buyer; cares about "numbers that move."

## Data room (6 files; all Q1 2026)

`purchase_orders.csv`, `goods_receipts.csv`, `invoices.csv` (the three-way match; `po_id` joins all three) · `supplier_contracts.csv` (prices, rebate thresholds, promo; `supplier_id` joins) · `supplier_claims_tracker.csv` (today's sheet = reconcile target; has one Q4 row to exclude) · `email_thread.pdf`.

**Known data trap:** SUP-003 (Meadowvale Dairy) quotes **per case = 12 units** — normalize UoM before any price/qty comparison. Assume other pack-size traps exist.

## email_thread.pdf — already mined (see `prep/email-thread-findings.md`)

Named cases = a built-in test set:
- **Meadowvale Dairy (SUP-003)** — Jenny "couldn't get numbers to line up," gave up → the UoM trap → a **missed** claim → **demo hero moment**.
- **Greenfield Farm** — short delivery tomatoes 150kg, open → logged-correct.
- **Sunrise Bakery** — €750 rolls overcharge → logged-correct.
- **Prime Cuts Butchers** — "feeling it's in there twice" → **duplicate / over-claimed**.
- **Sweet Treats** — no paperwork our side → not substantiable.
- **Rebate suppliers** (flour/drinks/packaging/dairy) — Jenny never checks thresholds; "where the real money is."

## STATUS / next action

- ✅ Field kit digested (playbook, principles, SPEC template, 3 skills).
- ✅ Prep artifacts written to `~/fde-trial/prep/`: `strategy.md`, `discovery-questions.md`, `PROJECT-BRIEF.draft.md`, `email-thread-findings.md`.
- ✅ `email_thread.pdf` extracted (copied to `data/`; pypdf installed for extraction).
- ⏳ **BLOCKED:** the **5 CSVs are not yet on disk** (only the PDF downloaded). User to drop them in `~/fde-trial/data/`.
- ▶️ **NEXT (on CSV arrival):** schema-sniff → three-way match w/ UoM normalization → contract entitlements → reconcile vs tracker (exclude Q4 row) → validate against the 5 named cases → output **€ owed / recovery rate / missed-money** + data-trap list. Write analysis to `prep/`.

## Field-kit operating loop (apply on the day)

`scope-a-workflow → SPEC.md → spec-driven-build → fde-presentation`, on the first-90-minutes timebox. Guardrails: smallest safe surface · API before screen · bounded blast radius · idempotent writes · human gate on the claim-submit write · transparent arithmetic · trace+audit · mock-first deterministic demo.
