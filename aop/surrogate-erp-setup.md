# Surrogate ERP Setup Runbook — Daily Basket Procurement Demo

**Purpose.** Stand up a surrogate ERP so two Duvo agents (a **reconciliation** agent and a **supplier-simulator** agent) can run a live claims-reconciliation demo against Google connections. The agent operates as **ari.nakos@duvo.ai**.

**Connections used (all created by the operator):**
| Capability | Use in demo | Access |
|---|---|---|
| Google Drive | Source CSVs + email_thread.pdf live here | read |
| Google Sheets | Live "Claims Tracker" sheet | read/write |
| Gmail | Send claim emails / read supplier replies | send/read (`gmail.modify`) |
| Human in the loop | Operator approval gate | n/a |

**Verified environment (from `duvo whoami`):**
- Profile `default`, user `ari.nakos@duvo.ai`, Auth type `OAuth`
- Team `57220e7d-d3d4-45dd-8831-ae0b5c8f70dd`
- Reconciliation agent already exists: `eb165d7e-c8aa-43d3-84ff-055fbcc961e3`
  - Revisions: `27f142e4-9882-4f10-8596-e93d72f420c2` (v2 "v2-files-attached") / `d928916c-051b-4f2f-9792-b9a25fdb2760` (v1)
  - As of writing, **no integrations are attached to either revision** — Section 5 fixes this.

**Integration catalog IDs (verified live via `duvo integrations list`):**
| Integration | integration_id | type slug | oauth_provider_key |
|---|---|---|---|
| Gmail | `1f46b0d7-f68b-4d3b-9445-aed1194044e9` | `gmail` | `google_gmail` |
| Google Drive | `5043c688-c82d-4b4f-bbec-5579b8419b05` | `googledrive` | `google_drive` |
| Google Sheets | `06974974-9122-452f-a2d1-4f23f8df50be` | `googlesheets` | `google_sheets` |
| Human in the loop | `cb2e07a5-5a9f-4ba8-bdb6-78ef93770da3` | `human-in-the-loop` | (none) |

> **CLI vs dashboard — the one rule that matters.** OAuth *integrations* (Gmail/Drive/Sheets) are **native** auth. `duvo connections create` only makes user-provided (custom MCP) connections and will **refuse** OAuth integrations. There are two supported ways to do the OAuth consent:
> - **CLI-assisted:** `duvo oauth native start <oauth_provider_key>` prints a Google consent URL; you open it in the browser, sign in as ari.nakos@duvo.ai, approve. The connection appears in `duvo connections list` afterward. **(Verified working — see Section 1.)**
> - **Dashboard:** Connections page → Add connection → pick the integration → click through Google consent. Functionally identical; the dashboard hides the URL step.
>
> Everything else (Drive upload, Sheet creation/seeding) is **dashboard / Google UI**. Attaching integrations to a revision and pinning connections is **CLI** (`revision-integrations`).

---

## 1. Create the Google connections in Duvo (OAuth)

Each Google connection is one OAuth consent as **ari.nakos@duvo.ai**. The provider argument to `oauth native start` is the **oauth_provider_key**, *not* the integration ID or type slug (verified: `gmail` 404s; `google_gmail` returns a consent URL).

### CLI path (recommended — scriptable, leaves an audit trail)

```bash
# Gmail (scope granted: gmail.modify  → read + send)
duvo oauth native start google_gmail

# Google Drive (scope: drive + drive.activity.readonly)
duvo oauth native start google_drive

# Google Sheets (scope: spreadsheets + drive)
duvo oauth native start google_sheets
```

For each command:
1. Copy the printed `authorization_url` and open it in a browser **already signed in as ari.nakos@duvo.ai** (or sign in when prompted).
2. Approve the consent screen. The browser redirects to `platform.duvo.ai/v1/oauth/callback/<provider>` and the token is stored server-side.
3. Optionally pass `--return-url <url>` to control where the browser lands after consent.

Verify all three landed:
```bash
duvo connections list          # expect Gmail, Google Drive, Google Sheets, each owned by ari.nakos@duvo.ai
duvo connections get <id>      # confirm provider + owner
```
Note the **connection IDs** that come back — you pin those in Section 5.

> **Scopes are fixed by the integration** (verified from the live consent URLs): Gmail = `gmail.modify`; Drive = `drive` + `drive.activity.readonly`; Sheets = `spreadsheets` + `drive`. You cannot narrow them at connect time.

### Dashboard path (equivalent)
Duvo dashboard → **Connections** → **Add connection** → choose **Gmail** / **Google Drive** / **Google Sheets** → complete Google consent as ari.nakos@duvo.ai. Repeat for all three. This is the official "How to Add a Connection" flow; use it if you'd rather not handle the URL by hand.

