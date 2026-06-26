# Duvo Deployment Record — Daily Basket Claims, live closed loop

Provisioned on Duvo (Production) via the `@duvoai/cli` (`duvo` v1.11.0). This records the live IDs,
the exact wiring, and the verified closed-loop result, so the deployment is reproducible and auditable.

> **"Sandbox" = the trial team `Ari Nakos Trial Days`, not a customer's production tenant.** The brief
> says "ship on the Duvo sandbox"; here that is a dedicated trial team on the Duvo Production platform.
> No real Daily Basket data, no real suppliers, no real email — the suppliers are `SupplierLedger` rows
> and the ERP is a surrogate Google Sheet. Production-platform, sandbox-scope.

> **Architecture note.** The working design is a **two-agent closed loop over a single Google Sheets
> workbook** (the surrogate ERP). An earlier approach uploaded the CSVs as knowledge-base files
> (`config.data.files`) — it is **superseded**: those files did not mount in the run sandbox, so the
> agent couldn't read them (captured in [`run-result.md`](./run-result.md)). Data now lives in the
> Sheet; the agents reach it through the Google Sheets connection. Design + gaps:
> [`SIMULATION-DESIGN.md`](./SIMULATION-DESIGN.md).

## Live resources

| Resource | Value |
|---|---|
| Team | `Ari Nakos Trial Days` — `57220e7d-d3d4-45dd-8831-ae0b5c8f70dd` |
| **Reconciliation agent** (plays Daily Basket / Jenny) | `eb165d7e-c8aa-43d3-84ff-055fbcc961e3` — live build `bb58ef3f-…` ("v4-duplicate-invoice"; adds duplicate-invoice + dangling-reference handling). The closed-loop run record below was captured on the predecessor build `b3b95613-…` ("v3-sheets-bus"). |
| **Supplier Simulator** (plays the 8 suppliers) | `e6e3b6e5-0037-4f88-a774-18abaa52dc0b` — live build `4f05ff4d-…` ("v2-ledger-reasoning") |
| Model | `claude-sonnet-4-6[1m]` · Agent Memory: enabled |
| Connection | Google Sheets — `0542cc25-1dc9-447b-8471-401834d77677` ("Google Sheets - ari.nakos@duvo.ai"), scopes `spreadsheets`+`drive` |
| Integration (slot) | `googlesheets` — `06974974-9122-452f-a2d1-4f23f8df50be` |
| Workbook ("surrogate ERP") | spreadsheet `1GeJpvll8va5_KJE8BlbC8EBAwbdAmFoUZY15vJ9ya-g` — "Daily Basket - Surrogate ERP" |
| Tabs | `PurchaseOrders · GoodReceipts · Invoices · Contracts` (source, read-only) · `ClaimsTracker` (grocer R/W) · `SupplierLedger` (supplier's private books, simulator-only) · `Correspondence` (shared message bus) |
| AOPs | recon: [`reconciliation-agent.aop.md`](./reconciliation-agent.aop.md) · sim: [`supplier-simulator.aop.txt`](./supplier-simulator.aop.txt) · ledger data: [`supplier-ledger.md`](./supplier-ledger.md). The exact deployed AOP text is held in the live Duvo build (above). |

## How it was wired (reproducible)

```bash
# 1. Auth + team
duvo login                                            # browser OAuth as ari.nakos@duvo.ai
duvo team use 57220e7d-d3d4-45dd-8831-ae0b5c8f70dd

# 2. Connect Google Sheets (native OAuth; force the work account)
duvo oauth native start google_sheets                 # open URL, add &login_hint=ari.nakos@duvo.ai
duvo connections list --json                          # -> connection 0542cc25-...

# 3. Create the reconciliation agent + attach/pin the Sheets connection to a revision
duvo agents create --name "Supplier Reconciliation & Claims Co-Pilot" \
  --input "$(cat aop/reconciliation-agent.aop.md)" --json         # -> agent eb165d7e-...
duvo revisions create --agent eb165d7e-... --name v3-sheets-bus --config-file <config>.json
duvo revision-integrations attach        --agent eb165d7e-... --revision <rev> --integration 06974974-...
duvo revision-integrations connections pin 0542cc25-... --agent eb165d7e-... --revision <rev> --integration 06974974-...
duvo revisions promote <rev>

# 4. Same for the Supplier Simulator agent
duvo agents create --name "Supplier Simulator (Daily Basket)" \
  --input "$(cat aop/supplier-simulator.aop.txt)" --json          # -> agent e6e3b6e5-...
#   (revision + attach + pin + promote, identical pattern)

# 5. Seed the workbook (one setup run creates + populates the 6 tabs; a second adds SupplierLedger)
duvo runs start --agent eb165d7e-... --message "<seed message with the CSV blocks>"

# 6. Run the closed loop (turn-taking; in production this is a Status-Change trigger / Queue)
duvo runs start  --agent eb165d7e-... --message "reconcile Q1 2026 + raise claims to Correspondence"
duvo runs respond <run> --approve                     # one HITL gate: Tier-2 closes + Tier-3 >EUR1k claims
duvo runs start  --agent e6e3b6e5-... --message "respond to awaiting_reply rows from your ledger"
duvo runs start  --agent eb165d7e-... --message "process replies; follow up on stalls; report"
# ...follow-up cycle for the Sunrise stall, then a final resolve + read-back.
```

## Closed-loop run record (Q1 2026, verified)

| Run | Agent | ID | Outcome |
|---|---|---|---|
| Seed workbook (6 tabs) | recon | `747b7dd1-…` | workbook created + populated |
| Seed SupplierLedger | recon | `f6d5e501-…` | supplier's private books added |
| Reconcile + raise claims | recon | `286542a3-…` | matched oracle to the cent; gated; 6 claims raised |
| Supplier responses | sim | `e072ab4f-…` | 4 credit_full, 1 stall, 1 credit_partial — from ledger |
| Resolve + follow-up | recon | `665f01ab-…` | banked credits; posted CORR-007 follow-up |
| Sunrise concede | sim | `663b3c61-…` | stall → credit_full €750 |
| Final resolve | recon | `846cf69e-…` | banked €750 |
| Read-back (verify) | recon | `eb79ecd1-…` | authoritative final state |

**Verified result:** €6,203 owed → **€5,536 recovered = 89.2%**, gap €667 (Sunrise promo March portion,
contract lapsed 2026-02-28). Correctly not chased: €450 duplicate (CLM-006 voided), Meadowvale false
positive (closed), Sweet Treats unprovable (closed). Full per-claim table in [`../PROOF-PACK.md`](../PROOF-PACK.md).

## Scope & honest boundaries

- **AOP-only.** The reconciliation, gating, correspondence, and resolution all ran from the agents'
  AOPs + the Sheets connection — no custom code. The euro arithmetic was *reasoned* and matched the
  deterministic engine (`agent/`) exactly; for production-grade audit, expose that engine as an
  MCP/skill so the math is guaranteed, not reasoned.
- **Turn-taking was manual** (sequential `runs start` + one approval). Production replaces this with a
  Status-Change trigger or a Queue so the loop self-advances.
- **Safety:** no real email; suppliers exist only as `SupplierLedger` rows + `Correspondence` threads;
  source tabs are read-only to the grocer; the simulator never reads the grocer's books.
