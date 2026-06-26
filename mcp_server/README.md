# Reconciliation MCP Server

Exposes the deterministic supplier-claims reconciliation engine (`../agent/`) as
callable MCP tools, so a Duvo agent can **call** for GUARANTEED arithmetic
instead of reasoning the euros. The LLM sits on top of deterministic tools and
never touches the trust-critical math: same inputs → same `run_id`, same totals,
re-checkable line-math behind every claim.

This server is a thin, **read-only** wrapper. It imports the engine's pure
analysis functions (`analyze`, `three_way_match`, `compute_entitlements`,
`period_rollup`, `build_claim_pack`) and serializes their output with the
engine's own `to_jsonable`. It never calls the engine's one write
(`submit_claim`) and never writes to `out/`. `data/` stays read-only input.

## Tools

| Tool | Signature | Returns |
|---|---|---|
| `reconcile_period` | `reconcile_period(period: str = "Q1-2026")` | The headline roll-up: `{run_id, period, rollup, claim_packs, orphan_tracker_rows}`. `rollup` has owed total, recovered, recovery rate, by-bucket (missed / logged-correct / over-claimed), over-claim risk, duplicate-billing blocked, annualized run-rate, counts. Each claim pack is `{idempotency_key, supplier_name, po_id, claim_type, eur_amount, line_math, evidence_rows, confidence, bucket}`. |
| `three_way_match` | `three_way_match(period: str = "Q1-2026")` | Raw PO→GRN→Invoice discrepancies (short-delivery / damage / price-gap / duplicate-invoice) **before** tracker reconciliation: `{period, n_claims, claims}`. |
| `compute_entitlements` | `compute_entitlements(period: str = "Q1-2026")` | Per-supplier contract entitlements (volume rebate only if the threshold is crossed; promo funding per quarter): `{period, n_claims, claims}`. |

`reconcile_period` is the one a Duvo agent normally calls. The other two are the
same engine sliced finer, for when the agent needs the raw discrepancies or just
the contract entitlements.

## Run it locally

```bash
pip install -r mcp_server/requirements.txt

# stdio transport — for a local MCP client / `mcp dev`:
python -m mcp_server.server
mcp dev mcp_server/server.py          # MCP Inspector, if the SDK CLI is installed

# Streamable HTTP transport — what Duvo requires (see Hosting below):
python -m mcp_server.server --http --host 0.0.0.0 --port 8000
```

Run from the **repo root** so the sibling `agent` package imports (the server
also inserts the repo root onto `sys.path`, so cwd is forgiving).

### Smoke test (no network, no `mcp` needed)

```bash
python -m mcp_server.smoke_test
```

Imports the engine directly, rebuilds the exact `reconcile_period` payload, and
asserts the Q1-2026 headline numbers — **owed €6,203**, recovered €0, recovery
0%, missed €4,628, over-claim risk €450, annualized €24,812. Validates the
wrapper logic even when the `mcp` package is not installed.

## Hosting (the one external dependency before registration)

> **Duvo's cloud agent needs a REACHABLE URL. `localhost` will not work.**

Duvo requires MCP's **Streamable HTTP** transport over a **public HTTPS URL**
with a trusted (non-self-signed) certificate. STDIO and the older HTTP+SSE
transport are **not** accepted. So before you can register this server, it must
be reachable on the public internet. Options:

- **Deploy to a small cloud host** (recommended for anything lasting): Cloud Run,
  AWS Lambda + API Gateway, Fly.io, a managed PaaS, or a VM/k8s — Duvo is
  host-agnostic. Run `python -m mcp_server.server --http --host 0.0.0.0 --port 8000`
  behind the platform's HTTPS termination.
- **Temporary tunnel** (fine for a demo/trial): run the server locally on `:8000`,
  then expose it with a tunnel:
  ```bash
  ngrok http 8000
  # or
  cloudflared tunnel --url http://localhost:8000
  ```
  Use the resulting `https://…` URL. The streamable-http endpoint is served at
  the `/mcp` path (e.g. `https://<your-host>/mcp`).

This hosting step is **the single external dependency** between "the code works"
(proven by the smoke test) and "Duvo can call it."

## Register it as a custom MCP connection in Duvo

Mechanism confirmed from the Duvo docs (`docs.duvo.ai/mcp/custom-mcp-servers.md`,
`.../building-mcp-servers.md`, `.../cli/managing-connections.md`):

**Web UI (simplest path):**
1. Go to the Connections page → <https://app.duvo.ai/integrations>.
2. Click **Add custom connection**.
3. Enter a recognizable name (e.g. `Reconciliation Engine`).
4. Select an authorization method — None / API key / Custom headers / OAuth
   (Duvo auto-detects Dynamic Client Registration; otherwise paste Client
   ID/Secret in Advanced and register the redirect URI it shows you).
5. Paste your **public HTTPS URL** (the `/mcp` streamable-http endpoint from
   Hosting above).
6. Click **Create**. Teammates then authenticate individually if you chose auth.

**CLI (`@duvoai/cli`):** custom MCP servers register under `integrations`, not
`connections`:
```bash
duvo integrations custom create \
  --name "Reconciliation Engine" \
  --server-url https://<your-public-host>/mcp \
  --auth-method url        # or: apikey | headers | oauth
# inspect afterwards:
duvo connections list
duvo connections get <connection-id>
# remove:
duvo integrations custom delete <custom-integration-id>
```
(`duvo connections` has `list`/`get` but no `create` for custom MCP — creation
goes through `duvo integrations custom create`.)

## How the reconciliation agent's AOP uses this

> Call `reconcile_period` for the audited euros (owed / recovered / by-bucket +
> claim packs), then do the correspondence and judgement — drafting the supplier
> email, prioritising claims, routing for human approval — on top of those
> guaranteed numbers. The agent reasons about *what to do*; it never recomputes
> the euros.