### Human-in-the-loop
No OAuth. It is a built-in (`default` auth) integration — you just **attach** it to the revision in Section 5; nothing to connect.

---

## 2. Google Drive layout (read-only source inputs)

Create one Drive folder, owned by ari.nakos@duvo.ai:

```
Daily Basket — Procurement/
├── purchase_orders.csv
├── good_receipts.csv
├── invoices.csv
├── supplier_contracts.csv
└── email_thread.pdf
```

- **How to populate (manual upload — acceptable):** open Google Drive in the browser as ari.nakos@duvo.ai → New → Folder → name it `Daily Basket — Procurement` → drag-drop the 5 files from `data/` in this repo. Keep `.csv` as-is (do **not** let Drive auto-convert to Google Sheets — uncheck "Convert uploads" in Drive settings, or upload and confirm the type stays CSV).
- **Read-only intent:** these are inputs the reconciliation agent reads, never writes. There's no Drive-level "read-only" flag needed for a single-owner demo; enforce it in the AOP (agent reads Drive, writes only the Sheet). If sharing with others, share the folder as **Viewer**.
- The four CSVs in `data/` are the source of truth: `purchase_orders.csv`, `good_receipts.csv`, `invoices.csv`, `supplier_contracts.csv`. `email_thread.pdf` is narrative context (2 pages).

---

## 3. Claims Tracker — Google Sheet schema (live, writable)

Create a Google Sheet named **`Daily Basket — Claims Tracker`** (a separate Sheet from the read-only Drive folder; this one the agent writes to). One header row, then seed rows.

### Columns

| # | Column | Type | Notes |
|---|---|---|---|
| 1 | `claim_id` | text | `CLM-0NN`. Agent-created drafts continue the sequence. |
| 2 | `date_logged` | date `YYYY-MM-DD` | Normalize legacy `DD/MM/YYYY` on seed. |
| 3 | `supplier` | text | Canonical supplier name (see Section 4). |
| 4 | `supplier_alias` | email | `ari.nakos+<slug>@duvo.ai` the agent emails (Section 4). |
| 5 | `invoice_ref` | text | `INV-NNNN` or blank. |
| 6 | `po_ref` | text | `PO-NNNN` or blank. |
| 7 | `claim_type` | text | Short claim/dispute type. |
| 8 | `claim_amount_eur` | number | EUR, blank if unquantified. |
| 9 | `status` | enum | **Controlled vocabulary below.** |
| 10 | `status_raw` | text | Original/free-text status as written by a human (audit of the messy source). |
| 11 | `evidence` | text | GRN id, note, contract clause, computation backing the claim. |
| 12 | `agent_detected` | bool | `TRUE` if the agent surfaced it; `FALSE` if human-logged. |
| 13 | `email_thread_id` | text | Gmail thread/message id of the claim email (loop-guard key, Section 6). |
| 14 | `last_action` | text | e.g. `seeded`, `email-sent 2026-06-26`, `reply-received`, `credit-confirmed`. |
| 15 | `owner` | text | Human owner (`Jenny W.`, `M. Shaw`) or `agent`. |

### Controlled status vocabulary
Normalize the messy source `status` values into exactly these. Keep the raw value in `status_raw`.

| Canonical `status` | Meaning | Seeds from raw values |
|---|---|---|
| `Open` | Logged, not yet worked | `Open`, `open` |
| `In Progress` | Being worked / chasing supplier | `in progress`, `WIP` |
| `Draft-agent` | Agent-detected, awaiting human approval before emailing | (new, agent-created) |
| `Credit-requested` | Claim email sent to supplier, awaiting reply | (new) |
| `Credit-received/Recovered` | Supplier credited / money recovered | `Paid` |
| `Closed-no-claim` | Investigated, no valid claim | (decision) |
| `Disputed` | Supplier disputes the claim | (from replies) |
| `Escalated` | Pushed to human / management | (from HITL) |
| `Pending` | Blocked on info (e.g. missing GRN) | `Pending` |

> Source statuses observed in `supplier_claims_tracker.csv`: `Open`, `in progress`, `WIP`, `open`, `Pending`, `Paid` — all mixed casing/wording. Map per the table above; never group on `status_raw`.

### Seed rows (from `data/supplier_claims_tracker.csv`, normalized)

