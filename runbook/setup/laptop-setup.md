# Laptop Setup (~15 minutes on a fresh machine)

The goal: get from a bare laptop to "an agent runs and can drive a browser and call an MCP tool." Run top to bottom; skip what's already installed.

## 0. Prerequisites

- **git**, **Node.js 18+**, **Python 3.11+**. Quick installs:
  - Node via [nvm](https://github.com/nvm-sh/nvm): `nvm install --lts`
  - Python via [uv](https://github.com/astral-sh/uv): `curl -LsSf https://astral.sh/uv/install.sh | sh`

## 1. Claude Code

```bash
npm install -g @anthropic-ai/claude-code
claude            # first run walks through auth
```

Authenticate either with an Anthropic API key or, for enterprise/GCP, via **Vertex AI**:

```bash
# API key
export ANTHROPIC_API_KEY=sk-ant-...

# OR Vertex AI on GCP (values per your project)
export CLAUDE_CODE_USE_VERTEX=1
export CLOUD_ML_REGION=europe-west1
export ANTHROPIC_VERTEX_PROJECT_ID=your-gcp-project
gcloud auth application-default login
```

(Confirm exact Vertex env names against the current Claude Code docs.)

## 2. Agent SDK

```bash
# Python
uv pip install claude-agent-sdk
# or Node
npm install @anthropic-ai/claude-agent-sdk
```

## 3. MCP tools

```bash
# Browser automation (the "computer use for the web" path)
claude mcp add playwright npx @playwright/mcp@latest

# Inspect/poke any MCP server by hand
npx @modelcontextprotocol/inspector
```

To add a custom MCP server (e.g. the Korral StoreLink server): `claude mcp add korral <command> <args>` or edit `~/.claude.json`.

## 4. Activate this kit's skills

This repo ships skills under `skills/` for portability. Make them invokable by linking them into the project's skills directory:

```bash
mkdir -p .claude/skills
ln -s ../../skills/scope-a-workflow .claude/skills/scope-a-workflow
ln -s ../../skills/spec-driven-build .claude/skills/spec-driven-build
ln -s ../../skills/fde-presentation .claude/skills/fde-presentation
```

(Or copy them. On your own machine `.claude/skills/` is writable; some managed sessions protect it.)

## 5. Verify

```bash
claude mcp list          # playwright (and any others) should appear
```

Then run the smoke test in [`agent-mcp-quickstart.md`](agent-mcp-quickstart.md). If the agent opens a page and reports back, the box is ready.

## Safety on a borrowed machine

- Put keys in environment variables or a local `.env` (git-ignored) — never in code or commits.
- Assume the machine is not yours: don't paste real customer data into practice runs; prefer Zero Data Retention for any enterprise data.
