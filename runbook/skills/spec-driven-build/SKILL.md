---
name: spec-driven-build
description: Take an approved SPEC.md from plan → tasks → implementation, building a safe agent/MCP workflow the way the constitution (CLAUDE.md) requires. Use after a spec exists and it's time to build — "implement the spec", "let's build it", "turn this into code". Enforces mock-first, smallest-safe-surface, idempotent gated writes, and trace+audit observability, checking each step against the acceptance criteria.
---

# Spec-Driven Build

Precondition: an approved `SPEC.md` exists (if not, invoke `scope-a-workflow` first). Read `CLAUDE.md` (the constitution) and `principles/development-principles.md` before starting.

## Steps

1. **Plan (the how).** From the spec, decide: tool path per system (MCP vs computer/browser use — use `playbook/architecture-decisions.md`), the orchestration (one Agent SDK agent; subagents only for parallel reads), data schemas, and the stack. Write the plan as a short section in `SPEC.md`.
2. **Tasks.** Break the plan into small, individually verifiable tasks. Order them so an end-to-end slice runs as early as possible.
3. **Implement, mock-first.** Build task by task. Stub systems you can't reach yet so the *whole* workflow runs today; record each mock in the spec's Assumptions section. API systems → MCP tools with strict small schemas returning decision evidence; no-API systems → computer/browser use wrapped in retries/timeouts.
4. **Make the write safe.** Single-entity, capped, **idempotent**, behind a `PreToolUse` human-approval gate. Persist approvals.
5. **Instrument.** Emit a trace (engineer) + audit (business) record per run, joinable by a run id. Never log secrets.
6. **Verify each step against acceptance criteria.** Run them like tests; add a tiny eval with one nasty case. Don't gold-plate past green.
7. **Run the guardrails checklist** in `playbook/architecture-decisions.md` before calling it done.

## Output

A working, demoable slice that satisfies the spec's acceptance criteria, plus an updated `SPEC.md`. Then hand off to `fde-presentation`.

> Paths above are relative to the repo root. If this skill runs from `.claude/skills/`, the repo root is two levels up.
