# Decomposition — Turning Fog Into a Plan

The defining FDE skill (and the famously hard part of a Palantir-style loop) is decomposing an ambiguous problem out loud. They watch *how you get to a plan*, not whether you reach a "right" answer. Drive the conversation; don't wait to be steered.

## The frame (memorize)

1. **User & decision** — Who is the user, and what decision or action are they trying to make?
2. **System of record** — Where does the truth live? What's the auth model to reach it?
3. **Smallest safe surface** — What's the least the agent must be able to do to serve that decision?
4. **What can go wrong** — Blast radius, failure modes, the irreversible step.
5. **How I'd know it worked** — The metric / acceptance test.
6. **Handoff & next** — What do I deliver, and what's the obvious next expansion?

Say each step as you reason through it. Then write it into `SPEC.md`.

## Clarifying-question bank

Ask 3–5 of these early — pick the ones that most reduce uncertainty.

**The decision**
- What happens today, by hand, and who does it?
- What's the trigger — a schedule, an event, a person asking?
- What's the single most valuable outcome if this works?

**Data & systems**
- Which systems hold the data? Which have APIs, which are screens-only?
- Is there a sandbox/test instance, or only production?
- What does a real example record/email/file look like? (Ask for one.)

**Auth & access**
- How do we authenticate to each system? SSO, per-user, service account, rotating keys?
- What can I get access to *today* vs. what must be mocked?

**Volume & exceptions**
- How many items per run/day? How spiky?
- What's a normal case vs. an exception, and who handles exceptions now?
- What's the rule for "escalate to a human" vs. "just fix it"?

**Risk & success**
- Which actions are irreversible or high-value? (These get the human gate.)
- How will we measure success in week one?
- What would make this *unsafe* to turn on?

**Handoff**
- Who operates this after I leave? Who owns the secrets and the runtime?

## Drive-the-conversation tips

- **Restate before you solve.** "So the real job is X, and the risky part is Y — is that right?" earns trust and catches misframing.
- **Name assumptions explicitly.** "I'll assume the portal has no API and mock it — flag me if that's wrong."
- **Timebox aloud.** "In the next hour I'll get one path working end-to-end on a mock; access to the real system can come after."
- **Bias to a concrete slice.** Vague discussions converge fast once you propose the smallest real example.

## The anti-pattern

Jumping to a solution before clarifying the decision and the system of record. If you catch yourself designing tools before you've named the *one decision* and *where the truth lives*, stop and back up to step 1.
