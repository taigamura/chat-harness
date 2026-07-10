"""Agentic loop: drives Qwen via Ollama, dispatches MCP tool calls."""

from __future__ import annotations

from typing import Any

from mcp.types import Tool

from chat_harness.config import Config
from chat_harness.llm import OllamaClient
from chat_harness.mcp_client import MCPClient

_MAX_ITERATIONS = 10

_SYSTEM_PROMPT_TEMPLATE = """\
You are a helpful assistant with access to MCP tools from the following servers: {servers}.

Guidelines:
- Use the available tools to answer requests rather than guessing or hallucinating.
- Always search the Obsidian vault first (obsidian_simple_search or obsidian_get_file_contents) before \
searching the web, to leverage local knowledge.
- Only search the web (fetch, ddg, or playwright tools) when the vault does not contain relevant information.
- When writing notes or files to the vault, use the obsidian-vault MCP tools.
- Respond in Markdown.
- When you have gathered enough information, provide a final answer without calling more tools.
"""


def _build_ollama_tools(tools: list[Tool], skip: list[str], degraded: list[str]) -> list[dict[str, Any]]:
    """Convert MCP Tool schemas to Ollama function-calling format."""
    result = []
    for tool in tools:
        if tool.name in skip:
            continue
        description = "" if tool.name in degraded else (tool.description or "")
        result.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": description,
                "parameters": tool.inputSchema or {},
            },
        })
    return result


def _serialize_tool_result(result: Any) -> str:
    """Flatten an MCP CallToolResult to a plain string for the message history."""
    if result is None:
        return ""
    content_blocks = getattr(result, "content", None)
    if content_blocks is None:
        return str(result)
    parts = []
    for block in content_blocks:
        block_type = getattr(block, "type", "unknown")
        if block_type == "text":
            parts.append(getattr(block, "text", ""))
        else:
            parts.append(f"[non-text content of type: {block_type}]")
    return "\n".join(parts)


class Agent:
    """Drives the Qwen agentic loop with persistent conversation history."""

    def __init__(self, config: Config, mcp_client: MCPClient, llm: OllamaClient) -> None:
        self._config = config
        self._mcp = mcp_client
        self._llm = llm
        self._messages: list[dict[str, Any]] = []
        self._ollama_tools: list[dict[str, Any]] = []
        self._system_prompt: str = ""
        self._build_tool_list()

    def _build_tool_list(self) -> None:
        skills = self._config.skills
        skip = skills.get("qwen_skip", [])
        degraded = skills.get("qwen_degraded", [])
        tools = self._mcp.list_tools()
        self._ollama_tools = _build_ollama_tools(tools, skip, degraded)

        server_names = sorted(set(self._mcp._tool_server.values()))  # noqa: SLF001
        servers = ", ".join(server_names) if server_names else "none"
        self._system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(servers=servers)

    def clear_history(self) -> None:
        """Reset the conversation history."""
        self._messages.clear()

    async def run(self, user_message: str) -> str:
        """Process a user message and return the assistant's final response."""
        self._messages.append({"role": "user", "content": user_message})

        system_messages = [{"role": "system", "content": self._system_prompt}]

        for _ in range(_MAX_ITERATIONS):
            response = await self._llm.chat(
                messages=system_messages + self._messages,
                tools=self._ollama_tools or None,
            )

            if not response.tool_calls:
                final = response.content or ""
                self._messages.append({"role": "assistant", "content": final})
                return final

            # Append assistant message with tool calls
            self._messages.append({
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": [
                    {
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments,
                        }
                    }
                    for tc in response.tool_calls
                ],
            })

            # Execute each tool call and append results
            for tc in response.tool_calls:
                try:
                    result = await self._mcp.call_tool(tc.name, tc.arguments)
                    tool_content = _serialize_tool_result(result)
                except Exception as exc:  # noqa: BLE001
                    tool_content = f"Error: {exc}"

                self._messages.append({
                    "role": "tool",
                    "content": tool_content,
                })

        fallback = "[Agent reached maximum iterations without a final answer]"
        self._messages.append({"role": "assistant", "content": fallback})
        return fallback
