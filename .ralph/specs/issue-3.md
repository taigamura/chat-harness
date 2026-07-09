# MCP client: both transports, boot, tool discovery

> GitHub issue #3 | Labels: ready-for-agent, P0 | https://github.com/taigamura/chat-harness/issues/3

## Parent

#1 Build chat-harness v1: local Qwen+MCP vault assistant

## What to build

Build `mcp_client.py` — the layer that reads `mcp.json`, brings up all MCP servers, discovers their tool schemas, and exposes a single unified `call_tool(name, args)` async function to the rest of the harness.

Two transport paths, selected by the `type` field in `mcp.json`:
- `"type": "sse"` → connect via SSE (obsidian-vault at `https://localhost:27124` with Bearer token auth; SSL verification disabled for localhost only)
- `"type": "stdio"` → spawn server as a subprocess using the official `mcp` Python SDK stdio client (playwright, ddg, fetch)

All server processes start at harness boot and are killed on exit. Tool schemas are discovered via `list_tools` at boot — nothing hardcoded. Adding a new server to `mcp.json` makes its tools available next session automatically.

Also deliver `tests/test_mcp_roundtrip.py`: spawn the obsidian-vault SSE server, call `list_tools`, make one tool call, assert a non-empty result. Skipped by default unless `CHAT_HARNESS_INTEGRATION=1`.

## Acceptance criteria

- [ ] `MCPClient` starts all servers from `mcp.json` on init and shuts them down cleanly on exit
- [ ] `MCPClient.list_tools()` returns tool schemas from all four servers
- [ ] `MCPClient.call_tool(name, args)` dispatches to the correct server and returns the result
- [ ] SSL verification is disabled only for the obsidian-vault SSE connection
- [ ] `test_mcp_roundtrip.py` passes with `CHAT_HARNESS_INTEGRATION=1` (requires Obsidian open on Windows)
- [ ] `test_mcp_roundtrip.py` is skipped (not failed) without `CHAT_HARNESS_INTEGRATION=1`

## Blocked by

- #2 Scaffold: pyproject, config, uv env, mcp.json

