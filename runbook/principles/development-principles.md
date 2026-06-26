# Development Principles

The canon that drives solid, shippable agentic software. These double as the AI's operating context (see [`../CLAUDE.md`](../CLAUDE.md)) — write them down so the agent builds the way you would.

## Part 1 — Spec-Driven Development (SDD)

**The idea:** write a structured, versioned spec *before* invoking the agent. The spec — goals, constraints, interfaces, acceptance criteria — becomes the **source of truth** the AI and you both build, test, and validate against. By 2026 every major tool ships an SDD flavor (GitHub [Spec Kit](https://github.com/github/spec-kit), Kiro, Claude Code, Cursor, OpenSpec). Teams report far fewer "regenerate from scratch" cycles than ad-hoc prompting.

**The flow** (Spec Kit's, lightly adapted):

1. **Constitution** — the durable rules of how we build (this kit's `CLAUDE.md`). Set once, reused.
2. **Specify** — the *what* and *why* for this task: users, decision, inputs/outputs, acceptance criteria, guardrails. Not the *how*. → `SPEC.md` from [`SPEC.template.md`](SPEC.template.md).
3. **Plan** — the *how*: architecture, tool path (MCP vs computer use), data shapes, stack.
4. **Tasks** — slice the plan into small, verifiable units.
5. **Implement** — build task by task; check each against the spec.

**Discipline:**

- **Spec-first, spec-anchored.** Keep the spec after the build and update it as reality changes — it stays the source of truth, not a throwaway.
- **The spec is the contract you demo against.** Your acceptance criteria *are* your demo script.
- **A good spec is small.** If it's longer than the code will be, you're over-specifying.

Your `duvo-assessment/IMPLEMENTATION_GOALS.md` is a working example: numbered goals, each with explicit acceptance criteria and non-goals. Reuse that shape.

## Part 2 — The guardrails canon

These keep an autonomous agent safe against the threat model of *a capable but possibly-confused agent acting on real systems*.

1. **Smallest safe surface.** Expose the fewest actions that do the job; a capability surface is a risk surface. Always list what you omit and why.
2. **API before screen.** Prefer an MCP tool over computer/browser use; the screen is the last resort that's brittle and slow. Choosing correctly — and saying why — is the senior signal.
3. **Bounded blast radius.** Writes are single-entity, single-action, quantity/value-capped. Worst case per call is small and auditable.
4. **Idempotency.** Retries and mid-flight failures must not double-act. Same key → same result, flagged as a replay.
5. **Human-in-the-loop on risk.** Irreversible/high-value actions pause for approval; persist the human's decision so the system accumulates judgment.
6. **Transparent over clever.** On trust-critical paths, prefer auditable logic the customer can verify over opaque inference. Return human-readable evidence, not raw IDs.
7. **Two-audience observability.** An engineer-facing trace (durations, retries, error codes) and a business-facing audit (who/what/why), joinable by a run id. Never log secrets.
8. **Mock-first, deterministic demos.** Build against stubs so the workflow demos before real access exists; keep demo data deterministic.
9. **Fail loud, fail safe.** Prefer a clear, structured error over a silent fallback. Errors return to the model so it can adapt.

## Part 3 — Verify like it's going to production

- **Acceptance criteria are tests.** Re-run them; green means done.
- **A tiny eval beats vibes.** A handful of realistic cases (including a nasty one) tells you more than one happy-path run.
- **Probe the seams.** The bugs live where systems meet: stale reads between two calls, auth that rotated mid-run, a non-serializable value at the protocol edge, unbounded free-text input.
- **Name the failure modes you didn't fix.** Listing known weaknesses is a strength in a review, not a liability.
