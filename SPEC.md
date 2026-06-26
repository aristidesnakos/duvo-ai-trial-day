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
| `purchase_orders.csv` (ERP) | agreed qty & price per PO | CSV export | n/a (file) | mock — file not yet provided |
| `goods_receipts.csv` (ERP/GRN) | received qty + condition (damage code) | CSV export | n/a (file) | mock — file not yet provided |
| `invoices.csv` (AP / supplier portal) | billed qty & price | CSV export | n/a (file) | mock — file not yet provided |
| `supplier_contracts.csv` | contract prices, UoM/pack size, rebate thresholds, promo funding terms | CSV export | n/a (file) | mock — file not yet provided |
| `supplier_claims_tracker.csv` | today's spreadsheet — **reconcile target, not source of truth** | CSV export | n/a (file) | mock — file not yet provided |
| `email_thread.pdf` | how claims are triggered/handed off; human-gate context | PDF (present) | n/a (file) | available |
| Claim submission target (supplier credit-note / dispute) | the only write | `[confirm on day]` — assume stubbed | `[confirm on day]` | **stubbed (mock)** for demo |

**System of record = ERP exports + contracts (READ).** Tracker = reconcile target (READ). All file schemas/columns are `[confirm on day]` against the real CSVs.

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

- [ ] **Meadowvale Dairy (SUP-003) — missed / UoM (hero):** Given dairy lines quoted **per case (12 units)**, when matched with UoM normalized, then a **justified claim Jenny abandoned** is surfaced, bucketed **missed**, with the conversion shown in evidence. Without normalization the numbers don't reconcile (negative control).
- [ ] **Greenfield Farm — short delivery, logged-correct:** Given tomatoes PO_qty − GR_qty = **150 kg** with a GRN and no credit note, then a justified short-delivery claim is produced and reconciles to the **open** tracker row (bucket **logged-correct**).
- [ ] **Sunrise Bakery — price-gap, logged-correct:** Given invoice price > contract price on rolls, then a **price-gap claim ≈ €750** is produced and matches the **disputed** tracker row (bucket **logged-correct**); € matches within rounding.
- [ ] **Prime Cuts Butchers — duplicate / over-claim:** Given a meat claim appearing **twice** in the tracker, then reconciliation flags **over-claimed** with `duplicate_of` set and does **not** raise a second claim.
- [ ] **Sweet Treats — not-substantiable:** Given gummy-bear claim with **no/short GR (no evidence)**, then the agent returns **not-claimable** with reason and **raises no claim** (no fabrication).
- [ ] **Rebate entitlement check:** For each rebate supplier (flour, drinks, packaging, dairy), given Q1 volume vs contract threshold, then earned-but-unclaimed **rebate €** is computed with basis shown; threshold-crossing cases bucketed **missed**.
- [ ] **Mark's question answered:** Run produces **€ owed**, **€ recovered**, **recovery rate**, split missed/logged-correct/over-claimed, plus annualized run-rate.
- [ ] **Idempotency:** re-run with same `(po_id, claim_type)` does not double-submit.
- [ ] **Human gate:** `submit_claim` pauses for approval; nothing is written without it.
- [ ] **Trace + audit:** every run leaves a `run_id`-joinable trace and per-claim audit record; no secrets logged.

## 9. Assumptions & mocks

- **CSVs not yet provided** — schemas/columns/values assumed; `load_period_data` validates and fails loud on mismatch. `[confirm on day]`
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
