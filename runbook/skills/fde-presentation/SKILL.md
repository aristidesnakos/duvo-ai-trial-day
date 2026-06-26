---
name: fde-presentation
description: Assemble and rehearse the ~10-minute final presentation of a forward-deployed build for a customer/team review. Use when the build is done and it's time to present, demo, or hand off — "build the presentation", "how do I present this", "prep the demo", "walk them through it". Produces the problem→scope→demo→deploy→risks structure, the engineer-and-consultant framing, and a decision-defense Q&A.
---

# FDE Presentation

Goal: a tight 10-minute talk that shows you can build *and* hold the customer conversation. They grade engineer **and** consultant — clarity, ownership, and customer empathy count as much as the code.

## Gather

Pull from `SPEC.md` and the build: the one-sentence problem, the scope decisions (incl. what you omitted and why), the working demo, the deploy/handover story, and the known risks.

## Structure (≈10 min)

1. **Problem (1 min)** — the customer workflow in one sentence and the "abandoned work" it recovers.
2. **Scope & decisions (3 min)** — the tool surface; what you exposed vs. deliberately omitted; MCP-vs-computer-use choices; the guardrails (blast radius, idempotency, human gate). This is where you win or lose.
3. **Demo (3 min)** — run the slice live: trigger → the agent working → the human-approval gate → the audit record. Have a recording/screenshots as fallback.
4. **Deploy & handover (1–2 min)** — where it runs in the customer's cloud (GCP/Vertex, co-located, Secret Manager), the ownership split, rollback.
5. **Risks & next (1–2 min)** — known weaknesses (name them honestly) + the next two expansions.

## Framing

- Open or close with the 60-second **"why I want to be deployed at a customer"** narrative: discovery → prototype → rollout → measurement, owning the outcome.
- Lead the value line: *"I get one safe, working agent running against the real stack fast — API where it exists, computer use where it doesn't, a human gate on risk."*

## Decision-defense Q&A (prepare answers)

Anticipate and have crisp answers for: Why MCP vs computer use here? · What's the worst a confused agent can do per call? · How does a key rotation mid-run behave? · Cloud Run or GKE, and why? · How do you know it does the right thing before go-live? · What breaks first at 10× volume?

## Output

A slide outline or talk track (offer a `.pptx` or a simple markdown/HTML deck), plus a one-page Q&A sheet. Rehearse once end-to-end and time it.
