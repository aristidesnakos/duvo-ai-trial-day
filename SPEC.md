# SPEC — Supplier-Claims Reconciliation Agent (Daily Basket)

> Source of truth for the build. Filled from prep (strategy / brief / email-thread).
> `[confirm on day]` = depends on discovery or the not-yet-seen CSV data.

## 1. Problem & context

Daily Basket (online grocer, ~€180M GMV) is owed money by suppliers — short/damaged deliveries, prices billed above contract, and earned-but-unclaimed volume rebates & promo funding — but the claims process lives in one analyst's (Jenny's) spreadsheet. It is reactive ("I only chase a claim when a supplier emails or something looks obviously wrong"), single-owner (when Jenny was out sick in Feb, nobody touched the sheet for two weeks and credit windows nearly closed), and structurally blind to money that was *never logged at all*. Finance Director Mark's actual question — *"how much are we recovering vs. how much is owed?"* — currently has **no answer** because nobody can compute the denominator. This agent **independently derives the claims that should exist** from the ERP exports + contracts, **reconciles them against the tracker**, and surfaces recoverable € with an auditable, human-gated claim pack — recovering the abandoned long tail (esp. the dairy UoM claim Jenny gave up on and the rebate thresholds she "never gets to check").

## 2. User & decision

- **User:** Finance Ops — operator **Jenny Walsh** (runs claims), sponsor **Paula Hart** (Finance Ops Lead), economic buyer **Mark Bryant** (Finance Director). The agent must run end-to-end **without Jenny**.
- **Decision/action:** For each `(po_id, claim_type)` or contract entitlement, decide: is there a **justified, evidence-backed claim**, and if so, **submit it** (human-approved) — bucketed as **missed / logged-correct / over-claimed / not-claimable**.
- **Trigger:** Human request / batch run over a period (Q1 2026). No live event stream in MVP; designed to run on a schedule later.

## 3. Systems of record & auth

| System | Holds | API? | Auth model | Access today? |
|---|---|---|---|---|
| `purchase_orders.csv` (ERP) | agreed qty & price per PO | CSV export | n/a (file) | live — on disk, validated by loader |
| `good_receipts.csv` (ERP/GRN) | received qty + condition (damage code) | CSV export | n/a (file) | live — on disk, validated by loader |
| `invoices.csv` (AP / supplier portal) | billed qty & price | CSV export | n/a (file) | live — on disk, validated by loader |
| `supplier_contracts.csv` | contract prices, UoM/pack size, rebate thresholds, promo funding terms | CSV export | n/a (file) | live — on disk, validated by loader |
| `supplier_claims_tracker.csv` | today's spreadsheet — **reconcile target, not source of truth** | CSV export | n/a (file) | live — on disk, validated by loader |
| `email_thread.pdf` | how claims are triggered/handed off; human-gate context | PDF (present) | n/a (file) | available |
| Claim submission target (supplier credit-note / dispute) | the only write | `[confirm on day]` — assume stubbed | `[confirm on day]` | **stubbed (mock)** for demo |

**System of record = ERP exports + contracts (READ).** Tracker = reconcile target (READ). The five CSVs are present and the loader validates columns / fails loud on mismatch; on a real engagement, re-confirm schemas against the customer's own exports.

## 4. Scope

- **In scope (smallest safe slice, end-to-end):**
  1. **Three-way match** per `po_id`: PO ↔ GR ↔ Invoice → flag short delivery, damage, price-above-contract. **UoM normalization first** (SUP-003 dairy = 12 units/case; assume other UoM traps exist until disproven).
  2. **Contract entitlements** per supplier: earned **volume rebate** (Q1 volume vs threshold) and **promo funding** owed.
  3. **Reconcile** derived claims vs tracker → four buckets: **missed / logged-correct / over-claimed / not-claimable**.
  4. **Claim pack** per justified claim: supplier, PO, basis, € amount, the three source rows as evidence, confidence.
  5. **Submit claim** — single, human-gated, idempotent write (stubbed for demo).
