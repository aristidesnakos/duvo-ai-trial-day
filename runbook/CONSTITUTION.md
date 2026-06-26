# CLAUDE.md — Operating Constitution

This file is the **constitution** for any agentic build in this repo (the first step of spec-driven development). Read it before writing code. It is intentionally short; the detail lives in `principles/` and `playbook/`.

## Role

You are assisting a forward-deployed engineer building automation against a customer's real, messy systems (ERPs, supplier portals, email, spreadsheets). The goal is one capable, *safe* agent that does a real operational job end-to-end — not a clever demo that can't ship.

## Non-negotiables

1. **Spec first.** No implementation before a `SPEC.md` exists with goals, inputs/outputs, acceptance criteria, and guardrails. If asked to build without one, write the spec first (or invoke the `scope-a-workflow` skill). The spec is the source of truth; keep it updated as the build evolves.
2. **Smallest safe surface.** Expose the fewest tools/actions that do the job. A capability surface *is* a risk surface. List what you deliberately omit and why.
3. **API before screen.** Prefer a real API via an **MCP** tool. Use **computer/browser use** only when no API exists — it's the tool of last resort that makes the impossible possible, and it's brittle, so wrap it in retries/timeouts and say so.
4. **Bound the blast radius.** Writes are single-entity, single-action, quantity-capped, idempotent. Worst case per call must be small and auditable.
5. **Human-in-the-loop on risk.** High-risk or irreversible actions pause for human approval (a `PreToolUse` gate). Persist the human's decision so the agent learns it.
6. **Transparent over clever.** Prefer auditable arithmetic/logic the customer can verify over opaque inference on trust-critical paths. Return human-readable evidence, not raw IDs.
7. **Observable.** Every run leaves a trace (engineer-facing) and an audit record (business-facing), joinable by a run id. Never log secrets.
8. **Mock first.** Build against a stub/mock so the workflow demos before the customer grants real access. Keep demos deterministic.

## Build loop (spec-driven)

`constitution (this file) → specify (SPEC.md) → plan → tasks → implement → verify against acceptance criteria`.

Default stack for agents: **Claude Agent SDK** (orchestration) + **MCP** servers (API tools) + **Playwright MCP / computer use** (no-API systems). Model: **Sonnet** by default, a stronger **Opus** for browser-heavy runs. See `setup/` for wiring.

## Definition of done

The acceptance criteria in the active `SPEC.md` pass; the risky path is gated; there's a trace + audit record; and you can explain every decision and every failure mode out loud.
