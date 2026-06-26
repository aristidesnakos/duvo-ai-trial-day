# HANDOFF — Daily Basket Supplier-Claims Agent

> Status doc. Read this to resume. Working dir: this repo. Scenario period = Q1 2026 (closed); in-scenario "today" = early April 2026.

## Status: SHIPPED — MVP complete & green

A working, deterministic, dependency-free Python agent reconciles PO → Goods Receipt → Invoice + contracts, reconciles against the tracker, and answers the Finance Director's question. **13/13 acceptance criteria pass.** The five CSVs are live on disk; `email_thread.pdf` mined.

**Answer to Mark:** €6,203 owed · €0 recovered · 0% recovery rate · €4,628 missed (€2,628 high-confidence + €2,000 promo at medium confidence — contract lapses mid-quarter, see PROOF-PACK) · €450 over-claim risk · €24,812 annualized.

## The thesis

**Don't automate the spreadsheet — replace it as the source of truth.** The tracker is the failure mode (single-owner Jenny; errors; money never logged). Derive claims from ERP exports + contracts via a three-way match + contract entitlements; use the tracker only as a reconciliation target → bucket into missed / logged-correct / over-claimed / not-claimable.

## Where everything is

- **Start here:** [`README.md`](./README.md) — front door + deliverables map.
- **Run it:** `python3 -m agent.run` · tests: `python3 tests/test_acceptance.py`.
- Brief: [`PROJECT-BRIEF.md`](./PROJECT-BRIEF.md) · Spec: [`SPEC.md`](./SPEC.md) · Proof: [`PROOF-PACK.md`](./PROOF-PACK.md) · Case study: [`CASE-STUDY.md`](./CASE-STUDY.md).
- Reusable asset: [`prep/reusable-asset-claims-recovery-runbook.md`](./prep/reusable-asset-claims-recovery-runbook.md).
- Duvo platform design (AOP): [`aop/`](./aop/).
- Method followed: [`runbook/`](./runbook/) (FDE Field Kit).

## Stakeholders

- **Paula Hart** — Finance Ops Lead (sponsor).
- **Jenny Walsh** — operator; runs the spreadsheet; key-person risk (the agent runs without her).
- **Mark Bryant** — Finance Director; economic buyer; cares about "numbers that move."

## Known data traps (all handled + tested)

- **UoM normalization** — Meadowvale Dairy quotes per case (12 units/case); normalize before comparing → the "hero" claim is honestly €0.
- **No GRN → unprovable** — Sweet Treats has no goods receipt; not claimable, not fabricated.
- **Duplicate detection** — Prime Cuts €450 logged twice (CLM-004 + CLM-006).
- **Period discipline** — the one Q4 row is excluded from Q1 totals.
- **Contract validity** — Sunrise promo contract lapses mid-Q1 → promo flagged medium confidence.

## Open items pending live discovery `[confirm on day]`

Write boundary (identify-only vs submit) · tracker semantics (what "recovered" means; when credit windows close) · rebate basis (gross/net/tiered) · promo trigger + pro-rating rule · pack sizes beyond dairy · damage coding · multiple GRs per PO · real submission endpoint + auth owner.

## Next step (not built)

Wrap the deterministic engine as an MCP server + drive with a Claude Agent SDK agent (the LLM sits on top of the deterministic tools, never touches the arithmetic). Then schedule recurring runs and wire the real submission endpoint behind the existing human gate. The `aop/` design is the Duvo-platform-native target shape.
