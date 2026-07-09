# REPL + one-shot entry, Rich streaming output

> GitHub issue #6 | Labels: ready-for-agent, P0 | https://github.com/taigamura/chat-harness/issues/6

## Parent

#1 Build chat-harness v1: local Qwen+MCP vault assistant

## What to build

Build `__main__.py` — the entry point that provides both interactive REPL and one-shot modes, with Rich-rendered streaming output.

Behaviour:
- `chat-harness` (no args) → interactive REPL: prompt loop, each response streamed token-by-token, `Ctrl+D` exits
- `chat-harness --prompt "..."` → one-shot: stateless, prints response, exits

Output rendering:
- Tokens are printed as they arrive via `httpx` streaming (no buffering the full response before display)
- After streaming completes, the final response is rendered as Rich markdown (headers, bullet points, code blocks)
- No Rich Live panel — plain streaming print then Rich render

Session state is an in-memory `list[Message]`. No persistence in v1.

## Acceptance criteria

- [ ] `chat-harness` drops into an interactive prompt loop; `Ctrl+D` exits cleanly
- [ ] `chat-harness --prompt "what is 2+2"` prints a response and exits with code 0
- [ ] Streaming tokens appear incrementally in the terminal (not batched after completion)
- [ ] Final response is rendered with Rich markdown formatting
- [ ] MCP servers are started on entry and shut down cleanly on exit

## Blocked by

- #5 Agent loop: tool-call dispatch, context trimming, session logging

