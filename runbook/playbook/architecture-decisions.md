# Architecture Decisions

How to choose the shape once you know the task. Defaults are for the Claude Agent SDK + MCP + computer-use stack; the reasoning transfers.

## Tool-path decision tree

```
Is there a usable API for this system?
├─ Yes ──────────────► MCP tool (clean, fast, testable). Prefer this.
└─ No / GUI-only ────► Computer use / Playwright MCP (the screen the human uses).
                        Brittle + slow → wrap in retries/timeouts, name the risk.

Does the job span multiple systems, multiple steps, and need judgment?
└─ Yes ──────────────► One capable Agent SDK agent orchestrating the tools above.
                        Keep context in one agent; don't relay between narrow bots.

Are there many independent, parallel reads (e.g. 50 POs)?
└─ Yes ──────────────► Subagents for fan-out (isolated context), one orchestrator merges.

Is there an irreversible / high-value write?
└─ Yes ──────────────► PreToolUse human-approval gate + idempotent, single-entity write.
```

## Tool design

- **High-leverage, not thin wrappers.** A tool should advance the agent's job and return the *evidence for a decision* (human-readable: on-hand, demand, gap, price, lead time) — not raw API rows the agent must re-interpret.
- **Strict, small schemas.** Bounded ranges, `additionalProperties: false`. The schema is documentation the model reads — good schemas prevent bad calls.
- **Errors back to the model.** Tool failures return structured, readable errors (code + what to do next) so the agent can adapt, not crash.

## Guardrails checklist (apply to every build)

- [ ] Smallest safe surface; omitted capabilities listed with reasons.
- [ ] Writes are single-entity, single-action, quantity/value-capped.
- [ ] Writes are idempotent (retry/replay can't double-act).
- [ ] High-risk actions gated on a human; the decision is persisted.
- [ ] Decision logic is transparent/auditable on trust-critical paths.
- [ ] Trace (engineer) + audit (business) records, joinable by run id; no secrets logged.
- [ ] Built mock-first; demo is deterministic; assumptions written in `SPEC.md`.

## Model selection

- **Sonnet** by default — strong, fast, cost-effective for most multi-step work.
- **Opus** for browser-heavy / long-horizon runs where reasoning depth pays off (Duvo runs browser-use agents on Opus).
- For enterprise data, run under **Zero Data Retention**.

## Deployment shape (speak to it even if you don't build it live)

- **Co-locate** the agent + its MCP servers inside the **customer's cloud** near the systems of record; on GCP that's **Vertex AI** for the model + Cloud Run/GKE for the runtime.
- **Secrets** via the cloud's secret manager, mounted and hot-reloaded; the runtime authenticates via a bound service account (Workload Identity on GCP), no static keys in the image.
- **Mock → real** is a config toggle, so you demo before the customer grants production access.
- **Ownership split:** you build/promote signed, versioned images; customer IT mounts secrets and operates the tenancy; rollback is re-deploying the previous image digest.

## When to *not* automate

If the action is rare, judgment-heavy, and irreversible, the right design may be an agent that *prepares the decision* (assembles evidence, drafts the action) and hands it to a human — not one that executes. Knowing where that line is is part of the job.
