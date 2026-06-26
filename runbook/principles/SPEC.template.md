# SPEC — <short name of the workflow>

> Copy this file to `SPEC.md` at the root of your build and fill it in *before* writing code.
> Keep it updated as the build evolves — it's the source of truth, not a throwaway.

## 1. Problem & context

One paragraph: what operational work this automates and why it's worth doing. The "abandoned work" it recovers.

## 2. User & decision

- **User:** who relies on this (role).
- **Decision/action:** the one decision or action the workflow turns on.
- **Trigger:** schedule / event / human request.

## 3. Systems of record & auth

| System | Holds | API? | Auth model | Access today? |
|---|---|---|---|---|
| e.g. SAP | POs, receipts | GUI-only | SSO | mock |
| e.g. Supplier portal | delivery status | none | per-user login | mock |

## 4. Scope

- **In scope:** the smallest path that serves the decision.
- **Out of scope / omitted capabilities:** what the agent deliberately *cannot* do, and why (this is a feature).

## 5. Tool surface

For each tool: name · purpose · inputs (typed) · output (the decision evidence it returns) · MCP or computer-use · read or write.

## 6. Data shapes

The strict schema(s) for the key inputs/outputs (e.g. the structured form a parsed email must produce).

## 7. Guardrails

- Blast radius (write is single-entity? capped?): 
- Idempotency key: 
- Human-approval gate on: 
- Transparent decision rule (state it): 
- Observability: trace + audit fields, run id: 
- Secrets handling: 

## 8. Acceptance criteria (these are your tests & demo script)

- [ ] Given … when … then … (happy path)
- [ ] An exception case is escalated, not mishandled
- [ ] A re-run with the same key does not double-act
- [ ] The risky write pauses for approval
- [ ] Every run leaves a trace + audit record

## 9. Assumptions & mocks

What you're stubbing today and the assumption behind each (revisit when real access lands).

## 10. Rollout & handoff

Where it runs, who operates it, who owns secrets, how it updates/rolls back, the next expansion.

## 11. Open questions

Things to confirm with the customer/IT before go-live.
