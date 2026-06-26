# Claims-Health Digest — prevention layer (spec, not built)

> **Purpose:** stop the *same headaches recurring every quarter*. The shipped agent *recovers*
> what's owed; this is the near-free *prevention* layer that sits on top — a quarterly digest
> built entirely from data the agent already computes. Specced here so we can point to it as the
> next tangible step without spending a build cycle today.
>
> Source of every pattern below: `data/email_thread.pdf` (Jenny ⇄ Paula, 31 Mar 2026).

## The recurring patterns, in Jenny's words

| Jenny said | Pattern | Status after the build |
|---|---|---|
| *"a couple of credit windows nearly closed on us"* | claims age past the deadline | recovered, but **timing not yet watched** |
| Sunrise *"needs to check with finance… same story every quarter"* | predictable supplier stall | chased + escalated, but **re-learned every quarter** |
| Rebates *"I almost never check whether we've crossed the threshold"* | entitlements missed near the line | computed when crossed; **near-misses not surfaced** |
| Prime Cuts *"logged in a rush… in there twice"* | manual duplicate entry | ✅ **prevented** — agent derives claims; humans stop hand-logging |
| Meadowvale *"couldn't get the numbers to line up"* | UoM mismatch | ✅ **prevented** — pack-size normalized from contract notes |
| Sweet Treats *"can't find the paperwork our side"* | invoiced with no goods receipt | flagged at *claim* time; should be caught at *receiving* time |

Three are already prevented by the reframe. The digest closes the other three.

## The deliverable: a quarterly Claims-Health digest (3 sections)

1. **Claims aging + credit-window clock** — every open claim with days-to-deadline (from
   `payment_terms_days`), sorted by what closes soonest. *Directly answers "credit windows
   nearly closed."* This is the highest-€ section: it prevents loss by **timing**, not detection.
2. **Supplier reliability scorecard** — per supplier: pays-clean vs. stalls vs. disputes, and
   average days-to-credit, accumulated across quarters in Agent Memory. *Turns "same story every
   quarter" into "we know Sunrise stalls — escalate on day one."* Manage by exception.
3. **Upstream hygiene fix-list** — two recurring data gaps handed back to receiving/procurement:
   "POs invoiced with no goods receipt" (the Sweet Treats class) and "contracts with non-standard
   units" (the Meadowvale class). *Fixes the problem at the source so it stops being generated.*

## Why this is in scope, not scope creep

- **No new capability or infrastructure** — it is a *view* over outputs the agent already
  produces: the reconciliation buckets, `payment_terms_days`, the Correspondence responses, and
  `quarter_spend` / `processed_corr_ids` already in Agent Memory.
- **Ships as a section of the existing run report** — no new pipeline, no monitoring stack, no
  auto-negotiation.
- **One cycle, inside the two-cycle cap.** Recovery was the MVP; this is layer 2, deliberately
  specced not built today.

## What it would take

- **Aging clock:** sort existing open claims by `requested_at + payment_terms_days`. ~half a day.
- **Scorecard:** roll up the verdicts the supplier loop already writes, keyed by supplier across
  runs (Agent Memory already persists per-quarter state). ~half a day.
- **Hygiene list:** the agent already detects NO_GRN and non-standard UoM mid-run — surface them
  as a standing list instead of per-claim asides. ~a couple of hours.

## The framing for the room

> "Recovery gets the money back. This makes next quarter quieter — and it stops the loss that
> isn't a missed claim at all, but a missed *deadline*. It's not new machinery; it's pointing the
> data the agent already has at next quarter instead of last."
