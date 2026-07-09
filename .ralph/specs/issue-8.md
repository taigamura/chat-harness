# Task tracking: TODO.md read/write tool

> GitHub issue #8 | Labels: ready-for-agent, P1 | https://github.com/taigamura/chat-harness/issues/8

## Parent

#1 Build chat-harness v1: local Qwen+MCP vault assistant

## What to build

Build `tasks.py` — a local tool that lets the agent read and write `TODO.md` in the repo root during a session. This gives the harness the same TaskCreate pattern Claude Code uses for managing multi-step work.

`tasks.py` exposes two operations registered as local tools (alongside MCP tools in the agent loop):
- `task_list` → read current `TODO.md` contents
- `task_append(text)` → append a line to `TODO.md`

Pure file I/O, no vault or MCP dependency. `TODO.md` is created if it does not exist.

## Acceptance criteria

- [ ] `task_list` returns the contents of `TODO.md` (empty string if file doesn't exist)
- [ ] `task_append("foo")` appends a line to `TODO.md` and persists it
- [ ] Both tools are registered in the agent loop and callable by Qwen as tool calls
- [ ] `TODO.md` lives in the harness repo root (CWD), not in the vault

## Blocked by

- #5 Agent loop: tool-call dispatch, context trimming, session logging

