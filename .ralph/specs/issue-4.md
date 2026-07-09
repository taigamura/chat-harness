# Ollama client + Qwen tool-call parser

> GitHub issue #4 | Labels: ready-for-agent, P0 | https://github.com/taigamura/chat-harness/issues/4

## Parent

#1 Build chat-harness v1: local Qwen+MCP vault assistant

## What to build

Build `ollama.py` — the OpenAI-compat client that talks to Ollama and parses Qwen's tool-call output reliably.

The client sends streaming requests to `http://localhost:11434/v1/chat/completions`. Qwen2.5-Instruct emits tool calls in two places simultaneously: a structured `tool_calls` array and redundant `<tool_call>...</tool_call>` tokens in the content field. The parser must handle both:

1. If `tool_calls` array is present and non-empty → use it, ignore content tokens
2. If `tool_calls` is absent or empty → parse `<tool_call>JSON</tool_call>` from the content field
3. If parsing fails → retry once with a corrective message ("your last tool call did not parse, emit exactly one tool_call in this shape: ..."), then raise a visible error

Also deliver `tests/test_qwen_toolcall.py`: send a request with a dummy tool schema to Ollama, assert `tool_calls` array is present and the content parses to valid JSON. Skipped by default unless `CHAT_HARNESS_INTEGRATION=1`.

## Acceptance criteria

- [ ] `OllamaClient.chat(messages, tools)` returns a parsed response with tool calls correctly extracted
- [ ] Parser prefers `tool_calls` array; silently falls back to content token parsing
- [ ] Parse failure triggers one retry with a corrective message before raising
- [ ] Streaming tokens are yielded as they arrive (for later use by the REPL)
- [ ] `test_qwen_toolcall.py` passes with `CHAT_HARNESS_INTEGRATION=1` (requires Ollama running on Windows)
- [ ] `test_qwen_toolcall.py` is skipped (not failed) without `CHAT_HARNESS_INTEGRATION=1`

## Blocked by

- #2 Scaffold: pyproject, config, uv env, mcp.json

