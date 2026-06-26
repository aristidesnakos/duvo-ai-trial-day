# DECISION-DEFENSE Q&A — Daily Basket Supplier-Claims Agent

> One-page defense for the trial-day final. Graded on engineering **and** consulting.
> Grounding (Q1 2026, closed): **€6,203 owed · €0 recovered · 0% recovery rate · €4,628 missed · €450 over-claim risk · €24,812 annualized · 13/13 tests pass.**

---

## Engineering

**Q. Why a deterministic Python engine + MCP, rather than computer use or an LLM doing the reasoning?**
Every euro we put in front of a supplier has to be re-checkable line-math an auditor can hold up — so the trust-critical path is plain arithmetic (`short = invoiced − received × price`, etc.), not inference. An LLM doing the math can silently round, hallucinate a credit, or be non-deterministic across runs; our engine gives the same € every time and writes the arithmetic into the audit record. The LLM/MCP layer sits *on top*: it orchestrates which tools to call and narrates findings, but never touches a number. Computer use is for systems with no API — here the inputs are clean CSV exports, so screen-driving would add fragility and a wider blast radius for zero benefit.

**Q. What's the worst a confused agent can do per call? (blast radius)**
The only write is `submit_claim`, and it is single-entity (one `po_id`/claim_type), single-action, and **quantity-capped to the derived € amount** — it cannot raise more than the math supports, and there is no batch auto-submit. It refuses to fire at all without a persisted human approval token (`BLOCKED_NEEDS_APPROVAL`), and it's idempotent on `(po_id|claim_type)`, so a re-run or a retry returns `ALREADY_SUBMITTED` rather than a second claim. The five source CSVs and the tracker are read-only — nothing the agent does mutates a system of record. Worst realistic case: it queues one over-stated claim for a human to reject at the gate; it cannot pay anyone, touch the ERP, or double-submit.

**Q. How does a key rotation / credential change mid-run behave?**
Today the submit endpoint is stubbed and the inputs are local files, so there are no live credentials to rotate in the MVP — by design, for a safe demo. When the real supplier-credit API lands, secrets come from env/secret store (never logged), and a mid-run rotation simply fails the `submit_claim` call loudly; because the write is idempotent and approval-gated, the safe recovery is to re-run — already-submitted claims return `ALREADY_SUBMITTED`, and un-submitted ones re-attempt cleanly. No partial or duplicate state results from a credential change. The read/derive/reconcile phase is fully deterministic and credential-free, so a rotation can never corrupt the analysis.

**Q. Cloud Run vs GKE — where does it run and why?**
This is a batch, request-triggered job over a quarter of CSVs (~20 rows each) — there's no long-lived service, no horizontal-scale need, so **Cloud Run** (or an equivalent scheduled container/job) is the right fit: scale-to-zero, pay-per-run, minimal ops, and it co-locates in Finance Ops' own GCP project so the data never leaves their boundary. GKE would be over-provisioned standing infrastructure to babysit for a job that runs on a schedule. The engine is stdlib-only Python in one container, so it's portable — it'll run on a laptop, a Cloud Run job, or a scheduled Vertex task with no change. We'd confirm the customer's actual cloud and secret-store on the day rather than assume.

**Q. How do you know it does the right thing before go-live?**
**13/13 acceptance tests pass**, and each maps to a named real-data scenario — short delivery, price gap, damage, the dairy UoM negative control, the duplicate, the missing-GRN refusal, and the rebate threshold checks. The engine's output was cross-verified by four independent analysis passes and is re-checkable by hand because every claim ships its line-math plus the three source rows. Critically, the tests pin the cases where the honest answer is *no money*: dairy reconciles to €0 and Sweet Treats is not-claimable — proving the agent won't fabricate. Determinism means the green test run and the demo run produce identical euros.

**Q. What breaks first at 10× volume?**
Functionally nothing — the matching is linear in rows and stdlib-only, so 200 rows/CSV is still sub-second; this dataset is hand-checkable by design. What strains first is the **human-approval gate**: at 10× claim volume, one-by-one approval becomes the bottleneck, so the next step is risk-tiered approval (auto-approve high-confidence sub-threshold claims, gate the rest) — a policy change, not an engine rewrite. The second pressure point is **input fan-out**: more suppliers means more UoM/pack-size traps and partial-delivery patterns to encode, which is config and coverage work the architecture already anticipates (pack size is read from the contract, not hardcoded).

