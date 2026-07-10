"""Smoke tests for the REPL (no live I/O)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from chat_harness.config import Config
from chat_harness.repl import run_repl


@pytest.fixture()
def config(tmp_path):
    return Config({"model": "test-model", "vault_path": "/tmp/vault"}, tmp_path / "c.yaml")


def _make_mcp():
    mcp = MagicMock()
    mcp.__aenter__ = AsyncMock(return_value=mcp)
    mcp.__aexit__ = AsyncMock(return_value=None)
    mcp.list_tools.return_value = []
    mcp._tool_server = {}
    return mcp


def _make_llm():
    llm = MagicMock()
    llm.__aenter__ = AsyncMock(return_value=llm)
    llm.__aexit__ = AsyncMock(return_value=None)
    return llm


def _make_agent():
    agent = MagicMock()
    agent.run = AsyncMock(return_value="answer")
    agent.clear_history = MagicMock()
    return agent


@pytest.mark.anyio
async def test_exit_command_terminates(config):
    """/exit input should cause run_repl to return cleanly."""
    mcp = _make_mcp()
    llm = _make_llm()
    agent = _make_agent()

    with (
        patch("chat_harness.repl.MCPClient", return_value=mcp),
        patch("chat_harness.repl.OllamaClient", return_value=llm),
        patch("chat_harness.repl.Agent", return_value=agent),
        patch("chat_harness.repl.Prompt.ask", side_effect=["/exit"]),
        patch("chat_harness.repl.console"),
    ):
        await run_repl(config)  # should return without raising


@pytest.mark.anyio
async def test_quit_command_terminates(config):
    mcp = _make_mcp()
    llm = _make_llm()
    agent = _make_agent()

    with (
        patch("chat_harness.repl.MCPClient", return_value=mcp),
        patch("chat_harness.repl.OllamaClient", return_value=llm),
        patch("chat_harness.repl.Agent", return_value=agent),
        patch("chat_harness.repl.Prompt.ask", side_effect=["/quit"]),
        patch("chat_harness.repl.console"),
    ):
        await run_repl(config)


@pytest.mark.anyio
async def test_banner_contains_model_name(config):
    mcp = _make_mcp()
    llm = _make_llm()
    agent = _make_agent()

    printed: list[str] = []

    from rich.panel import Panel as RichPanel

    banner_renderables: list[str] = []

    def capture_print(renderable, **kwargs):
        if isinstance(renderable, RichPanel):
            # Walk the panel's renderable tree to find text content
            import rich.text
            obj = renderable.renderable
            if isinstance(obj, rich.text.Text):
                banner_renderables.append(obj.plain)
            else:
                banner_renderables.append(str(obj))
        else:
            banner_renderables.append(str(renderable))

    with (
        patch("chat_harness.repl.MCPClient", return_value=mcp),
        patch("chat_harness.repl.OllamaClient", return_value=llm),
        patch("chat_harness.repl.Agent", return_value=agent),
        patch("chat_harness.repl.Prompt.ask", side_effect=["/exit"]),
        patch("chat_harness.repl.console") as mock_console,
    ):
        mock_console.print.side_effect = capture_print
        await run_repl(config)

    combined = " ".join(banner_renderables)
    assert "test-model" in combined


@pytest.mark.anyio
async def test_ctrl_d_exits_cleanly(config):
    mcp = _make_mcp()
    llm = _make_llm()
    agent = _make_agent()

    with (
        patch("chat_harness.repl.MCPClient", return_value=mcp),
        patch("chat_harness.repl.OllamaClient", return_value=llm),
        patch("chat_harness.repl.Agent", return_value=agent),
        patch("chat_harness.repl.Prompt.ask", side_effect=EOFError),
        patch("chat_harness.repl.console"),
    ):
        await run_repl(config)  # should not raise


@pytest.mark.anyio
async def test_clear_command_calls_agent(config):
    mcp = _make_mcp()
    llm = _make_llm()
    agent = _make_agent()

    with (
        patch("chat_harness.repl.MCPClient", return_value=mcp),
        patch("chat_harness.repl.OllamaClient", return_value=llm),
        patch("chat_harness.repl.Agent", return_value=agent),
        patch("chat_harness.repl.Prompt.ask", side_effect=["/clear", "/exit"]),
        patch("chat_harness.repl.console"),
    ):
        await run_repl(config)

    agent.clear_history.assert_called_once()
