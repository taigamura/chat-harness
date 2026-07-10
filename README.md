# chat-harness

Local Qwen+MCP vault assistant running on WSL2. Talks to a local Ollama model and
connects to Obsidian, Playwright, DuckDuckGo, and web-fetch via MCP.

---

## Prerequisites

| Tool | Why |
|---|---|
| WSL2 (Ubuntu recommended) | Runtime environment |
| [Ollama](https://ollama.com/download) installed on Windows | Serves the Qwen model |
| [Obsidian](https://obsidian.md) + [Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api) | Vault MCP server |

---

## 1 — Pull the Qwen model in Ollama

Open PowerShell (Windows side) and run:

```powershell
ollama pull qwen2.5:14b-instruct-q4_K_M
```

Verify it's running and reachable from WSL:

```bash
curl http://localhost:11434/api/tags
```

---

## 2 — Clone the repo (WSL)

```bash
git clone https://github.com/YOUR_USER/chat-harness.git ~/chat-harness
cd ~/chat-harness
```

---

## 3 — Run the one-shot setup script

```bash
bash install/wsl-setup.sh
```

This script is idempotent — safe to re-run. It installs:

- Node.js via nvm (skipped if already present)
- `uv` / `uvx` (skipped if already present)
- npm MCP server packages: `@playwright/mcp`
- Python MCP server packages via uvx: `duckduckgo-mcp-server`, `mcp-server-fetch`
- Playwright Chromium browser
- Python dependencies via `uv sync`

---

## 4 — Configure config.yaml

Edit [config.yaml](config.yaml) to match your machine:

```yaml
vault_path: ~/Documents/ObsidianVault   # path to your Obsidian vault inside WSL
model: qwen2.5:14b-instruct-q4_K_M      # must match the name pulled in step 1
ollama_url: http://localhost:11434       # default; change only if Ollama is on another port
log_dir: ~/.chat-harness/logs
```

---

## 5 — Configure the Obsidian MCP token

1. In Obsidian, open **Settings → Local REST API** and copy the API key.
2. Edit [mcp.json](mcp.json) and replace `YOUR_OBSIDIAN_LOCAL_REST_TOKEN`:

```json
"obsidian-vault": {
  "type": "sse",
  "url": "https://localhost:27124",
  "headers": {
    "Authorization": "Bearer <paste-your-token-here>"
  }
}
```

> The Obsidian Local REST API plugin uses a self-signed cert on localhost; the MCP
> client disables certificate verification automatically for `localhost` addresses.

---

## 6 — Verify the install

```bash
bin/chat-harness --help
bin/chat-harness --version
```

You should see the version string and the help text without errors.

---

## Optional — Windows Terminal shortcut

Copy the profile snippet from [install/windows-terminal-profile.json](install/windows-terminal-profile.json)
into your Windows Terminal `settings.json` under the `profiles.list` array. It adds a
"chat-harness" tab that drops straight into the harness from WSL.

A convenience launcher for batch scripts is at [install/windows-launcher.bat](install/windows-launcher.bat).

---

## Running tests

```bash
uv run pytest
```

---

## Troubleshooting

**`ollama: connection refused`** — make sure Ollama is running on Windows and that
`OLLAMA_HOST=0.0.0.0` is set so WSL can reach it (Ollama Settings → enable for all interfaces, or set the env var before starting).

**MCP server warning on startup** — a server that fails to connect prints a warning
but does not abort the harness; the remaining servers continue normally.

**Wrong vault path** — `vault_path` in `config.yaml` must be the WSL path, not the
Windows path (e.g. `/mnt/c/Users/you/Documents/ObsidianVault`, not `C:\Users\...`).