- **Out of scope / omitted capabilities (deliberate):**
  - **No auto-submission** without human approval; **no supplier dispute handling**; **no cash collection / payment posting**. (`[confirm boundary with Paula on day]`)
  - **No write-back to the tracker or ERP** beyond the single claim-submit. Tracker stays read.
  - **No opaque ML inference** — claims are transparent line-math only.
  - **No fabricated claims** where evidence is insufficient (e.g. missing GR) — these are returned as *not-claimable*, never raised.
  - **Period-bounded to Q1 2026**; the single Q4 row is excluded from Q1 totals.

## 5. Tool surface

Fewest tools that do the job. All read tools are deterministic over the provided CSVs; one write.

| Tool | Purpose | Inputs (typed) | Output (decision evidence) | MCP/CU | R/W |
|---|---|---|---|---|---|
| `load_period_data` | Load + validate the 5 CSVs for a period | `period: str (e.g. "Q1-2026")` | typed record sets (POs, GRs, invoices, contracts, tracker rows); rows outside period flagged/excluded | local (file) | R |
| `normalize_uom` | Convert all qty to a common unit before any € comparison | `line: {supplier_id, qty, uom}`, `contract_pack_size` | `{qty_base_units, uom_applied, conversion_note}` | local | R |
| `three_way_match` | Match PO↔GR↔Invoice per `po_id`, detect discrepancies | `po_id` | `{po_id, short_delivery_qty, damaged_qty, price_gap_eur, billed_vs_contract, evidence_rows}` | local | R |
| `compute_entitlements` | Per-supplier rebate + promo funding owed for period | `supplier_id, period` | `{supplier_id, q1_volume, threshold, rebate_eur, promo_eur, basis}` | local | R |
| `reconcile_against_tracker` | Compare derived claims to tracker; assign bucket | `derived_claims[]`, `tracker_rows[]` | `{claim, bucket: missed\|logged-correct\|over-claimed\|not-claimable, tracker_match, delta_eur, duplicate_flag}` | local | R |
| `build_claim_pack` | Assemble human-readable, auditable claim | `claim` | `{supplier, po_id, claim_type, eur_amount, line_math, evidence_rows[3], confidence, bucket}` | local | R |
| `submit_claim` | **The only write.** Raise one claim, human-gated, idempotent | `claim_pack`, `idempotency_key=(po_id, claim_type)` | `{submission_id, status, idempotency_key, run_id}` | MCP/stub | **W** |

## 6. Data shapes

Exact columns `[confirm on day]` against real CSVs. Target internal shapes:

**DerivedClaim**
```
{ po_id: str, supplier_id: str, claim_type: "short_delivery"|"damage"|"price_gap"|"rebate"|"promo",
  eur_amount: number, line_math: str,                  # human-readable arithmetic
  evidence: { po_row, gr_row, invoice_row | contract_row }, uom_normalized: bool,
  confidence: "high"|"medium"|"low", period: "Q1-2026" }
```

**ReconciledClaim** (= DerivedClaim + )
```
{ bucket: "missed"|"logged-correct"|"over-claimed"|"not-claimable",
  tracker_row_id: str|null, tracker_status: "open"|"paid"|"disputed"|null,  # [confirm statuses]
  delta_vs_tracker_eur: number, duplicate_of: str|null,
  claimable: bool, not_claimable_reason: str|null }
```

**ClaimPack** (submit input) = ReconciledClaim + `idempotency_key=(po_id, claim_type)` + `approved_by`, `approved_at`.

