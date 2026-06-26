# Retail / CPG Problem Archetypes

Most operations-automation tasks in this space are one of six shapes. Identify the shape, and the approach, guardrails, and demo slice fall out. Examples are drawn from the [Duvo case study](https://claude.com/customers/duvo) (procurement, supply chain, category management for retail/CPG).

For each: **Trigger** (what the ask sounds like) · **Shape** (the pattern) · **Tool path** · **Guardrails** · **Demo slice** (smallest end-to-end) · **Metric**.

---

## 1. Cross-system reconciliation

- **Trigger:** "Our POs, the supplier portal, and SAP don't agree." / "Reconcile invoices against receipts."
- **Shape:** Read the same facts from N systems → match → diff → auto-correct the safe discrepancies, escalate the rest.
- **Tool path:** MCP for systems with APIs (ERP); computer/browser use for the portal that has none. One agent holds the cross-reference in context.
- **Guardrails:** Corrections are writes — single-record, idempotent, human-gated above a value/£ threshold. Read widely, write narrowly.
- **Demo slice:** Reconcile *one* PO across two sources, flag the discrepancy, propose the fix, pause for approval.
- **Metric:** % auto-resolved; exceptions surfaced per run; confirmation rate (Duvo: inbound delivery confirmations 52%→90%).

## 2. Monitor → decide → outreach

- **Trigger:** "Track commodity prices and start the supplier conversation when it's worth it."
- **Shape:** Continuous/scheduled read → transparent decision rule → draft outreach → send on approval.
- **Tool path:** MCP/API or scraped feeds for prices; email/MCP for outreach; a `schedule` for cadence.
- **Guardrails:** The decision must be **auditable arithmetic**, not opaque inference (the buyer has to defend it). Outreach drafts are human-approved before send.
- **Demo slice:** One SKU, detect threshold breach, build the negotiation case, draft the supplier email, stop at "send?".
- **Metric:** Savings from work that *never got done before* (Duvo/Rohlik: €1.45M annualized in week one across 120+ SKUs).

## 3. Document / email understanding → structured action

- **Trigger:** "This supplier email half-confirms the delivery and disputes a price — handle it."
- **Shape:** Messy unstructured input (email, PDF, scan) → extract to a strict schema → take the structured action / write back.
- **Tool path:** The model parses; MCP/computer use writes back to the system of record. A schema is the contract.
- **Guardrails:** Never invent fields; low-confidence extractions go to a human. Validate against the schema before any write.
- **Demo slice:** Parse one real-looking email into `{delivery_status, disputed_line, new_price}`, show the write-back it *would* make.
- **Metric:** Extraction accuracy on a small labeled set; manual-touch reduction.

## 4. Chasing / completion loops

- **Trigger:** "Nobody chases the long tail — onboarding docs, delivery confirmations, missing PODs."
- **Shape:** Track what's outstanding → follow up across channels → escalate on rules → log outcomes. The value is *persistence*, not cleverness.
- **Tool path:** MCP for status systems + email; computer use for portals; state to remember who's been chased.
- **Guardrails:** Rate-limit outreach; cap retries; escalation rules explicit; full audit of who was contacted and why.
- **Demo slice:** Take a list of 5 open items, send the right follow-up for each, escalate the one that's overdue.
- **Metric:** Coverage of the long tail (Duvo: supplier onboarding chasing −50–70%).

## 5. Setup / configuration across systems

- **Trigger:** "Set up this promotion / onboard this vendor / change this assortment" — many fields, many screens.
- **Shape:** One request → fill many fields across one or more systems → validate → write back → confirm.
- **Tool path:** Heavy on computer/browser use (these flows are usually GUI-only); MCP where a config API exists.
- **Guardrails:** Dry-run/preview before commit; field validation; idempotent so a re-run doesn't double-create.
- **Demo slice:** Configure one promotion on a mock portal end-to-end with a preview-then-confirm step.
- **Metric:** Setup time reduction (Duvo: promotional setup −65–70%).

## 6. Negotiation / contract prep + ERP write-back

- **Trigger:** "Prepare the annual supplier negotiation and write the result back."
- **Shape:** Assemble a case from data → generate a document/contract → write outcomes back to the ERP.
- **Tool path:** MCP for data + ERP write; document generation; computer use if the ERP step is GUI-only.
- **Guardrails:** Generated terms are a **draft for human sign-off**; the ERP write is gated and idempotent.
- **Demo slice:** Build a one-supplier negotiation brief + draft contract; show the gated ERP write-back.
- **Metric:** Cycle-time cut (Duvo: annual negotiations shortened ~1 month, ~80% automated).

---

## Cross-cutting truths

- **The moat is the no-API systems.** Clean integrations are easy; the value is automating the screens nobody could automate before. Show you can do both and choose well.
- **One capable agent per job** beats a relay of narrow bots — context stays intact across the whole operation.
- **Every archetype ends in a write you must make safe.** The read side degrades gracefully; the write side is single, idempotent, gated.
