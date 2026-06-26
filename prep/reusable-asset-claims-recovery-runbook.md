# Supplier-Claims Recovery: a three-way-match + entitlement reconciliation pattern

> A domain-reusable runbook for FDE deployments at CPG / grocery / retail customers.
> **What it does:** independently *derives* the supplier claims that **should** exist from ERP exports + contracts, *reconciles* them against whatever the customer chases today, and surfaces **recoverable € with an auditable, human-gated claim pack.**
> **Not** "digitize the customer's claims spreadsheet." The spreadsheet is the failure mode; truth lives upstream.

---

## 0. When to use this pattern

Reach for this runbook when the customer's ask sounds like any of:

- "Automate our supplier-claims / deductions / credit-note spreadsheet."
- "We don't know how much we're owed vs. how much we actually recover."
- "Reconcile our invoices against what we received / against contract."
- "Our volume rebates / promo funding — we never check whether we crossed the threshold."
- "One person owns this and when they're out, nothing happens."

**Archetype match (field kit):**
- **Primary** — Cross-system reconciliation: the three-way match `PO ↔ Goods Receipt ↔ Invoice`.
- **Secondary** — Contract entitlement: earned-but-unclaimed rebates / promo funding from period volumes vs. contract thresholds.
- **Tertiary** — Completion / chasing: the un-logged long tail nobody gets to.