| claim_id | date_logged | supplier | supplier_alias | invoice_ref | po_ref | claim_type | claim_amount_eur | status | status_raw | evidence | agent_detected | email_thread_id | last_action | owner |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CLM-001 | 2026-01-15 | Greenfield Farm | ari.nakos+greenfield@duvo.ai | INV-2002 | PO-1002 | Short delivery | 375 | Open | Open | 150kg short per GRN-3002 | FALSE | | seeded | Jenny W. |
| CLM-002 | 2026-01-21 | Sunrise Bakery | ari.nakos+sunrise@duvo.ai | INV-2004 | PO-1004 | Price discrepancy | 750 | In Progress | in progress | billed 0.95 vs agreed 0.80 | FALSE | | seeded | Jenny W. |
| CLM-003 | 2026-01-25 | Meadowvale Dairy | ari.nakos+meadowvale@duvo.ai | INV-2003 | PO-1003 | Price discrepancy | | In Progress | WIP | numbers look off units vs cases?? need to check w supplier | FALSE | | seeded (date 25/01/2026 normalized) | Jenny W. |
| CLM-004 | 2026-01-26 | Prime Cuts Butchers | ari.nakos+primecuts@duvo.ai | INV-2006 | PO-1006 | Overcharge | 450 | Open | Open | 0.30/kg over pricelist on chicken | FALSE | | seeded | Jenny W. |
| CLM-005 | 2026-02-02 | Sweet Treats Co | ari.nakos+sweettreats@duvo.ai | | PO-1007 | Short delivery? | | Pending | Pending | supplier says delivered full - cant find GRN, Tom looking | FALSE | | seeded | Jenny W. |
| CLM-006 | 2026-02-10 | Prime Cuts Butchers | ari.nakos+primecuts@duvo.ai | INV-2006 | | Overcharge | 450 | Open | open | pork/chicken overcharge - chase supplier (dup of CLM-004?) | FALSE | | seeded | M. Shaw |
| CLM-007 | 2025-12-20 | Riverside Beverages | ari.nakos+riverside@duvo.ai | INV-2099 | | Damaged goods | 600 | Credit-received/Recovered | Paid | Q4 claim settled - credited 18/12 | FALSE | | seeded | Jenny W. |
| CLM-008 | 2026-02-18 | Greenfield Farm | ari.nakos+greenfield@duvo.ai | | | Price query | | Open | open | Paula asked re tomato pricing - maybe not a claim | FALSE | | seeded | Jenny W. |

> CLM-006 vs CLM-004 look like a duplicate of the same Prime Cuts overcharge — leave both in to demo the agent's dedup detection. Northgate (SUP-001) and EcoPack (SUP-008) have no seed rows but keep their aliases (Section 4) for net-new agent-detected claims.

---

## 4. Supplier → alias map

Every supplier maps to a **plus-aliased** address on the operator's mailbox so all "supplier" mail routes back into ari.nakos@duvo.ai but threads stay separable (and the supplier-simulator agent can answer on each). All eight are real entries from `supplier_contracts.csv`.

| supplier_id | supplier_name (canonical) | alias address | slug |
|---|---|---|---|
| SUP-001 | Northgate Mills Ltd | ari.nakos+northgate@duvo.ai | northgate |
| SUP-002 | Greenfield Farm | ari.nakos+greenfield@duvo.ai | greenfield |
| SUP-003 | Meadowvale Dairy Ltd | ari.nakos+meadowvale@duvo.ai | meadowvale |
| SUP-004 | Sunrise Bakery | ari.nakos+sunrise@duvo.ai | sunrise |
| SUP-005 | Riverside Beverages | ari.nakos+riverside@duvo.ai | riverside |
| SUP-006 | Prime Cuts Butchers | ari.nakos+primecuts@duvo.ai | primecuts |
| SUP-007 | Sweet Treats Co | ari.nakos+sweettreats@duvo.ai | sweettreats |
| SUP-008 | EcoPack Ltd | ari.nakos+ecopack@duvo.ai | ecopack |

Plus-addressing needs no setup in Gmail — `ari.nakos+anything@duvo.ai` already delivers to ari.nakos@duvo.ai. Use Gmail filters keyed on the `+slug` (or on the subject tags in Section 6) to label/route per supplier if you want a tidy demo inbox.

---

## 5. Attach connections to an agent revision

Two layers (verified from `duvo revision-integrations --help`):
1. **Attach an integration** = add an integration *slot* to the revision (`revision-integrations attach`).
2. **Pin a connection** = bind *your specific OAuth connection* to that slot (`revision-integrations connections pin`).

Both layers are required: a slot with no pinned connection has no credentials.

> **Recommended target.** Don't mutate the existing v2 revision in place — clone it to a new revision so the demo is reproducible and the old one stays as a fallback. (`duvo revisions --help` for `create`/`clone`; mark this step as **operator's choice** — attaching directly to v2 `27f142e4-...` also works.) The commands below use a placeholder `--revision <REV>`.

