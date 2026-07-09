# Scaffold: pyproject, config, uv env, mcp.json

> GitHub issue #2 | Labels: ready-for-agent, P0 | https://github.com/taigamura/chat-harness/issues/2

## Parent

#1 Build chat-harness v1: local Qwen+MCP vault assistant

## What to build

Set up the repo skeleton so every subsequent slice has a working install surface to build on. This slice produces nothing runnable yet, but after it completes a developer can clone the repo, run `wsl-setup.sh`, and have a fully configured environment with all dependencies installed.

Deliverables:
- `pyproject.toml` — deps: `mcp`, `httpx`, `click`, `pyyaml`, `rich`; managed by `uv`
- `config.yaml` — `vault_path`, `model`, `ollama_url`, `log_dir`, `skills.qwen_skip`, `skills.qwen_degraded`
- `mcp.json` — mirrors real Claude Code `settings.json` mcpServers shape: obsidian-vault as `{"type": "sse", "url": "https://localhost:27124", "headers": {"Authorization": "Bearer ..."}}`, playwright/ddg/fetch as stdio
- `install/wsl-setup.sh` — idempotent: installs Node, ensures `uvx` available, installs npm MCP servers, runs `playwright install chromium`, installs Python deps via `uv sync`
- `install/windows-launcher.bat` — `wsl -e bash -c "cd ~/chat-harness && uv run python -m chat_harness %*"`
- `install/windows-terminal-profile.json` — Windows Terminal profile that opens the REPL directly
- `bin/chat-harness` — bash shim: `exec uv run python -m chat_harness "$@"`
- `chat_harness/__init__.py`, `chat_harness/config.py` — load `config.yaml`, resolve vault path

## Acceptance criteria

- [ ] `uv sync` completes without errors from a fresh clone
- [ ] `wsl-setup.sh` is safe to re-run on an already-configured machine (no errors, no duplicate installs)
- [ ] `mcp.json` matches the real Claude Code `settings.json` mcpServers shape (SSE for obsidian-vault, stdio for the rest)
- [ ] `bin/chat-harness --help` exits without error (even though the module body is a stub)
- [ ] `windows-launcher.bat` and `windows-terminal-profile.json` exist in `install/`

## Blocked by

None — can start immediately.

