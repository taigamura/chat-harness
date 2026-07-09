# Agent loop: tool-call dispatch, context trimming, session logging

> GitHub issue #5 | Labels: ready-for-agent, P0 | https://github.com/taigamura/chat-harness/issues/5

## Parent

#1 Build chat-harness v1: local Qwen+MCP vault assistant

## What to build

Build `agent.py` — the core loop that wires together the Ollama client and the MCP client into a single callable: `agent.run(prompt, tools) -> str`.

The loop:
1. Send system prompt + conversation slice to Ollama
2. Parse response for tool calls
3. Dispatch each tool call via `MCPClient.call_tool()`
4. Feed results back as `tool` messages
5. Repeat until the model responds with no tool calls
6. Return the final text response

Context trimming: the full in-memory `list[Message]` is kept intact, but each send to Ollama uses only: system prompt + last user message + last 3 tool exchanges. This mitigates Qwen's reliability degradation past ~10 turns.

Session logging: after each turn, append the full (untrimmed) message list as one JSON line to `~/.chat-harness/logs/<timestamp>.jsonl`. The log file is opened at session start and closed on exit.

## Acceptance criteria

- [ ] `agent.run(prompt, tools)` returns a string response after completing the tool-call loop
- [ ] Tool calls are dispatched via `MCPClient.call_tool()` and results fed back correctly
- [ ] Context sent to Ollama is trimmed to system prompt + last user message + last 3 tool exchanges
- [ ] Full untrimmed history is written to `~/.chat-harness/logs/<timestamp>.jsonl` each turn
- [ ] Log directory is created if it does not exist
- [ ] Per-skill `max_turns` frontmatter (if present) causes the loop to abort with a visible error when exceeded

## Blocked by

- #3 MCP client: both transports, boot, tool discovery
- #4 Ollama client + Qwen tool-call parser