```bash
AGENT=eb165d7e-c8aa-43d3-84ff-055fbcc961e3
REV=<target-revision-id>     # v2 27f142e4-9882-4f10-8596-e93d72f420c2, or a fresh clone

# 5a. Attach the four integration slots (repeat --integration; one call is fine)
duvo revision-integrations attach \
  --agent  $AGENT \
  --revision $REV \
  --integration 1f46b0d7-f68b-4d3b-9445-aed1194044e9 \  # Gmail
  --integration 5043c688-c82d-4b4f-bbec-5579b8419b05 \  # Google Drive
  --integration 06974974-9122-452f-a2d1-4f23f8df50be \  # Google Sheets
  --integration cb2e07a5-5a9f-4ba8-bdb6-78ef93770da3    # Human in the loop

# 5b. Confirm the slots exist
duvo revision-integrations list --agent $AGENT --revision $REV

# 5c. Pin YOUR connection (from `duvo connections list`, Section 1) into each Google slot.
#     --integration takes the integration ID or the slot ID from the list above.
duvo revision-integrations connections pin <gmail_connection_id> \
  --agent $AGENT --revision $REV --integration 1f46b0d7-f68b-4d3b-9445-aed1194044e9
duvo revision-integrations connections pin <drive_connection_id> \
  --agent $AGENT --revision $REV --integration 5043c688-c82d-4b4f-bbec-5579b8419b05
duvo revision-integrations connections pin <sheets_connection_id> \
  --agent $AGENT --revision $REV --integration 06974974-9122-452f-a2d1-4f23f8df50be

# 5d. Verify pins
duvo revision-integrations connections list --agent $AGENT --revision $REV --integration <integration-or-slot-id>
```

**Uncertain / verify against your CLI version:**
- Whether `attach` is idempotent if a slot already exists (re-running may error or no-op).
- Whether Human-in-the-loop (no OAuth) needs a pin at all — likely **no**; attach alone should suffice. Confirm with `revision-integrations list`.
- Exact revision clone command (`duvo revisions --help`) — naming differs by CLI version.
- For the **supplier-simulator agent**, repeat 5a–5d on its own revision; it needs Gmail (to reply as suppliers) and likely Human-in-the-loop, but **not** Drive/Sheets write.

---

## 6. Email convention + loop-guard spec

The reconciliation agent and supplier-simulator agent talk over Gmail. Without guardrails they will ping-pong forever. Spec:

### Subject tags (machine-parseable)
- Outbound claim from reconciliation agent: **`[DB-CLAIM <claim_id>] <supplier> — <claim_type>`**
  e.g. `[DB-CLAIM CLM-001] Greenfield Farm — Short delivery`
- Reply from supplier-simulator: **`[SUPPLIER-REPLY <claim_id>] ...`** (or a plain `Re:` that preserves the `[DB-CLAIM <id>]` tag).
- The `<claim_id>` in the tag is the join key back to the Claims Tracker row.

### Routing (plus-alias)
- Reconciliation agent sends each claim **to** the supplier's alias from Section 4 (`ari.nakos+<slug>@duvo.ai`), **from** ari.nakos@duvo.ai.
- Supplier-simulator agent watches for `[DB-CLAIM ...]` mail, replies **from** the matching alias.
- The `+slug` tells the simulator which supplier persona to answer as; the `[DB-CLAIM <id>]` tag tells it which dispute.

### Loop-guard (Agent Memory dedup)
- Maintain a processed-message ledger in **Agent Memory** (a memory file, e.g. `processed_message_ids.md`) keyed by Gmail `message_id`.
- **Before acting on any inbound message:** if its `message_id` is already in the ledger, **skip** (no reply, no tracker write). Otherwise process, then append the `message_id`.
- **One reply per thread:** each agent replies **at most once** per `email_thread_id`. Record `email_thread_id` on the tracker row (column 13) when the claim email is sent; the supplier-simulator answers once and stops; the reconciliation agent ingests that reply, updates the tracker, and does **not** re-email the same thread.
- **Tracker = state, not the inbox.** Drive the next action off the row's `status` + `last_action`, never off "is there unread mail." A claim in `Credit-requested` with a recorded `email_thread_id` is already sent — do not resend.
- **Human-in-the-loop gate:** agent-detected claims enter as `Draft-agent` and require operator approval (HITL) before the agent flips them to `Credit-requested` and sends. This is the hard stop that prevents autonomous mass-emailing during the demo.

---

## Quick verification checklist
- [ ] `duvo connections list` shows Gmail, Google Drive, Google Sheets owned by ari.nakos@duvo.ai
- [ ] Drive folder `Daily Basket — Procurement` has 5 files, CSVs not converted to Sheets
- [ ] `Daily Basket — Claims Tracker` Sheet exists with the 15-column header + 8 seeded rows, statuses normalized
- [ ] `duvo revision-integrations list --agent eb165d7e-... --revision <REV>` shows 4 slots
- [ ] Each Google slot has a pinned connection (`connections list` per slot)
- [ ] Supplier-simulator agent has its own Gmail (+ HITL) slots pinned
- [ ] Agent Memory has an empty `processed_message_ids` ledger to start