---

## Finance / business

**Q. Your rebate math credits Northgate €1,548 — but they only clear the €50,000 threshold by €1,600. If we net out credits/returns, does that rebate vanish?**
Fair challenge, and it's the right one to ask. We computed the rebate on **gross PO spend (€51,600)** as a *documented assumption* — it's flagged in the SPEC as a "confirm on the day" item, not a hidden choice. Because Northgate clears by only €1,600, a net-spend definition could pull them back under, so we would not quote that €1,548 externally until Finance confirms whether "spend" means gross or net of credits. Switching basis is a **config flag, not a rewrite** — the threshold test and percentage are parameters, so we re-run and you have the net number in minutes.

**Q. Is the €4,628 of missed money real, or is the promo padding it?**
We lead with what's solid: **€2,628 high-confidence missed money** — Riverside damaged goods €1,080 and the Northgate rebate €1,548, both backed by source rows. The **€2,000 Sunrise promo is presented as caveated upside**: its contract ran to 2026-02-28 and lapsed two-thirds of the way into Q1, so the engine deliberately marks it **medium-confidence** and tells you to pro-rate or confirm the promo rule before quoting it to the supplier. That's the honest read — we surface the money *and* qualify it rather than overstate the headline. The €4,628 is real but tiered, and we'd never put the promo in front of Sunrise without your sign-off on the rule.

**Q. The €450 Prime Cuts amount shows up in both "owed" and "over-claim risk" — aren't you double-counting?**
No — it's the opposite, and catching it is the point. The €450 chicken overcharge is real and **owed exactly once** (€6.80 vs €6.50 contract × 1,500). But it was logged **twice** on the tracker (CLM-004 and CLM-006, different owners and spelling), so the **€450 over-claim risk is the danger of chasing or being paid twice** — which would burn the supplier relationship. The agent raises one claim, flags the duplicate (`duplicate_of=CLM-006`), and does *not* submit a second. The two figures describe one real claim and the duplicate-payment risk attached to it — never two claims.

**Q. Why is the recovery rate 0% — is the agent broken?**
The denominator (€6,203 owed) is now computable for the first time; the numerator is genuinely zero because **nothing logged in Q1 has actually been collected yet**. The only `Paid` row in the tracker is a Q4 item, which we correctly **exclude from the Q1 period totals** — counting it would inflate the rate dishonestly. So 0% isn't a bug, it's the true starting baseline: it's the number that finally lets you measure recovery going forward, which you couldn't do before because no one could compute what was owed.

**Q. How do I trust the €4,628 (and the €6,203) is real and not made up?**
Three independent reasons. First, **transparent line-math**: every euro carries its arithmetic plus the three source rows (PO, GRN, invoice/contract) as evidence — you can re-derive it by hand. Second, **13/13 tests pass** and the engine output was cross-checked by four separate analysis passes. Third, and most telling, **the agent refuses to fabricate**: the dairy claim Jenny chased resolves to **€0** once units are normalized, and Sweet Treats is **not-claimable** because there's no goods receipt to substantiate it. An agent that reports €0 and "can't claim this" where the data doesn't support money is one you can trust on the cases where it does find money.

**Q. What about the unit-vs-case confusion that stumped Jenny on the dairy claim?**
That's exactly the trap we close. Meadovale quotes **per case = 12 units**, so comparing a 6,000-unit invoice against a 500-case PO looks like a huge mismatch — which is what defeated Jenny. The engine **normalizes UoM to a common base unit *before* any euro comparison**, so INV-2003 (6,000 units @ €1.50) reconciles exactly to PO-1003 (500 cases @ €18.00) = €9,000 → **€0, no claim**, with the per-case conversion shown explicitly in the line-math. The win isn't found money — it's permanently retiring a question that ate her time, and the same normalization guards every other supplier against the same trap.
