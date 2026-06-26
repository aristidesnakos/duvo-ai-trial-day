# TALK TRACK — Supplier-Claims Reconciliation Agent

> Spoken-word narrative for a ~10-minute final presentation.
> Audience: **Paula Hart** (Finance Ops Lead, sponsor) · **Mark Bryant** (Finance Director, economic buyer) · **Duvo co-founder + hiring manager** (grading engineering *and* consulting).
> Delivery note: speak it, don't read it. Pauses are marked `[…]`. Time budgets are the ceiling — if you're over, cut the parentheticals first, never the numbers.

---

## 0. Opening — "why I want to be deployed at a customer" (60 sec)

Thanks for the day. Before I show you what I built, thirty seconds on why I want this job — because it's the same shape as what I did today.

The work I like is going into a customer's actual mess, finding the workflow that's quietly leaking money, and *owning it the whole way through* — discovery, prototype, rollout, and then the measurement that proves it moved a number. Not handing over a deck and leaving. Sitting next to the person who does the job until the thing runs without me.

That's exactly what happened here. I started the day talking to how Jenny works, found the leak, built one safe agent against your real data, and today I can hand you a number you couldn't get this morning. So let me walk you through it the way I'd want to walk any customer through it. `[…]`

---

## 1. Problem (1 min)

Here's the workflow in one sentence: **Daily Basket is owed money by suppliers — short deliveries, damaged goods, prices billed above contract, and rebates you've earned but never claimed — and today that whole process lives in one analyst's spreadsheet, so the money nobody happened to chase just… stays unrecovered.**

That's the abandoned work. It's reactive — Jenny's own words were *"I catch what I catch."* When she was out sick in February, nobody touched the sheet for two weeks and credit windows nearly closed.

And here's the line that organized everything I built. Mark, you asked Finance: *"how much are we recovering versus how much is owed?"* — and the honest answer was that nobody could tell you. Not because the team's not good, but because **nobody could compute the denominator.** You can't have a recovery *rate* if you've never calculated what you're owed in the first place. `[…]`

So that became the job: compute the denominator, from source, and make every euro of it defensible.

---

## 2. Scope & decisions (3 min) — *the heart of it*

This is the part I most want you to push on, because the decisions matter more than the code.

**The tool surface — seven tools, and exactly one of them writes.** Load and validate the data; normalize units of measure; do the three-way match of PO to goods-receipt to invoice; compute contract entitlements; reconcile what I derived against your tracker; build the claim pack. Those six are all **read-only and deterministic**. The seventh — `submit_claim` — is the *only* thing that can change the outside world. A capability surface is a risk surface, so I kept it as small as it could be while still doing the whole job end-to-end.

**Now the more interesting half — what I deliberately left out.** `[…]`
- **No auto-submit.** The agent never raises a claim on its own. It proposes; a human approves.
- **No write-back to the tracker or the ERP.** Your spreadsheet is a *reconcile target*, not something I touch. I read it to see what you've already caught — I never edit it.
- **No opaque ML.** There is zero inference on the trust-critical path. Every euro is plain arithmetic you can re-check by hand in front of a supplier. I'll show you the exact line-math in a second.
- **And no fabricated claims.** Where the evidence isn't there, the agent *refuses* — it returns "not-claimable" rather than inventing money. That restraint is a feature, and it's where I'd argue you should trust it most.

**On MCP versus computer-use** — this is a real engineering call, so let me be precise. The principle is API before screen: use a real API through an MCP tool wherever one exists, and only fall back to driving a screen when there's genuinely no API. Here, the inputs are clean CSV exports, so today the engine is **deterministic Python** — no LLM anywhere near the arithmetic. The documented next step is to wrap that same engine as an **MCP server** and drive it with the **Claude Agent SDK**, so the model orchestrates the tools but *still never touches the math*. That separation is deliberate: the LLM decides *what to look at*, the deterministic engine decides *what the number is*. `[…]`

**The guardrails, quickly, because they're how you let an agent near money safely:**
- **Blast radius:** the one write is single-entity, single-action, and capped to the exact euro amount I derived. The worst a confused agent can do in one call is propose one wrong claim — which a human then has to approve.
- **Idempotency:** the key is the PO plus claim type. Re-run it, re-submit it — you get "already submitted," never a second claim.
- **Human gate:** `submit_claim` returns `BLOCKED_NEEDS_APPROVAL` until a real person's approval is recorded. Nothing is written without it.
- **Transparency and audit:** every run emits a `run_id` and leaves two records — an engineer-facing trace and a business-facing audit, joinable by that id. No secrets logged.

That's the consulting answer and the engineering answer at once: **smallest safe surface, transparent math, one gated write.** `[…]`

---

## 3. Demo (3 min) — *narrate what they see*

