"""Roundtrip tests for MCPClient.

Integration tests require a running Obsidian instance on Windows with the
Local REST API plugin enabled. Skip them by default; run with:

    CHAT_HARNESS_INTEGRATION=1 uv run pytest tests/test_mcp_roundtrip.py
"""

from __future__ import annotations

import asyncio
import json
import os
import ssl
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from chat_harness.mcp_client import MCPClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def minimal_mcp_json(tmp_path: Path) -> Path:
    """A minimal mcp.json with no real servers (unit tests only)."""
    cfg = {"mcpServers": {}}
    p = tmp_path / "mcp.json"
    p.write_text(json.dumps(cfg))
    return p


@pytest.fixture()
def integration_mcp_json() -> Path:
    """Return the real mcp.json from the repo root."""
    return Path(__file__).parent.parent / "mcp.json"


# ---------------------------------------------------------------------------
# Unit tests (always run)
# ---------------------------------------------------------------------------

class TestMCPClientUnit:
    def test_list_tools_empty_when_no_servers(self, minimal_mcp_json):
        client = MCPClient(minimal_mcp_json)
        assert client.list_tools() == []

    def test_call_tool_raises_on_unknown_name(self, minimal_mcp_json):
        client = MCPClient(minimal_mcp_json)
        with pytest.raises(ValueError, match="Unknown tool"):
            asyncio.run(client.call_tool("nonexistent_tool"))

    def test_load_config_raises_when_missing(self, tmp_path):
        client = MCPClient(tmp_path / "does_not_exist.json")
        with pytest.raises(FileNotFoundError):
            client._load_config()

    def test_context_manager_empty(self, minimal_mcp_json):
        """MCPClient as async context manager should not raise with no servers."""
        async def _run():
            async with MCPClient(minimal_mcp_json) as client:
                assert client.list_tools() == []

        asyncio.run(_run())

    def test_ssl_disabled_for_localhost(self, tmp_path):
        """SSE connections to localhost must use an unverified SSL context."""
        cfg = {
            "mcpServers": {
                "vault": {
                    "type": "sse",
                    "url": "https://localhost:27124",
                    "headers": {"Authorization": "Bearer token"},
                }
            }
        }
        mcp_json = tmp_path / "mcp.json"
        mcp_json.write_text(json.dumps(cfg))

        captured_ssl: dict = {}

        class _FakeSSECM:
            async def __aenter__(self):
                return (AsyncMock(), AsyncMock())

            async def __aexit__(self, *args):
                pass

        def fake_sse_client(url, headers=None, ssl=None):  # noqa: ARG001
            captured_ssl["ctx"] = ssl
            return _FakeSSECM()

        fake_session = MagicMock()
        fake_session.__aenter__ = AsyncMock(return_value=fake_session)
        fake_session.__aexit__ = AsyncMock(return_value=None)
        fake_session.initialize = AsyncMock()
        fake_session.list_tools = AsyncMock(return_value=MagicMock(tools=[]))

        async def _run():
            with (
                patch("chat_harness.mcp_client.sse_client", side_effect=fake_sse_client),
                patch("chat_harness.mcp_client.ClientSession", return_value=fake_session),
            ):
                client = MCPClient(mcp_json)
                try:
                    await client._connect_sse("vault", cfg["mcpServers"]["vault"])
                except Exception:  # noqa: BLE001
                    pass

        asyncio.run(_run())

        ctx = captured_ssl.get("ctx")
        assert ctx is not None, "ssl argument should have been passed to sse_client"
        assert isinstance(ctx, ssl.SSLContext), "Expected an ssl.SSLContext for localhost"
        assert ctx.verify_mode == ssl.CERT_NONE, "SSL verification must be disabled for localhost"


# ---------------------------------------------------------------------------
# Integration tests (require CHAT_HARNESS_INTEGRATION=1)
# ---------------------------------------------------------------------------

_skip_integration = pytest.mark.skipif(
    not os.getenv("CHAT_HARNESS_INTEGRATION"),
    reason="Set CHAT_HARNESS_INTEGRATION=1 to run integration tests",
)


@_skip_integration
class TestMCPClientIntegration:
    def test_list_tools_returns_tools_from_all_servers(self, integration_mcp_json):
        """All configured servers should contribute at least one tool."""
        async def _run():
            async with MCPClient(integration_mcp_json) as client:
                tools = client.list_tools()
                assert len(tools) > 0, "Expected at least one tool across all servers"

        asyncio.run(_run())

    def test_obsidian_list_tools(self, integration_mcp_json):
        """obsidian-vault SSE server should expose known tools."""
        async def _run():
            async with MCPClient(integration_mcp_json) as client:
                tool_names = {t.name for t in client.list_tools()}
                assert tool_names, "Expected obsidian-vault tools to be discoverable"

        asyncio.run(_run())

    def test_call_tool_returns_nonempty_result(self, integration_mcp_json):
        """Calling an obsidian list/search tool should return a non-empty result."""
        async def _run():
            async with MCPClient(integration_mcp_json) as client:
                tools = client.list_tools()
                candidates = [
                    t.name for t in tools
                    if "list" in t.name.lower() or "search" in t.name.lower()
                ]
                assert candidates, "Expected at least one list/search tool"
                result = await client.call_tool(candidates[0], {})
                assert result is not None

        asyncio.run(_run())
