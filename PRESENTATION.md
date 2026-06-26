# Presentation Run-of-Show — Daily Basket Supplier-Claims Agent

> ~10 minutes to a room grading **engineer + consultant**: Paula Hart (Finance Ops, sponsor), Mark Bryant (Finance Director, economic buyer), + Duvo co-founder & hiring manager.
> Three companion docs: **[TALK-TRACK.md](TALK-TRACK.md)** (what to say) · **[DEMO-SCRIPT.md](DEMO-SCRIPT.md)** (what to type) · **[DECISION-DEFENSE-QA.md](DECISION-DEFENSE-QA.md)** (hard questions).

## Timing

| # | Section | Min | Beat |
|---|---|---|---|
| 0 | Opening — "why deployed at a customer" | 1.0 | discovery → prototype → rollout → measurement; own the outcome |
| 1 | Problem | 1.0 | Mark's question Finance couldn't answer; money never logged |
| 2 | **Scope & decisions** (win here) | 3.0 | 7 tools / one write; what we omitted; deterministic engine vs LLM; guardrails |
| 3 | **Demo** (live) | 3.0 | tests → roll-up → missed → dairy hero → duplicate → **human gate** → audit |
| 4 | Deploy & handover | 1.0 | live on Duvo; runs without Jenny; schedules next |
| 5 | Risks & next | 1.0 | name weaknesses honestly; next two expansions |
| — | **Total** | **~10** | + Q&A |

## The numbers (say them exactly)

**€6,203 owed · €0 recovered · 0% recovery rate · €4,628 missed · €450 over-claim risk · ~€24,812 annualized.**
- Missed = Riverside damage €1,080 + Northgate rebate €1,548 + Sunrise promo €2,000.
- **Lead with €2,628 high-confidence** (Riverside + Northgate); present the €2,000 promo as caveated upside (its contract expired 2026-02-28).
- Hero = **Meadowvale dairy reconciles to €0** once the per-case UoM (12/case) is normalized — proving there's *no* claim, not fabricating one.
- 13/13 acceptance tests pass.

## The one-liner (open and close on it)

> "I get one safe, working agent running against the real stack fast — API where it exists, computer use where it doesn't, a human gate on risk."

## Scope section — the spine (3 min)

- **Surface:** 7 deterministic tools, **exactly one write** (`submit_claim`).
- **Deliberately omitted:** no auto-submit, no tracker/ERP write-back, no opaque ML, **no fabrication** (missing GR → not-claimable; dairy → €0).
- **Why this shape:** the trust-critical path is **transparent line-math the buyer can re-check**, not LLM inference. The deterministic engine is the tool layer; the next step wraps it as an **MCP server + Claude Agent SDK** — the model orchestrates, never touches a number.
- **Guardrails:** single-entity, €-capped, **idempotent** write; **human-approval gate**; deterministic `run_id` + trace/audit.

## Demo section (3 min) — see [DEMO-SCRIPT.md](DEMO-SCRIPT.md)

Pre-flight: `rm -f out/approvals.json out/submissions.json` so the "blocked" beat fires.
Arc: `tests (13/13)` → `agent.run` (€6,203 / 0%) → MISSED (€4,628) → **dairy €0 hero** → Prime Cuts duplicate → **gate** (refuse → approve → submit → idempotent) → audit JSON.

## Deploy & handover (1 min)

- **It's already live on Duvo (Production).** Provisioned via `@duvoai/cli` as the agent *"Supplier Reconciliation & Claims Co-Pilot"* (`eb165d7e-c8aa-43d3-84ff-055fbcc961e3`), model `claude-sonnet-4-6`, with the five CSVs + email thread loaded as knowledge-base files. The local Python engine is the **deterministic, hand-checkable core**; the Duvo agent is the **hosted, schedulable** front.
- **Honest boundary:** the proof run is **identify-only** — read-only KB files in, report + draft claims out, **no live writes**. HITL gates (outbound email; tracker edits; claims > €1,000) are encoded in the AOP and bind once the write connections exist.
- **Runs without Jenny** — that's the resilience win (Feb's 2-week gap nearly closed credit windows).
- **Productionize (dashboard):** connect Google Sheets + the `claims@dailybasket.com` mailbox, promote the revision, add **Schedules** (weekly sweep Mon 07:00 Europe/Brussels + a quarter-end rebate run), re-enable the runtime HITL toggle.

## Risks & next (1 min) — name them first

1. **Rebate basis is gross PO spend; Northgate clears €50k by only €1,600.** If "net spend" means net of credits, that €1,548 could move — it's a **config flag, not a rewrite**; confirm the definition with Finance before quoting.
2. **The €2,000 Sunrise promo is for an expired contract** — flagged medium-confidence; high-confidence missed is €2,628.
3. **Multi-GRN / partial deliveries and contract-window edges** are flagged-and-lowered-confidence today, not fully modeled — first thing to harden on live exports.
- **Next two:** (a) MCP server + Agent SDK wrapper + scheduled runs; (b) wire the real claim-submission endpoint behind the existing gate, then write recovered € back to the tracker.

## Q&A — full answers in [DECISION-DEFENSE-QA.md](DECISION-DEFENSE-QA.md)

Be ready for: deterministic engine vs LLM/computer-use · worst case per call · key rotation mid-run · Cloud Run vs GKE · how you know it's right pre-go-live · what breaks at 10× · and the three finance pokes above (gross/net rebate, expired promo, the €450 dual-view).
