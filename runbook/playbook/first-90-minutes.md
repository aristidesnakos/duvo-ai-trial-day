# The First 90 Minutes (and the hours after)

A timeboxed runbook for when the clock starts and you've been handed a machine and an ambiguous task. Adjust the clock to the day's length; the *order* is the point.

## T+0:00 → 0:15 — Make the machine work

- Run [`../setup/laptop-setup.md`](../setup/laptop-setup.md). Get Claude Code, the Agent SDK, and the Playwright MCP installed and a key set.
- `git clone` this kit and open it with Claude Code so `CLAUDE.md` and the skills load.
- Verify with [`../setup/agent-mcp-quickstart.md`](../setup/agent-mcp-quickstart.md): one agent call that uses one MCP tool. If that runs, the box is good.

## T+0:15 → 0:35 — Scope (don't build yet)

- Restate the task in **one sentence**: *"The user is a ____ who needs to ____ so they can ____."*
- Run the decomposition frame in [`decomposition.md`](decomposition.md) **out loud**. Ask clarifying questions early; silence reads as confusion, questions read as competence.
- Pin three things before anything else: the **system(s) of record**, the **auth model**, and the **one decision** the workflow turns on.

## T+0:35 → 0:50 — Write the spec

- Copy [`../principles/SPEC.template.md`](../principles/SPEC.template.md) to `SPEC.md` (or invoke the **`scope-a-workflow`** skill to fill it from your notes).
- Nail the **acceptance criteria** and **guardrails**. This is the contract you'll demo against.
- Read it back to whoever gave you the task. Cheap to fix scope now; expensive later.

## T+0:50 → 2:30 — Build the smallest end-to-end slice

- Match the task to a pattern in [`problem-archetypes.md`](problem-archetypes.md); decide the shape with [`architecture-decisions.md`](architecture-decisions.md).
- **Mock first.** Stub the systems you don't have access to yet so the whole workflow runs today. Note each assumption in `SPEC.md`.
- Build **one capable agent** that does the job once, deterministically. API systems via MCP; no-API systems via computer/browser use. Don't widen scope — make one path work.
- Invoke **`spec-driven-build`** to go plan → tasks → implement against the spec.

## T+2:30 → 3:30 — Harden the risky path

- Put the **human-approval gate** before the irreversible write; make writes **idempotent**.
- Add the **trace + audit** records. Handle the one or two failure modes most likely to happen live (lost auth, a flaky page, a missing record).
- Re-run against the acceptance criteria. Green = done; don't gold-plate.

## Final 30–45 min — Prepare the demo

- Invoke **`fde-presentation`** to assemble the 10-minute talk: problem → scope & decisions → live demo → deploy/handover → risks & next.
- Dry-run the demo once. Have a recording or screenshots as a fallback if the live run flakes.

## Field rules

- **Timebox ruthlessly.** A small thing that works and is explained beats an ambitious thing that half-works.
- **Blocked on access? Mock it, note the assumption, move on.** Never burn 40 minutes on a credential.
- **Narrate.** They're scoring how you think as much as what you ship.
- **Reach for an API before a screen.** Saying *why* you chose MCP vs computer use is a senior signal.
