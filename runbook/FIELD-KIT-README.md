# FDE Field Kit

A portable operating system for forward-deployed engineering: clone it onto any machine and you arrive with a working method — how to scope an ambiguous customer problem, build a safe agent against messy systems, and present the result.

Built for retail/CPG operations work (the [Duvo](https://claude.com/customers/duvo) problem space: procurement, supply chain, category management across ERPs, supplier portals, email, and spreadsheets), but the method is domain-agnostic.

## Why this exists

When you're handed an unfamiliar laptop and an ambiguous task, the bottleneck isn't talent — it's having your method *with you*. This kit is that method, as version-controlled docs plus invokable Claude Code skills. The principles double as the AI's operating context, so the agent builds the way you would.

## 60-second start on a fresh machine

```bash
git clone https://github.com/USERNAME/fde-field-kit.git
cd fde-field-kit
# Open with Claude Code — CLAUDE.md primes it with the principles,
# and the skills below become invokable immediately.
claude
```

Then verify the box can run agents: follow [`setup/laptop-setup.md`](setup/laptop-setup.md) (~15 min) and [`setup/agent-mcp-quickstart.md`](setup/agent-mcp-quickstart.md).

## What's inside

| Path | Use it when |
|---|---|
| [`playbook/first-90-minutes.md`](playbook/first-90-minutes.md) | The clock starts. A timeboxed runbook: configure → scope → spec → build → demo. |
| [`playbook/problem-archetypes.md`](playbook/problem-archetypes.md) | You've heard the task. Find which retail/CPG archetype it is and how to attack it. |
| [`playbook/decomposition.md`](playbook/decomposition.md) | The ask is vague. Drive it to a plan with the decomposition frame + clarifying-question bank. |
| [`playbook/architecture-decisions.md`](playbook/architecture-decisions.md) | Choosing the shape: MCP vs computer use vs agent, guardrails, model selection. |
| [`principles/development-principles.md`](principles/development-principles.md) | The canon. Spec-driven development + the guardrails that keep an agent safe. |
| [`principles/SPEC.template.md`](principles/SPEC.template.md) | Copy this to start any build. The contract the AI and you both work from. |

## Invokable skills (Claude Code)

Open this repo with Claude Code and invoke:

- **`scope-a-workflow`** — turn a vague customer ask into a filled `SPEC.md`.
- **`spec-driven-build`** — take a `SPEC.md` from plan → tasks → implementation.
- **`fde-presentation`** — assemble the 10-minute final presentation from your work.

Skills live in [`.claude/skills/`](.claude/skills/) and load automatically when this is your working directory.

## The one-line method

> Read for the decision, write the spec, build the smallest safe slice end-to-end, reach for an API (MCP) before a screen (computer use), gate the risky write on a human, and narrate every choice.

## License

MIT — see [`LICENSE`](LICENSE). Use it, fork it, make it yours.
