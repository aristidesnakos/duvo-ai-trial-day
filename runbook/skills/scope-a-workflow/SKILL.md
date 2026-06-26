---
name: scope-a-workflow
description: Turn a vague customer ask into a filled SPEC.md before any code is written. Use at the start of any automation task — when the requirement is ambiguous, when you've just been handed a problem, or when someone says "can you automate X". Drives clarifying questions, finds the system of record and auth model, defines the smallest safe tool surface and acceptance criteria. Trigger on "scope this", "what's the spec", "help me figure out what to build", or a fresh underspecified task.
---

# Scope a Workflow → SPEC.md

Goal: produce a tight `SPEC.md` (from `principles/SPEC.template.md`) that becomes the contract for the build. Do **not** write implementation code in this skill.

## Steps

1. **Restate in one sentence.** "The user is a ___ who needs to ___ so they can ___." Confirm it with the requester.
2. **Run the decomposition frame** (`playbook/decomposition.md`): user & decision → system of record → smallest safe surface → what can go wrong → success metric → handoff. Reason out loud.
3. **Ask 3–5 clarifying questions** from the bank in `playbook/decomposition.md`. Prioritize: where the truth lives, the auth model, what's accessible today vs. must be mocked, the irreversible action, the week-one metric. Ask for a real example record/email/file.
4. **Classify the archetype** using `playbook/problem-archetypes.md` and note the implied tool path and guardrails.
5. **Fill the template.** Complete every section of `SPEC.template.md`. Be explicit about out-of-scope / omitted capabilities and about what you're mocking.
6. **Make acceptance criteria testable** — each one a given/when/then you could demo. These are your demo script.
7. **Read it back.** Summarize the spec to the requester in 5 lines and get a thumbs-up before building.

## Output

A saved `SPEC.md` and a 5-line verbal summary. Then hand off to the `spec-driven-build` skill.

> Paths above are relative to the repo root. If this skill runs from `.claude/skills/`, the repo root is two levels up.
