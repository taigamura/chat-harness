# Sub-agent support for parallel skill execution

> GitHub issue #9 | Labels: ready-for-agent, P1 | https://github.com/taigamura/chat-harness/issues/9

## Parent

#1 Build chat-harness v1: local Qwen+MCP vault assistant

## What to build

Build `subagent.py` — the module that lets a skill spawn parallel worker agents for multi-step skills like `/autoresearch` and `/canvas`.

Implementation: `asyncio.gather` over N scoped `agent.run(prompt, tools_subset)` coroutines. Each sub-agent has its own in-memory conversation state but shares the parent's `MCPClient` pool (MCP servers are long-lived at the harness level). Sub-agents are not process-isolated — this is acceptable for v1 and matches Claude Code's Agent tool behaviour.

Reliability expectation: best-effort. `/autoresearch` and `/canvas` push Qwen past its reliable tool-loop length (~10 turns). Sub-agent failures surface visibly (exception propagated, not swallowed).

Expose a single entry point: `run_subagents(tasks: list[str], tools) -> list[str]` — takes a list of prompts, runs them concurrently, returns their responses.

## Acceptance criteria

- [ ] `run_subagents(["summarise X", "summarise Y"], tools)` runs both concurrently via `asyncio.gather`
- [ ] Each sub-agent has independent conversation state
- [ ] Sub-agents share the parent `MCPClient` pool (no duplicate server spawning)
- [ ] A sub-agent failure raises visibly rather than being silently swallowed
- [ ] `/autoresearch` can invoke sub-agents via this module (integration verified by running the skill end-to-end, even if output quality is best-effort)

## Blocked by

- #5 Agent loop: tool-call dispatch, context trimming, session logging

