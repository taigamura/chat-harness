"""MCP client: boots all servers from mcp.json, discovers tools, dispatches calls."""

from __future__ import annotations

import json
import ssl
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import Tool

_DEFAULT_MCP_JSON = Path(__file__).parent.parent / "mcp.json"

_LOCALHOST_HOSTS = {"localhost", "127.0.0.1", "::1"}


class MCPClient:
    """Manages MCP server connections and provides a unified tool interface.

    Usage::

        async with MCPClient() as client:
            tools = client.list_tools()
            result = await client.call_tool("obsidian_search", {"query": "foo"})
    """

    def __init__(self, mcp_json_path: Path | None = None) -> None:
        self._config_path = Path(mcp_json_path) if mcp_json_path else _DEFAULT_MCP_JSON
        # Maps server_name -> ClientSession
        self._sessions: dict[str, ClientSession] = {}
        # Maps tool_name -> server_name for fast dispatch
        self._tool_server: dict[str, str] = {}
        # Maps tool_name -> Tool schema
        self._tool_schemas: dict[str, Tool] = {}
        # Keep open context managers alive until _stop()
        self._cms: list[Any] = []

    async def __aenter__(self) -> "MCPClient":
        await self._start()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._stop()

    # ------------------------------------------------------------------
    # Boot / teardown
    # ------------------------------------------------------------------

    async def _start(self) -> None:
        config = self._load_config()
        for name, server_cfg in config.get("mcpServers", {}).items():
            transport_type = server_cfg.get("type", "stdio")
            try:
                if transport_type == "sse":
                    session = await self._connect_sse(name, server_cfg)
                else:
                    session = await self._connect_stdio(name, server_cfg)
                self._sessions[name] = session
                await self._discover_tools(name, session)
            except Exception as exc:  # noqa: BLE001
                # A server failing to start should not abort the whole client
                print(f"[mcp_client] Warning: failed to start server '{name}': {exc}")

    async def _stop(self) -> None:
        # Close sessions in reverse order; the underlying transports are
        # cleaned up when the context managers stored in self._cms exit.
        for cm in reversed(self._cms):
            try:
                await cm.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass
        self._sessions.clear()
        self._tool_server.clear()
        self._tool_schemas.clear()
        self._cms.clear()

    # ------------------------------------------------------------------
    # Transport helpers
    # ------------------------------------------------------------------

    async def _connect_sse(self, name: str, cfg: dict[str, Any]) -> ClientSession:
        url: str = cfg["url"]
        headers: dict[str, str] = cfg.get("headers", {})

        # Disable SSL verification only for localhost SSE connections
        ssl_context: ssl.SSLContext | bool
        hostname = urlparse(url).hostname or ""
        if hostname in _LOCALHOST_HOSTS:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        else:
            ssl_context = True  # default: SSL verification enabled

        cm = sse_client(url, headers=headers, ssl=ssl_context)
        read, write = await cm.__aenter__()
        self._cms.append(cm)

        session = ClientSession(read, write)
        session_cm = session
        await session_cm.__aenter__()
        self._cms.append(session_cm)

        await session.initialize()
        return session

    async def _connect_stdio(self, name: str, cfg: dict[str, Any]) -> ClientSession:
        command: str = cfg["command"]
        args: list[str] = cfg.get("args", [])
        env: dict[str, str] | None = cfg.get("env")

        params = StdioServerParameters(command=command, args=args, env=env)
        cm = stdio_client(params)
        read, write = await cm.__aenter__()
        self._cms.append(cm)

        session = ClientSession(read, write)
        session_cm = session
        await session_cm.__aenter__()
        self._cms.append(session_cm)

        await session.initialize()
        return session

    # ------------------------------------------------------------------
    # Tool discovery
    # ------------------------------------------------------------------

    async def _discover_tools(self, server_name: str, session: ClientSession) -> None:
        response = await session.list_tools()
        for tool in response.tools:
            self._tool_server[tool.name] = server_name
            self._tool_schemas[tool.name] = tool

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_tools(self) -> list[Tool]:
        """Return all tool schemas discovered across all servers."""
        return list(self._tool_schemas.values())

    async def call_tool(self, name: str, args: dict[str, Any] | None = None) -> Any:
        """Dispatch a tool call to the owning server and return the result."""
        server_name = self._tool_server.get(name)
        if server_name is None:
            raise ValueError(f"Unknown tool: '{name}'. Available: {sorted(self._tool_server)}")
        session = self._sessions[server_name]
        result = await session.call_tool(name, arguments=args or {})
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_config(self) -> dict[str, Any]:
        if not self._config_path.exists():
            raise FileNotFoundError(f"mcp.json not found at {self._config_path}")
        with self._config_path.open() as fh:
            return json.load(fh)
