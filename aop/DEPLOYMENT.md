# Duvo Deployment Record — Supplier Reconciliation & Claims Co-Pilot

The agent is **live on Duvo** (Production), provisioned via the `@duvoai/cli` (`duvo` v1.11.0).
This file records the live IDs and the exact commands used, so the deployment is reproducible
and auditable.

## Live resources

| Resource | Value |
|---|---|
| Team | `Ari Nakos Trial Days` — `57220e7d-d3d4-45dd-8831-ae0b5c8f70dd` |
| Agent (Assignment) | **`eb165d7e-c8aa-43d3-84ff-055fbcc961e3`** — "Supplier Reconciliation & Claims Co-Pilot" |
| Live build / revision | **`27f142e4-9882-4f10-8596-e93d72f420c2`** ("v2-files-attached") — the 6 files are attached here so they land in the run sandbox. (Initial build `d928916c…` had `files: []` and the agent couldn't see the data.) |
| Model | `claude-sonnet-4-6[1m]` · Agent Memory: enabled |
| Knowledge-base files | `purchase_orders.csv`, `good_receipts.csv`, `invoices.csv`, `supplier_contracts.csv`, `supplier_claims_tracker.csv`, `email_thread.pdf` — attached via `config.data.files` (team-file IDs `<team>%2F<filename>`) |
| AOP source | [`aop/reconciliation-agent.aop.md`](./reconciliation-agent.aop.md) (the AOP loaded into the build's system input) |

## How it was provisioned (reproducible)

```bash
# 1. Auth (interactive, browser OAuth) + team
duvo login
duvo team use 57220e7d-d3d4-45dd-8831-ae0b5c8f70dd

# 2. Create the agent with the AOP
duvo agents create \
  --name "Supplier Reconciliation & Claims Co-Pilot" \
  --input "$(cat aop/reconciliation-agent.aop.md)" --json

# 3. Upload the Q1 data as knowledge-base files (presigned PUT)
for f in purchase_orders good_receipts invoices supplier_contracts supplier_claims_tracker; do
  url=$(duvo files upload-url --file-name "$f.csv" --content-type "text/csv" --json | jq -r .signedUrl)
  curl -s -X PUT -H "Content-Type: text/csv" --upload-file "data/$f.csv" "$url"
done
url=$(duvo files upload-url --file-name email_thread.pdf --content-type application/pdf --json | jq -r .signedUrl)
curl -s -X PUT -H "Content-Type: application/pdf" --upload-file data/email_thread.pdf "$url"

# 4. Run it
RUN_ID=$(duvo runs start --agent eb165d7e-c8aa-43d3-84ff-055fbcc961e3 --json | jq -r .run.id)
duvo runs get "$RUN_ID" --json
duvo runs messages "$RUN_ID"            # read the report
# HITL (when connections are live): duvo runs respond "$RUN_ID" --approve | --deny
```

## Scope of this deployment (honest boundaries)

- **Identify-only run.** OAuth connections (Google Sheets, the `claims@` mailbox, Slack) are
  created via the Duvo dashboard, not the CLI. For the proof run the agent reads the uploaded
  **read-only** knowledge-base files and produces the report + draft claims as text — it does not
  write to a live tracker or send email. This matches the SPEC's mock-first design and keeps blast
  radius at zero.
- **HITL gates** are encoded in the AOP (Tier 1 outbound email; Tier 2 tracker edits; Tier 3
  claims > €1,000). At runtime they surface as human requests answerable with
  `duvo runs respond --approve/--deny/--answer`. They only bind once the write connections exist.

## Productionization (next steps, dashboard)

1. Connect Google Sheets (source data + tracker) and the `claims@dailybasket.com` mailbox in the
   Duvo dashboard; attach them to a new revision and `duvo revisions promote`.
2. Add Schedules (`duvo agents schedules`) — weekly sweep + quarter-end rebate run — and a
   file-drop trigger for new invoice PDFs.
3. Re-enable the runtime HITL toggle so the gated writes pause for approval before going live.

## Run record

See [`run-result.md`](./run-result.md) for the captured output of run
`213ca90e-406e-467f-a0fb-265de1f2ea27`.
