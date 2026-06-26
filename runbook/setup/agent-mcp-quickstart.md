# Agent + MCP Quickstart

A minimal Claude Agent SDK run that proves the box can (a) run an agent and (b) drive a browser through the Playwright MCP — the "computer use for the web" path. Then the shape of the *one capable agent* that uses two tools at once.

> Verified against the Python SDK's documented API (`query`, `ClaudeAgentOptions`, `mcp_servers`, `mcp__server__tool` naming). Confirm exact MCP tool names against your installed version — `npx @modelcontextprotocol/inspector` or `claude mcp` will list them.

## A. Smoke test — agent drives a browser

```python
# smoke_test.py   →   uv run python smoke_test.py
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    mcp_servers={
        # external MCP server, launched as a subprocess
        "playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]},
    },
    # Omitting allowed_tools means you'll be ASKED to approve each tool call —
    # which is the human-in-the-loop gate in its simplest form.
    # Pre-approve once you know the names, e.g.:
    # allowed_tools=["mcp__playwright__browser_navigate", "mcp__playwright__browser_snapshot"],
)

async def main():
    prompt = "Open https://example.com and tell me the page's main heading."
    async for message in query(prompt=prompt, options=options):
        print(message)

anyio.run(main)
```

If it opens the page and reports the heading, the machine is ready for real work.

## B. The shape that matters — one capable agent, two tool paths

This is the miniature of Duvo's "single agent run": the same agent uses an **API tool (MCP)** for the clean system and **browser use** for the system with no API.

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]},
        # your domain MCP server (e.g. the Korral StoreLink server) added alongside:
        "korral": {
            "command": "python3",
            "args": ["-m", "korral_mcp.server"],
            "env": {"PYTHONPATH": "src", "KORRAL_MCP_STORELINK_MODE": "mock",
                    "KORRAL_STORE_KEYS_FILE": "store_keys.json"},
        },
    },
)

prompt = (
    "Check the stock gap for SKU 8847291 at stores 47 and 102 using the korral tools. "
    "For any store short by more than 6 units, look up the supplier's portal page in the "
    "browser and confirm lead time. Summarize what you'd order — but stop and ask me "
    "before raising any replenishment order."
)
```

One agent, full context, both tool paths, and a natural stop-for-approval before the write — the whole FDE pattern on a laptop.

## C. The real human-approval gate

For production-shaped control instead of a manual prompt, pass a permission callback (or use the SDK's hooks) so a specific high-risk tool — e.g. `mcp__korral__raise_replenishment_order` — always pauses for an explicit yes:

```python
async def can_use_tool(tool_name, tool_input, context):
    if tool_name == "mcp__korral__raise_replenishment_order":
        # surface tool_input to a human; return an allow/deny decision
        ...
    return {"behavior": "allow", "updatedInput": tool_input}

# options = ClaudeAgentOptions(..., can_use_tool=can_use_tool)
```

(Confirm the exact callback/hook signature against the SDK docs for your version — the *concept* is the load-bearing part: irreversible actions never fire without a human.)

## Custom in-process tools

To expose your own logic as a tool without a separate server, use the `@tool` decorator + `create_sdk_mcp_server` from `claude_agent_sdk`, then add it to `mcp_servers`. Handy for a quick mock of a system you don't have access to yet.