**Do NOT use it when** the real job is just OCR-ing supplier credit notes (that's document-understanding), or when there is no independent source of truth to derive claims from (no PO/GR feed). Without an upstream source you can only digitize the sheet — and digitizing the sheet forward-propagates its gaps.

**The reframe to bring to discovery (consultants, not order-takers):**
1. The spreadsheet holds errors *and omissions* — money that should have been claimed was never logged at all. Automating it as-is forward-propagates the gaps.
2. Truth lives upstream: PO/GR/Invoice + contracts are the source. *Derive* claims from source; use the tracker only as a **reconciliation target** (what we caught vs. missed vs. logged wrong).
3. Reframe the outcome from "digitize sheet" → "**recover the money we're owed and remove the single-person dependency.**" That is the € the economic buyer can feel.

---

## 1. Input data contract

You need five inputs. Map the customer's real exports onto these roles; column names vary, the **keys and roles** do not. Confirm each on the day.

### 1.1 Purchase Orders (PO) — what was agreed
| Role | Typical column | Notes |
|---|---|---|
| **PO key** | `po_id` | Primary join key across all three docs. |
| Supplier key | `supplier_id` | Joins to contracts. |
| Line item / SKU | `sku` / `item_id` | Needed when a PO has multiple lines. |
| Agreed quantity | `qty_ordered` | **With its UoM** (case / unit / kg). |
| Agreed unit price | `unit_price` | **With its UoM** — the contracted price basis. |
| Order date / period | `order_date` | For period bucketing. |

### 1.2 Goods Receipt (GR / GRN) — what physically arrived
| Role | Typical column | Notes |
|---|---|---|
| **PO key** | `po_id` | Join back to PO. **May be 1-to-many** (partial deliveries → multiple GRs per PO). |
| Received quantity | `qty_received` | **With its UoM.** |
| Condition | `condition` / `damage_flag` / `damaged_qty` | How "damaged" is coded varies — confirm the vocabulary. |
| Receipt date | `gr_date` | For period bucketing of the *delivery*. |

### 1.3 Invoice — what was billed
| Role | Typical column | Notes |
|---|---|---|
| **PO key** | `po_id` | Join back to PO. May also be many-to-one. |
| Billed quantity | `qty_billed` | **With its UoM.** |
| Billed unit price | `unit_price_billed` | **With its UoM.** Compared to contract/PO price. |
| Invoice date / period | `invoice_date` | For period bucketing. |

### 1.4 Supplier contracts — entitlements & price basis
| Role | Typical column | Notes |
|---|---|---|
| **Supplier key** | `supplier_id` | Join key. |
| Contract price / price list | `contract_price` + **`price_uom`** | The defensible price. **Capture the UoM explicitly.** |
| Pack / case size | `units_per_case` | The UoM-normalization factor. **First-class field, not a footnote.** |
| Rebate basis | `rebate_threshold`, `rebate_rate`, `rebate_basis` | Threshold (volume or €), rate, gross vs. net, tiered?, per-period? |
| Promo funding terms | `promo_terms` / `promo_funding` | Trigger conditions and amount owed. |
| Contract period | `valid_from` / `valid_to` | A claim must fall inside an active contract. |

### 1.5 Claims tracker — the reconciliation target (NOT the source of truth)
| Role | Typical column | Notes |
|---|---|---|
| **Claim key** | `po_id` (+ `claim_type`) | Used to match a tracker row to a derived claim. |
| Claim type | `claim_type` | short / damage / price-gap / rebate / promo. |
| Claimed amount | `amount` | What was logged — compare to what we derive. |
| Status | `status` | open / disputed / paid / closed. Define what "claimed" means and when cash lands. |
| Supplier | `supplier_id` / `supplier_name` | For grouping. |

> **Read-only on all five inputs.** The only write this pattern ever makes is the gated claim submission (§5).

---

## 2. Match algorithm steps

Run per `po_id` (and per line / SKU where lines exist). Every step emits **human-readable evidence**, never just a verdict.

### Step 0 — Period scoping (do this FIRST)
- Decide the claim period (e.g. the closed quarter). Bucket each PO/GR/Invoice by the agreed date basis (confirm: order date vs. receipt date vs. invoice date).
- **Exclude out-of-period rows** from the headline total. Carry them in a separate bucket so nothing is silently dropped.

### Step 1 — UoM normalization  ⚠️ FIRST-CLASS GOTCHA
**Do this before any quantity or price comparison.** This is the single most common reason a human "couldn't get the numbers to line up."
- For each line, resolve the UoM of `qty_ordered`, `qty_received`, `qty_billed`, `unit_price`, `unit_price_billed`, and `contract_price`.
- Normalize everything to **one canonical UoM per line** (typically the base unit) using `units_per_case` / weight conversions from the contract.
  - Example trap: contract quotes **per case = 12 units**; invoice bills **per unit**. A naive price compare reports a 12× phantom gap (or misses a real one).
- **Persist the conversion in the evidence** ("contract €X/case ÷ 12 = €Y/unit; invoice €Z/unit → gap €(Z−Y)/unit"). The buyer must be able to hold the arithmetic up in front of the supplier.
- **Assume UoM traps exist until proven otherwise.** Check every supplier, not just the one the customer flagged.

### Step 2 — Aggregate partial deliveries
- Sum `qty_received` across **all** GRs for the PO before comparing to `qty_ordered`. A single PO is frequently fulfilled by multiple GRNs.
- Likewise aggregate multiple invoices per PO if present.

### Step 3 — Short-delivery check
- `qty_ordered (norm) − Σ qty_received (norm) > tolerance` → **short-delivery claim.**
- € = shortfall × contracted unit price (normalized).

### Step 4 — Damage check
- Inspect `condition` / `damaged_qty`. Damaged units that were billed → **damage claim.**
- € = damaged qty × contracted unit price.

### Step 5 — Price-above-contract check
- Compare normalized `unit_price_billed` vs. normalized `contract_price`.
- `billed > contract + tolerance` → **price-gap claim.**
- € = (billed − contract) × billed qty (normalized).

### Step 6 — Evidence sufficiency gate  ⚠️
- A claim is only raisable if the supporting rows exist. **No GR, no claim** for short/damage. **No contract price, no price-gap claim.**
- If evidence is missing, route to the **not-substantiable** bucket (§4) — do **not** fabricate a claim the data can't defend. (The supplier may simply be right.)

Each derived claim record carries: `supplier`, `po_id`, `claim_type`, `€ amount`, the **three source rows** (PO/GR/Invoice) as evidence, the UoM conversion, and a confidence flag.

---

## 3. Entitlement (rebate / promo) computation

Run per supplier, for the claim period. This is usually the **headline upside** — earned money the reactive process never checks.

### Rebates
1. Aggregate the supplier's qualifying volume (or € spend) for the period — **normalized UoM** and on the correct gross/net basis from the contract.
2. Compare to `rebate_threshold`. If crossed:
   - Flat: `earned = volume × rebate_rate` (or the contracted flat amount).
   - Tiered: apply the rate of the highest tier reached (or marginal-per-tier — **confirm the contract's mechanic**).
3. Emit an **entitlement claim** with the volume math shown line by line.

### Promo funding
1. Identify promos in-period and their trigger conditions (e.g. ran the promo, hit a display/volume commitment).
2. Where triggered, compute owed funding per the contract terms.
3. Emit a promo-funding claim with the trigger evidence.

> Entitlements are still **transparent arithmetic**: every € traces to a contract clause + a volume figure, not a model's guess.

---

## 4. Reconcile derived claims vs. tracker → four buckets

Match each **derived** claim to tracker rows on `(po_id, claim_type)` (supplier+type where no PO). Then bucket:

| Bucket | Definition | Why it matters |
|---|---|---|
| **(a) Missed** | We derived a justified claim; tracker has **no** matching row. | **Recoverable upside — the headline.** "Money never logged at all." |
| **(b) Logged-correct** | Tracker row matches a derived claim, amount agrees. | Already on it; reassures the customer the agent agrees with their wins. |
| **(c) Over-claimed / logged-wrong** | Tracker has a row with **no** derived basis, a **duplicate** row, or an amount **above** what we can substantiate. | **Risk / cleanup** — over-claims expose the customer to supplier disputes. |
| **(d) Not-substantiable** | A claim exists or is implied but evidence is insufficient (§2 Step 6). | Judgment call surfaced honestly; don't raise it, don't hide it. |

**Recoverable € (period)** = Σ(a justified short + damage + price-gap) + Σ(a earned-but-unclaimed rebate + promo) − Σ(c over-claims to retract).
**Run-rate** = period × periods/year (caveat seasonality).
**Recovery rate** = € recovered ÷ € owed — the metric the economic buyer actually asked for; this pattern is what finally computes the **denominator**.

---

## 5. Guardrails (non-negotiable)

- [ ] **Read widely, write narrowly.** ERP exports + contracts = system of record (read). Tracker = reconcile target (read). **Claim submission is the only write.**
- [ ] **Human-gated write.** Each claim submission pauses for human approval (`PreToolUse` gate). Persist the decision.
- [ ] **Idempotent write.** Keyed on `(po_id, claim_type)` (or `(supplier_id, claim_type, period)` for entitlements) so a retry/replay can't double-submit. This *also* defends against the duplicate-row failure mode.
- [ ] **Single-entity, value-capped.** One claim per call; cap the € a single call can submit.
- [ ] **Transparent arithmetic, not opaque inference.** Every € is defensible line-math the buyer can show a supplier. UoM conversion is shown explicitly in the evidence.
- [ ] **Period discipline.** Out-of-period rows excluded from the headline total and bucketed separately.
- [ ] **Observable.** Each run leaves an engineer trace + a business audit record, joinable by run id. No secrets logged.
- [ ] **Mock-first & deterministic.** "Submit claim" is stubbed for the demo; same input → same € every run. Mock → real is a config toggle.

---

## 6. Common data traps checklist

Walk this list on every deployment — each one has sunk a real reconciliation:

- [ ] **UoM / pack-size mismatch.** Contract per-case (e.g. 12/case) vs. invoice per-unit. Normalize *before* any compare; check **every** supplier, not just the flagged one. *(This is the trap that makes a human give up — and the agent's hero moment when it surfaces a claim they abandoned.)*
- [ ] **Partial deliveries / multiple GRs per PO.** Sum all GRNs before the short-delivery check, or you'll invent phantom shortfalls.
- [ ] **Multiple invoices per PO.** Aggregate before the price/qty compare.
- [ ] **Period boundaries.** Which date defines the period — order, receipt, or invoice? Exclude out-of-period rows; confirm the period is *closed* before treating it as claimable.
- [ ] **Duplicate tracker rows.** Same claim logged twice "in a rush" → over-claim risk. The idempotency key catches this on reconcile.
- [ ] **Duplicate invoice (double-bill).** A 2nd invoice on a PO that has **no 2nd goods receipt** is the supplier billing twice for one delivery, not a legitimate second shipment. **Discriminator: count the GRNs** — one GRN + two invoices = double-bill (or a partial re-bill if the prices differ). This is *prevent-loss*, the opposite direction from a recovery claim: flag **DO-NOT-PAY**, route to **AP**, and **never** raise it as a supplier credit claim or let it touch the recovery total.
- [ ] **Dangling reference.** A tracker/claim row cites an invoice or PO **not present in our data** → flag **"reference not found"** and verify before acting; do not chase or pay against an id you can't see in the source.
- [ ] **Evidence sufficiency.** No GR → can't substantiate a short/damage claim; the supplier may be right. Route to not-substantiable, never fabricate.
- [ ] **"Damaged" coding.** A flag? a separate qty column? free text? Confirm the vocabulary before trusting it.
- [ ] **Rebate basis.** Gross vs. net, per-period, tiered (flat vs. marginal)? Get one worked example from the customer.
- [ ] **Tracker status semantics.** What does "claimed" mean — logged, submitted, disputed, paid? When does cash actually land?
- [ ] **Tolerances.** Tiny qty/price deltas (rounding) shouldn't generate claims. Agree a tolerance threshold up front.
- [ ] **Contract validity window.** A claim must fall inside an active contract period.

---

## 7. Smallest safe demo slice (end-to-end)

To prove the pattern fast: take **one PO with a UoM trap**, normalize → derive the claim → show it's **missing from the tracker** (bucket a) → assemble the claim pack with evidence → pause at "submit?". Then show **one over-claimed duplicate** (bucket c) caught on reconcile. Two cases tell the whole story: money we missed, and risk we caught.

---

*Pattern lineage: maps to field-kit archetype #1 (cross-system reconciliation) + #6 (contract entitlement) with a #4 chasing tail. Default stack: Claude Agent SDK orchestrator + MCP for ERP/API reads + computer-use only for no-API portals; Sonnet by default, Opus for browser-heavy runs; under Zero Data Retention for enterprise data.*
