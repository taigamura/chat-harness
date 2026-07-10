#!/usr/bin/env bash
# Idempotent WSL setup for chat-harness
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ── Node / npm ──────────────────────────────────────────────────────────────
if ! command -v node >/dev/null 2>&1; then
  echo "[setup] Installing Node.js via nvm..."
  curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  export NVM_DIR="$HOME/.nvm"
  # shellcheck disable=SC1090
  source "$NVM_DIR/nvm.sh"
  nvm install --lts
  nvm use --lts
else
  echo "[setup] Node $(node --version) already installed — skipping"
fi

# ── uv / uvx ────────────────────────────────────────────────────────────────
if ! command -v uvx >/dev/null 2>&1; then
  echo "[setup] Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.cargo/bin:$PATH"
else
  echo "[setup] uvx $(uvx --version 2>&1 | head -1) already installed — skipping"
fi

# ── npm MCP servers ─────────────────────────────────────────────────────────
echo "[setup] Installing npm MCP server packages..."
npm install -g --prefer-offline @playwright/mcp 2>&1 | tail -5

# ── Playwright browsers ──────────────────────────────────────────────────────
echo "[setup] Installing Playwright Chromium..."
npx playwright install chromium

# ── Python deps ─────────────────────────────────────────────────────────────
echo "[setup] Installing Python dependencies via uv sync..."
cd "$REPO_DIR"
uv sync

echo ""
echo "[setup] Done. Run: bin/chat-harness --help"
