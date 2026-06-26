# Talk Track — Daily Basket Claims Agent (17:00 presentation)

> Your presenter cheat-sheet for the co-founder + hiring-manager session. **This is a presentation, not a live build** — everything is already shipped. You demo the agent, walk the proof, point to the asset + case study, and close with where the account goes next.
> Every number here is live engine output (`python3 -m agent.run`, run `run-Q1-2026-70ce31ef`, 18/18 acceptance criteria) — re-checkable from the source rows.

---

## Slot plan (~45 min: present ~25, leave ~20 for Q&A)

| Min | Beat | Goal |
|--:|---|---|
| 0–1 | **Cold open** | One sentence that lands the outcome |
| 1–3 | **The reframe** | Why I didn't automate the spreadsheet ("consultants, not order-takers") |
| 3–10 | **Demo** | Local engine live → buckets → 18/18 tests → the one gated write |
| 10–15 | **Proof pack** | €35,403 protected, the three traps, honest 0% recovered |
| 15–18 | **Live on Duvo** | Closed loop 0%→89.2% demonstration + the one honest caveat |
| 18–19 | **Asset + case study** | Point to them (don't walk them line-by-line) |
| 19–25 | **Where this goes next** | Three horizons + the ask |
| 25–45 | **Q&A** | See the bank below |

---

## Cold open (say this first, verbatim-ish)

> *"Daily Basket is owed money by its suppliers all the time — short deliveries, damage, prices above list, rebates and promos earned but never claimed. They just couldn't say how much. Mark asked 'how much are we recovering versus how much are we owed?' and Finance had no answer. Now they do: **€6,203 owed, €4,628 of it never logged, and €29,200 of double-billing blocked before AP paid it — €35,403 protected in one quarter** — and every euro is line-math you can hold up in front of a supplier."*

## The reframe (the FDE judgment moment — own it early)

The stated ask was *"automate our claims spreadsheet."* You didn't — and that's deliberate:

> *"Automating the spreadsheet would hard-code its blind spot. The sheet only contains what someone happened to chase, so the money nobody logged stays invisible forever. So I didn't digitize the sheet — I **replaced it as the source of truth**. The agent derives the claims that *should* exist from the source systems — purchase order, goods receipt, invoice, plus contracts — and uses the tracker only as a **reconciliation target**. That reframe is the whole reason an unanswerable question turned into €4,628 of missed money. Digitizing the sheet would've shipped a faster version of the wrong answer."*

---

## Demo runsheet

### 1. Demo strategy
- **Spine = the LOCAL engine, live in the terminal.** Stdlib-only, deterministic, instant, offline — *nothing* in the room can fail mid-sentence (no network, no auth, no API latency). You type, it prints the same numbers every time.
- **Duvo = proof, by reference.** You don't run the closed loop live; you *point to* the captured Duvo run record (`aop/DEPLOYMENT.md` + IDs) as evidence the same logic already ran end-to-end on the platform.
- One line to say it: *"I'm running the engine locally so the math is in front of you with zero network risk; the Duvo run record proves the same logic runs platform-native."*

### 2. Command card (type in order; cwd = repo root)

**(a) Run the report**
```bash
python3 -m agent.run
```
> Say: *"This is the whole answer to Mark's question — derived from the ERP exports, not from the spreadsheet. Read-only, runs anywhere, same numbers every time."*

**(b) Narrate the buckets** (no new command — talk over the printed output; see §3)
> Say: *"Every euro here is line-math you can re-check — short-ship qty, price gap, rebate threshold — never inference. The tracker isn't my source; it's just what I reconcile against."*

**(c) Numbers are contracts**
```bash
python3 tests/test_acceptance.py
```
> Say: *"€6,203 owed, €4,628 missed — those aren't slides, they're assertions in the suite. 18 of 18 green means the headline is a contract, not a claim."*

**(d) The one human-gated write**
```bash
python3 -m agent.run --approve "SUP-001:Q1-2026|rebate" --approver "Mark Bryant"
```
> Say: *"The agent reads everything, but it only ever writes one thing — a claim submission — and only after a named human approves it. Idempotent, value-capped, stubbed. Smallest safe surface."*

### 3. What to point at on screen (when the report prints)
Put your finger on these four, in order:
1. **`MARK'S QUESTION` block (top)** — `€ owed €6,203 · recovered €0 · RECOVERY RATE 0%`. *"This is the number they couldn't produce before."*
2. **`MISSED` bucket** — 3 claims totalling **€4,628** (Riverside damage €1,080, Northgate rebate €1,548, Sunrise promo €2,000). *"Money that should have been claimed and was never even logged."*
3. **`DO-NOT-PAY` / `PREVENT-LOSS` block** — **€29,200** across 3 duplicate invoices. *"Double-billing flagged before AP pays it — loss prevented in the other direction."*
4. **`NOT-CLAIMABLE` items at €0** — Meadowvale (UoM normalizes to €0) + Sweet Treats (no goods receipt → human). *"It refuses to fabricate — the 'hero' dairy claim is €0 once units line up."*

### 4. The 60-second Duvo segment (spoken, while showing `aop/DEPLOYMENT.md`)
> *"Same logic, live on Duvo. Two agents over a Google-Sheets surrogate ERP: a reconciliation agent that plays Daily Basket, and a supplier simulator that plays the eight suppliers from their own private ledger. The recon agent raised the claims, a human approved the gate, the suppliers responded, and the loop resolved over multiple turns — moving recovery from **0% to 89.2%, €5,536 of €6,203 banked.** The €667 gap is the Sunrise March promo, correctly NOT chased because the contract lapsed 2026-02-28."*
- IDs on hand if asked: recon agent `eb165d7e-c8aa-43d3-84ff-055fbcc961e3`, team `Ari Nakos Trial Days`.
- **The honest caveat — say it unprompted:** *"To be clear — simulated suppliers, surrogate ERP, trial team, not real cash or real email. The euro math was reasoned by the agent and matched the deterministic engine exactly; for production I'd expose this engine as an MCP so the arithmetic is guaranteed, not reasoned."*

### 5. Failure fallbacks
- **Projector dies:** narrate from this sheet — the four numbers (€6,203 / €4,628 / €29,200 / €0) are the whole story.
- **Terminal/Python won't run:** open `out/run-Q1-2026-70ce31ef.audit.json` (business rollup) + `.trace.json` (engineer trace) — same numbers, no execution.
- **No network:** expected — the local engine is offline by design. For the Duvo segment fall back to `aop/DEPLOYMENT.md` + `PROOF-PACK.md`.
- **Total laptop failure:** have phone/slide screenshots of (1) the printed report, (2) `18/18 passed`, (3) the DEPLOYMENT.md run-record table.
- **Golden rule:** if anything stutters, fall back to the engine — *never* to the live Duvo loop in the room.
- **Pre-flight:** `ls out/` and run all four commands once before you walk in, so the fallback paths are real and the demo is warm.

---

## Numbers cheat-sheet (memorize these)

| Number | What it is | One-line basis (defend it) |
|---|---|---|
| **€6,203** | Total owed, Q1 2026 (justified, de-duplicated) | 6 claim packs from PO↔GRN↔Invoice + contracts. = 4,628 missed + 1,125 logged-correct + 450 over-claimed. |
| **€4,628** | Missed / never logged (3 claims) | Riverside damage **€1,080** + Northgate rebate **€1,548** + Sunrise promo **€2,000**. |
| └ €1,080 | Riverside damage — *high confidence* | GRN-3005: 120 cases leaking/crushed, photos with warehouse × €9.00/case. |
| └ €1,548 | Northgate volume rebate — *high confidence* | Q1 spend €51,600 ≥ €50,000 threshold → 3% × €51,600. Only supplier that crosses. |
| └ €2,000 | Sunrise promo — **MEDIUM confidence** | €2,000/qtr co-funding, but **contract lapses 2026-02-28**. Full-quarter assumed → pro-rate or confirm before quoting. |
| **€1,125** | Logged-correct (already on it) | Greenfield short €375 (CLM-001) + Sunrise price-gap €750 (CLM-002). |
| **€450** | Over-claimed — real, but logged twice | Prime Cuts (€6.80−€6.50)×1,500kg. Logged as **CLM-004 + CLM-006**, different owners → would double-chase/double-pay. |
| **€29,200** | Duplicate billing BLOCKED (do-not-pay, 3 invoices) | INV-2032 Riverside €16,200 + INV-2033 Greenfield €3,000 + INV-2031 Northgate €10,000. **Prevent-loss, NOT a recovery claim.** Discriminator: count the GRNs (2nd invoice, 1 receipt = double-bill). |
| **€35,403** | Total money protected | 6,203 owed + 29,200 blocked. |
| **€0 / 0%** | Recovered to date / recovery rate | Honest starting point — claims *identified & packaged*, not yet *collected*. The denominator nobody had before. |
| **€24,812/yr** | Annualized run-rate | Q1 × 4 (6,203×4). **Seasonality caveat** — confirm with Finance before quoting externally. |
| **0% → 89.2%** | Duvo live demo recovery | €5,536 of €6,203, one human approval, two-agent closed loop. |
| **€667** | The 89.2% gap | Sunrise promo March portion — contract lapsed 2026-02-28, correctly not over-collected. |
| **18/18** | Acceptance criteria | `python3 tests/test_acceptance.py` — every headline number asserted as a test contract. |

*Also handy:* €2,628 = high-confidence missed money (Riverside + Northgate) = €4,628 minus the medium-confidence Sunrise €2,000.

---

## Honesty landmines (own these before they ask)

1. **Recovery is €0 — and that's the point.** "Claims are *identified and packaged*, not yet *collected*. €0 recovered is the honest denominator — the thing Finance never had. You can't manage a recovery rate you can't compute; now Mark has one."
2. **The 89.2% is a demonstration, not customer cash.** "We proved the recovery loop closes end-to-end on Duvo — but with *simulated* suppliers and a *surrogate* Sheet ERP. The €5,536 isn't in Daily Basket's bank; it shows the loop works. Next step is real exports and real suppliers."
3. **The €24,812/yr is Q1×4, not a promise.** "A run-rate, not a forecast. Q1 has its own seasonality — I'd validate against full-year exports before quoting externally. I'm giving you the method, not a guaranteed annual figure."
4. **On Duvo, the euro math was *reasoned*, not *guaranteed*.** "It matched my deterministic engine to the cent — but 'matched this run' isn't 'guaranteed every run.' Production exposes the engine as an MCP so the math is computed, not reasoned. A deliberate trust upgrade, not a gap I missed."
5. **The sample is tiny — by design.** "~8 suppliers, ~20 rows per file. I chose hand-checkable data so every euro can be verified against source rows — that's how you earn trust in a finance tool. Real figures come from the full exports; the engine scales, the verification discipline stays."
6. **The Sunrise €2,000 has a pro-rate caveat.** "Flagged medium-confidence on purpose — the promo contract lapses two-thirds into the quarter. The agent says *pro-rate or confirm* rather than assert it. It's also exactly the €667 gap in the Duvo demo — the agent correctly didn't over-collect."
7. **Turn-taking in the live loop was manual.** "I advanced it by hand to keep it observable while building. Production replaces that with a Status-Change trigger or Queue so the loop self-advances. The human approval stays; the manual stepping goes."

---

## Anticipated Q&A

> The hardest questions this room will actually ask, grouped. Every number is engine output, re-checkable from source rows.

### Product & FDE judgment

**"We asked you to automate the spreadsheet. You didn't. Why?"**
Automating the spreadsheet hard-codes its blind spot: it only contains what someone *happened to chase*, so the un-claimed tail stays invisible forever. Instead I derive the claims that *should* exist from PO ↔ Goods Receipt ↔ Invoice + contracts, and use the tracker as a **reconciliation target, not the source of truth**. That reframe turned Mark's unanswerable question into €6,203 owed with €4,628 never logged. Digitizing the sheet would've given him a faster version of the wrong answer.

**"How is this different from a BI dashboard, or a script someone could write?"**
A dashboard shows data you already have; it can't show the claim that was never raised, because that row doesn't exist to chart. This *derives* missing claims from the discrepancy between three systems and a contract, then packages each with line-math and evidence ready for a supplier. A script could do the arithmetic — and underneath, mine does — but the value is the judgment layer: routing the unprovable Sweet Treats shortage to a human, flagging the Prime Cuts duplicate, chasing claims through correspondence. That's an agent's job, not a cron job's.

**"Why an agent at all, instead of deterministic code?"**
The math *is* deterministic code, and it stays that way — same inputs, same euros, stdlib-only. The agent never does arithmetic. It sits *on top* — orchestrating the pipeline, deciding what's claimable vs. what needs a human, writing supplier correspondence, chasing replies. The principle: never put the euros inside the model's reasoning. The engine guarantees the number; the agent handles the messy language-and-judgment work around it.

### Trust & correctness

**"How do I know these numbers are right?"**
Every euro is re-checkable by hand from source rows — Riverside's €1,080 is 120 damaged cases × €9.00, traceable to GRN-3005. The headlines aren't prose, they're **asserted in the test suite as contracts**: 18/18 pin €6,203, €4,628, €450, 0%. Change the engine and a number moves, the tests go red. Transparent arithmetic a buyer can hold up in front of a supplier, not opaque inference.

**"What stops it inventing money or hallucinating a claim?"**
Three guardrails, each a passing test. **No evidence, no claim:** Sweet Treats has no goods-receipt row → unprovable → routed to a human, not invented. **No phantom gaps:** Meadowvale's per-case pricing is normalized before comparing, so a naive ~€99k "gap" closes to exactly €0. **No double-counting:** Prime Cuts' real €450 was logged twice under different owners → flagged, not raised twice. The model never produces a euro figure; it routes and explains what the engine computed.

**"What's the false-positive story — does it over-claim?"**
The flagship false-positive is Meadowvale Dairy. They quote per case (12 units/case, read from the contract note, not hard-coded). A naive unit-price compare flags a huge phantom gap — literally why Jenny "couldn't get the numbers to line up." Normalized, INV-2003 reconciles *exactly* to PO-1003 → €0, no claim. The honest answer is zero, so they stop chasing it. The engine is built to close false positives, not manufacture claims.

### Business

**"Recovery is 0% — so what did we actually get?"**
0% is the honest starting line, and that's the point: before this, Mark couldn't even compute the *denominator*. Now he can — €6,203 owed, €4,628 never previously logged, plus €29,200 of duplicate billing flagged "DO NOT PAY." The deliverable isn't collected cash yet; it's the first time the recovery rate is *answerable*, with €35,403 identified or protected in a single quarter. Identified ≠ collected — and now there's a number to drive to 100%.

**"Is the €24,812/yr run-rate real?"**
It's Q1 × 4, with two caveats before anyone quotes it. Seasonality: a grocer's Q1 isn't four identical quarters. Sample size: ~20 rows per file, hand-checkable by design — great for proving correctness, thin for forecasting. So I treat €24,812 as an order-of-magnitude indicator, not a committed number; the validated figure is the €6,203 owed in the quarter we actually measured.

**"Why should Mark fund this?"**
It removes a key-person risk that already cost money — when Jenny was out two weeks in February, credit windows nearly closed. It answers the exact question he asked and Finance couldn't. And the first quarter alone surfaced €4,628 in missed money the old process structurally couldn't see, plus €29,200 in double-billing it would've paid blind. It pays for itself on the un-claimed tail in one quarter; every quarter after is recurring.

### Platform & Duvo

**"Walk me through what's actually deployed on Duvo."**
A **two-agent closed loop** on Duvo Production (trial-team scope): a reconciliation agent playing Daily Basket, and a Supplier Simulator role-playing all 8 suppliers from their *own private ledger*. They share one Google Sheets workbook as a surrogate ERP — source tabs read-only, a Correspondence tab as the message bus replacing email. It's **AOP-only** (no custom code in the deployment), and turn-taking is currently **manual** with one human approval gate. The arithmetic was reasoned by the agent and matched the deterministic engine to the cent.

**"Is the 89.2% recovery real?"**
No — and I'm explicit. 89.2% (€5,536 of €6,203) *demonstrates* the recovery loop works end-to-end, not money in the bank. The suppliers are simulated `SupplierLedger` rows, the ERP is a surrogate Sheet, no real email. What it proves: claims go out, the supplier reasons from its own books, credits and a stall come back, the agent banks them — including correctly *not* chasing the €450 duplicate and the Meadowvale false positive. The €667 gap is Sunrise's March promo, honestly left because the contract lapsed 2026-02-28.

**"What breaks at real-supplier, 200-supplier scale?"**
Four things, each documented as a known gap. The agent currently *reasons* the arithmetic in the loop — at scale I'd expose the deterministic engine as an MCP so the math is guaranteed. Turn-taking is manual — production uses a Status-Change trigger or Queue to self-advance. No real privacy boundary today (both agents share one workbook) — production splits the supplier's books behind a real integration. And UoM traps beyond dairy, multiple GRNs per PO, and rebate basis (gross/net/tiered) need confirming against live data.

### Delivery

**"What would you do with two more days?"**
Day one: expose the deterministic engine as an MCP server/skill so the live agent *calls* the arithmetic instead of reasoning it — the single biggest trust upgrade, already the documented next step. Day two: replace manual turn-taking with a Queue/trigger, and run scope checks against live exports — rebate basis, other suppliers' pack sizes, what "recovered" means (cash vs. logged). I'd resist new features; the brief caps me at two post-MVP cycles, and a tighter trust story beats a broader fragile one.

**"What's the reusable asset, and why does it matter for the next customer?"**
The reusable asset is the **recovery pattern itself**: derive what *should* be true from source systems, reconcile against the human record, bucket into missed / correct / over-claimed / not-claimable, gate the one write. Not specific to grocery — it's the shape of any "are we leaving money on the table?" reconciliation. For the next customer I keep the architecture and swap the domain rules. The trial built a claims agent; what it really produced is a repeatable way to build recovery agents.

---

## Where this account goes next

Daily Basket is the strongest kind of FDE beachhead: thin-margin, high-volume, money leaking structurally, every euro recovered or blocked dropping straight to the bottom line. We landed by answering the one question Mark couldn't. Here's where I'd take it — three horizons, numbers kept honest.

> **One caveat governs everything.** The proof is a **single quarter, ~8 of ~200 suppliers** — €35,403 protected, demonstrated live at 89.2%. Those are *demonstrated and identified*, not *collected*. I won't multiply a tiny sample into a fake-precise headline. The real number comes from full exports; the ranges below *bound* it, not oversell it.

### Horizon 1 — Harden and scale the win (2–6 weeks)
1. **Run all ~200 suppliers × all 4 quarters.** The biggest unknown-to-known step. *Bound, not forecast:* if per-supplier recovery held, ~200 suppliers implies a mid-five- to low-six-figure annual *recoverable* run-rate (the €24,812/yr from 8 suppliers is the floor); duplicate-billing prevention (€29,200/qtr) plausibly scales further because AP double-bills are volume-driven. **Commit to a real number only after the export run** — that run *is* the deliverable, and costs us almost nothing because the engine exists.
2. **Make the loop unattended.** Replace manual turn-taking with Schedules now, a Case Queue as the production target (`aop/auto-handoff.md`). Wiring, not redesign — the AOP is already idempotent. Gated high-value items still stop for a human.
3. **Expose the engine as an MCP/skill** (`mcp_server/`) so the euro math is guaranteed, not reasoned — the LLM orchestrates but never touches the trust-critical arithmetic.
4. **Wire the real submit target + AP duplicate-payment block as live controls.** Replace the stub; turn the €29,200 do-not-pay signal into a pre-payment gate. Fastest "money that moves" win — the one Mark feels first.

### Horizon 2 — Adjacent finance-ops leakage (next quarter)
Same three-way-match spine, pointed at the next leak — no new core:
- **AP duplicate-payment prevention as its own control** — promote the €29,200 / GRN-count signal to a standing pre-payment gate across all 200 suppliers.
- **Early-payment / payment-terms discount capture** — `payment_terms_days` is already in contract data; flag every invoice with an unclaimed term-driven discount or paid outside terms.
- **Contract-compliance monitoring** — silent price creep, rebate thresholds crossed but never invoiced, promo windows lapsing (the Sunrise case) — run as a *monitor*, not just a quarterly reconcile.
- **Accruals / credit-note reconciliation** — derived-truth-vs-logged machinery applied to the credit-note / accruals ledger.

### Horizon 3 — Replicate the pattern (the Duvo platform play)
"**Recover what you're owed**" is a *reusable, parameterized pattern*, not a bespoke build. Any business with PO/GRN/Invoice + supplier contracts — other grocers, distributors, wholesalers, hospitality, retail in Duvo's book — has the same leak. The reusable runbook (`prep/reusable-asset-claims-recovery-runbook.md`) + parameterized template turn this deployment into a **template**: map the customer's exports onto five input roles, confirm the data quirks, and the engine + AOP + guardrails come for free. The FDE flywheel — one deployment becomes a repeatable land motion. *Honest gate:* the pattern needs an independent upstream source of truth to derive from (no PO/GR feed → you can only digitize the spreadsheet, which we explicitly don't do). That qualifier is also the sales filter for which accounts fit.

### The ask
To start Horizon 1 this month, three things from Mark and Paula:
1. **Full ERP exports** — all ~200 suppliers, all 4 quarters. The one input that turns the bounded estimate into a real number. (Read-only; `data/` stays untouched.)
2. **A real submit target + a named owner** — the actual claims destination and AP duplicate-payment gate, plus who owns the approval queue.
3. **A sign-off on the autonomy level** — what the loop may do unattended (sub-threshold, reversible) vs. what always waits for a human (claims over €1,000, closing human-owned rows). I'd rather Mark draw that line than assume it.

> Give me those three and the full-book number — the one Mark actually cares about — is a 2–6 week deliverable, not a promise.

---

## Close (last 30 seconds)

> *"So: I didn't automate the spreadsheet — I replaced it as the source of truth. In one quarter that protected €35,403, every euro re-checkable, and I demonstrated the full recovery loop live on Duvo. Recovery today is honestly €0 — but for the first time the question is answerable, and I've shown the loop that drives it to 89%. Give me the full exports and a real submit target, and the whole-book number is a two-to-six-week deliverable."*
