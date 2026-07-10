"""Ollama HTTP client for chat completions with tool-use support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from chat_harness.config import Config


class LLMError(Exception):
    """Raised when the Ollama API returns an error response."""


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class ChatResponse:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)


class OllamaClient:
    """Async Ollama chat client with tool-use support."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OllamaClient":
        self._client = httpx.AsyncClient(base_url=self._config.ollama_url, timeout=120.0)
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> ChatResponse:
        """POST to /api/chat and return a structured response."""
        assert self._client is not None, "OllamaClient must be used as a context manager"

        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        try:
            response = await self._client.post("/api/chat", json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LLMError(f"Ollama returned {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.RequestError as exc:
            raise LLMError(f"Ollama request failed: {exc}") from exc

        data = response.json()
        message = data.get("message", {})
        content: str | None = message.get("content") or None

        tool_calls: list[ToolCall] = []
        for tc in message.get("tool_calls", []):
            fn = tc.get("function", {})
            tool_calls.append(ToolCall(name=fn.get("name", ""), arguments=fn.get("arguments", {})))

        return ChatResponse(content=content, tool_calls=tool_calls)