**Period roll-up (Mark's answer)**
```
{ eur_owed_total, eur_recovered_to_date, recovery_rate = recovered/owed,
  by_bucket: { missed_eur, logged_correct_eur, over_claimed_eur },
  annualized_run_rate = q1 * 4 (seasonality caveat) }
```

## 7. Guardrails

- **Blast radius:** the only write is `submit_claim` — single-entity (one `po_id`/claim), single-action, **quantity-capped to the derived € amount**, no batch auto-submit.
- **Idempotency key:** `(po_id, claim_type)` (entitlements: `(supplier_id, claim_type, period)`). Re-run with same key = no second claim.
- **Human-approval gate on:** `submit_claim` (PreToolUse pause). Decision persisted with `approved_by`/`approved_at`.
- **Transparent decision rule:** a claim exists only when source rows support it by explicit arithmetic — short = `PO_qty − GR_qty` (UoM-normalized); damage = GR damage qty × contract price; price_gap = `(invoice_unit_price − contract_unit_price) × billed_qty`; rebate = `Q1_volume ≥ threshold ⇒ earned_rate × volume`. Missing GR ⇒ **not-claimable** (never fabricate). UoM normalized before every € comparison.
- **Observability:** every run emits a `run_id`; engineer trace (matches, exclusions, conversions) + business audit record (per claim: €, line-math, evidence, bucket, approver). Joinable by `run_id`.
- **Secrets handling:** no secrets in MVP (local files / stubbed submit). When real submission API lands, secrets via env/secret store, never logged. `[confirm on day]`
- **Period discipline:** Q1 2026 only; exclude the Q4 row from Q1 totals.
- **Determinism:** same input ⇒ same € every run (mock-first).

## 8. Acceptance criteria (tests & demo script)

> **All 13 pass** as of the build — see `tests/test_acceptance.py` (18/18). Two prep assumptions were **overturned by the real data** and corrected below; both corrections make the story more defensible (we don't fabricate, and we show where money *isn't*).

- [x] **Meadowvale Dairy (SUP-003) — UoM negative control (corrected):** Dairy is quoted **per case (12 units)**. Once UoM is normalized, INV-2003 (6,000 units @ €1.50) reconciles **exactly** to PO-1003 (500 cases @ €18.00) = €9,000 → **€0, NO claim**. The flagship is not "money found in dairy" (that would be fabrication) but **proving the claim Jenny abandoned doesn't exist**, while the per-case logic that defeated her is shown explicitly. *(Prep had assumed a missed dairy claim; the data says otherwise.)*
- [x] **Greenfield Farm — short delivery, logged-correct:** PO_qty − GR_qty = **150 kg**; billed for 150 undelivered × €2.50 = **€375.00**; reconciles to **open** tracker row CLM-001 (bucket **logged-correct**).
- [x] **Sunrise Bakery — price-gap, logged-correct:** rolls €0.95 vs €0.80 × 5,000 = **€750.00**; matches tracker CLM-002 (in progress → **logged-correct**).
- [x] **Riverside Beverages — damage, MISSED:** GRN-3005 flags **120 damaged cases** × €9.00 = **€1,080.00**; **not in the tracker** → bucket **missed** (the largest single missed discrepancy).
- [x] **Prime Cuts Butchers — duplicate / over-claim:** chicken €6.80 vs €6.50 × 1,500 = **€450.00**, real once but logged **twice** (CLM-004 + CLM-006) → bucket **over-claimed**, `duplicate_of=CLM-006`, over-claim risk €450; does **not** raise a second claim.
- [x] **Sweet Treats — not-substantiable:** PO-1007 has **no GRN** → **not-claimable**, **no claim raised** (no fabrication).
- [x] **Rebate entitlement check (corrected):** Of the four rebate suppliers (flour/drinks/packaging/dairy), **only Northgate flour crosses** its threshold (€51,600 ≥ €50,000 @ 3% = **€1,548.00**, MISSED); the other three are below (Riverside a €2,600 near-miss) → recorded transparently as €0, not raised. **Plus Sunrise promo €2,000/qtr** owed unconditionally (MISSED). *(Prep had assumed rebates were the big multi-supplier upside; only one qualifies.)*
- [x] **Mark's question answered:** **€6,203 owed · €0 recovered · 0% recovery rate · €4,628 missed · €450 over-claim risk · €24,812 annualized.**
- [x] **Idempotency:** re-submit with same `(po_id|claim_type)` key returns `ALREADY_SUBMITTED`, no second claim.
- [x] **Human gate:** `submit_claim` returns `BLOCKED_NEEDS_APPROVAL` until a human approval is persisted; nothing is written without it.
- [x] **Trace + audit:** every run emits a deterministic `run_id` and writes `out/<run_id>.trace.json` + `.audit.json`; no secrets logged.

## 9. Assumptions & mocks

- **CSVs are live on disk** — `load_period_data` validates columns and fails loud on mismatch; on a real engagement re-confirm schemas against the customer's exports. `[confirm on day]`
- **SUP-003 dairy = 12 units/case**; **assume other UoM traps exist** until proven otherwise (check pack/case size per supplier).
- **`submit_claim` is stubbed** (returns deterministic mock `submission_id`); real endpoint/auth TBD. `[confirm on day]`
- **Tracker statuses** (open/paid/disputed) and what "claimed"/"recovered" mean (cash landed vs logged) `[confirm on day]`.
- **Rebate basis** (gross vs net, per-period, tiered) and **promo trigger conditions** `[confirm on day]`.
- **Damage coding** in GRs and **partial deliveries / multiple GRs per PO** handling `[confirm on day]`.
- **Q1 2026 closed** as of early Apr 2026 ⇒ claimable; exclude the single Q4 row.

## 10. Rollout & handoff

- **Runs:** locally / in Finance Ops' environment over period CSV exports; batch run, no Jenny dependency.
- **Operator:** Jenny (day-to-day) + Paula (owner); designed to run unattended on a schedule next.
- **Secrets owner:** Finance Ops / IT when the real submission API is wired. `[confirm on day]`
- **Update/rollback:** SPEC is source of truth; deterministic mock means safe re-runs; submit is idempotent so rollback = don't re-approve. Tracker untouched.
- **Next expansion:** schedule recurring runs; widen UoM/contract coverage; later automate submission + chase loop and write recovered € back to the tracker.

## 11. Open questions (confirm with Paula/Jenny/IT on the day)

- Exact CSV schemas/columns and the period field used to scope Q1.
- Confirm the **write boundary**: identify-only vs human-gated submit for MVP (`[confirm with Paula]`).
- Tracker semantics: statuses, what "recovered" means (cash vs logged), and when credit windows close.
- Rebate threshold basis (gross/net, tiered) and promo funding trigger conditions.
- All supplier pack/case sizes (UoM traps beyond SUP-003); how damage is coded; multiple GRs per PO.
- Real claim-submission target + auth (to replace the stub) and who owns those secrets.
- Agree the exact **€X owed / recovery-rate target** with Mark/Paula at the 10:30 scope check before building.

## 12. Build plan & status (spec-driven-build)

**Stack:** Python 3 (stdlib only — `csv`, `dataclasses`, `hashlib`, `json`, `argparse`); deterministic, dependency-free, runs on any machine. **Transparent arithmetic** (constitution §6): every € is re-checkable line-math, never opaque inference. Orchestration today is the **autonomous CLI runner** (`agent/run.py`); the Claude Agent SDK + MCP-server wrapper is the documented next step (the deterministic engine becomes the tool layer the SDK calls).

**Module map (tool surface from §5 → code):**

| SPEC tool | Module | Notes |
|---|---|---|
| `load_period_data` | `agent/loader.py` | validates columns, scopes to Q1, splits the Q4 row out |
| `normalize_uom` | `agent/matcher.py` | reads pack size from the contract note (generic, not SUP-003-hardcoded) |
| `three_way_match` | `agent/matcher.py` | short / damage / price-gap; missing-GRN → not-claimable |
| `compute_entitlements` | `agent/entitlements.py` | rebate (only if threshold crossed) + promo |
| `reconcile_against_tracker` | `agent/reconcile.py` | buckets + duplicate detection + orphan-row scan |
| `build_claim_pack` / roll-up | `agent/claimpack.py` | per-claim pack + Mark's-question roll-up |
| `submit_claim` (**the only write**) | `agent/submit.py` | human-gated, idempotent, capped, stubbed |
| run_id + trace/audit | `agent/observability.py` | deterministic run_id; `out/<run_id>.*.json` |

**Run it:**
```
python3 -m agent.run                 # full reconciliation report (read-only)
python3 -m agent.run --json          # machine-readable roll-up + claim packs
python3 -m agent.run --approve "SUP-001:Q1-2026|rebate" --approver "Mark Bryant"
python3 -m agent.run --submit        # the only write; only fires for approved claims
python3 tests/test_acceptance.py     # 18/18 acceptance criteria
```

**Status: MVP complete & green.** 18/18 acceptance criteria pass; the human-gated idempotent write was exercised end-to-end (blocked → approved → submitted → already-submitted). Engine numbers match the independent 4-stream verification exactly.