Let me run the real slice. *(commands run live; I'll narrate.)*

**Trigger.** I kick off one run over Q1 2026. No Jenny, no manual step — one command. It loads and validates the five CSVs, scopes everything to Q1, and splits out the one Q4 row so it can't pollute the totals.

**The agent reconciles.** Watch what comes back, because the story isn't just "it found money" — it's that it knows where the money *isn't*.

- The hero case is **Meadowvale Dairy** — the one Jenny gave up on because *"the numbers wouldn't line up."* The contract quotes dairy **per case, twelve units to a case.** The agent normalizes that unit-of-measure first, and once it does, the invoice — six thousand units at €1.50 — reconciles *exactly* to the PO — five hundred cases at €18 — at €9,000. So the answer is **€0. There is no claim.** That's the win: it does the unit conversion that defeated a person, and it tells you to *stop chasing it*. It didn't manufacture a number to look clever. `[…]`
- **Riverside Beverages — €1,080, missed.** A hundred and twenty damaged cases logged on the goods-receipt, the full load invoiced anyway, and nothing claimed. Largest single missed item. Pure recoverable upside.
- **Northgate Mills — €1,548 rebate, missed.** Q1 spend of €51,600 crossed the €50,000 threshold at 3%. Jenny's instinct that "rebates are where the money is" was directionally right — but of the four rebate suppliers, **only this one actually qualifies.** The agent tells you *which* one, so effort goes where it pays.
- **Prime Cuts — €450, and this one's the opposite direction.** A real €450 overcharge that got logged *twice*, under two owners with different spellings. The agent flags it as a duplicate so you don't chase it twice and damage a supplier relationship. Catching an over-claim protects you as much as finding a missed one.
- And **Sweet Treats** — the agent wants to claim it, but there's **no goods-receipt**, so it refuses. Not-claimable. No fabrication.

**Now the gate.** I try to submit the Northgate claim. It comes back `BLOCKED_NEEDS_APPROVAL`. Nothing was written. I record an approval — approver, timestamp — and re-run submit. *Now* it fires, returns a submission id, and writes the audit record. Run it one more time and it says **already submitted** — idempotent.

**The audit record.** Here's what's left behind, joined by `run_id`: the supplier, the PO, the basis, the euro amount, the line-math, the three evidence rows, the confidence flag, and who approved it. That's the artifact you hold up in front of a supplier.

And the headline that answers Mark's question, all from source: **€6,203 owed · €0 recovered · a 0% recovery rate · €4,628 in missed money · €450 of over-claim risk caught · roughly €24,812 annualized.** Thirteen of thirteen acceptance tests pass behind all of that. `[…]`

---

## 4. Deploy & handover (1–2 min)

Where this goes from here. `[…]`

Today it runs **unattended — no Jenny in the loop.** One command, end to end, over a period's exports. That alone kills the key-person risk that cost you two weeks in February.

The next step is **scheduled runs inside your own cloud** — same deterministic engine, wrapped as an MCP server and driven by the Agent SDK, on a quarterly cadence so the rebate and promo windows get checked *every* quarter automatically, not when someone remembers. When the real claim-submission endpoint lands, it goes behind the *same* human gate that's already there — secrets in your secret store, never in logs, owned by Finance Ops and IT.

**The ownership split is clean:** Finance Ops owns the approvals and the claim decisions — that's Paula and Jenny, the gate is theirs. I own the engine, the tool surface, and the schemas, and I keep them current as your real exports evolve. Rollback is trivial because the write is idempotent and the tracker is untouched — if you don't approve, nothing happens; if you do, it can only happen once.

---

## 5. Risks & next (1–2 min)

Let me be honest about the weaknesses, because you should hear them from me first. `[…]`

- **The €2,000 Sunrise promo is medium-confidence, and I want to flag it loudly.** That contract runs to February 28th — it lapses two-thirds of the way through Q1. The agent claims the full quarter and *tells you* the contract wasn't active the whole period. So **pro-rate it or confirm the rule before you quote it to the supplier.** Strip it out and your high-confidence missed money is **€2,628** — Riverside plus Northgate. I'd rather hand you a qualified number than an overstated one.
- **The annualized €24,812 is a run-rate, not a forecast** — it's Q1 times four. Rebates and promos recur quarterly, but discrepancies vary by season. Confirm with Finance before that number leaves the building.
- **It's built on CSV exports today.** The loader fails loud if columns drift, but on a real engagement I'd re-confirm every schema against your live ERP, and I'd assume there are *more* unit-of-measure traps like the dairy one until I've proven there aren't.
- **And `submit_claim` is stubbed.** The whole gated, idempotent, capped pathway is real and exercised — but the actual endpoint and auth are the one thing I'd wire next with IT.

**The next two expansions** are the obvious ones: schedule the recurring runs in your cloud, and widen UoM and contract coverage so nothing like the dairy case can hide again. After that, automate the chase loop behind the gate.

So to close where I opened — the value line I'd bring to any customer: **I get one safe, working agent running against the real stack fast — API where it exists, computer-use where it doesn't, and a human gate on the risk.** Today that turned "we have no idea" into "€6,203 owed, €4,628 of it missed, and here's the evidence for every euro." `[…]` Happy to take it apart.

---

### Timing check
| Section | Budget |
|---|--:|
| 0. Opening | 1:00 |
| 1. Problem | 1:00 |
| 2. Scope & decisions | 3:00 |
| 3. Demo | 3:00 |
| 4. Deploy & handover | 1:30 |
| 5. Risks & next | 1:30 |
| **Total** | **~10:00** |
