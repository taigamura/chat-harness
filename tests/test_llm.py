"""Unit tests for OllamaClient using respx to mock httpx."""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response

from chat_harness.config import Config
from chat_harness.llm import LLMError, OllamaClient


@pytest.fixture()
def config(tmp_path):
    return Config({"ollama_url": "http://localhost:11434", "model": "test-model"}, tmp_path / "c.yaml")


@pytest.fixture()
def ollama_url():
    return "http://localhost:11434"


def _chat_response(content: str | None = None, tool_calls: list | None = None) -> dict:
    message: dict = {"role": "assistant"}
    if content is not None:
        message["content"] = content
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return {"model": "test-model", "message": message, "done": True}


@respx.mock
@pytest.mark.anyio
async def test_plain_text_response(config):
    respx.post("http://localhost:11434/api/chat").mock(
        return_value=Response(200, json=_chat_response(content="Hello, world!"))
    )
    async with OllamaClient(config) as llm:
        resp = await llm.chat([{"role": "user", "content": "Hi"}])

    assert resp.content == "Hello, world!"
    assert resp.tool_calls == []


@respx.mock
@pytest.mark.anyio
async def test_tool_call_response(config):
    tool_calls = [{"function": {"name": "search", "arguments": {"query": "cats"}}}]
    respx.post("http://localhost:11434/api/chat").mock(
        return_value=Response(200, json=_chat_response(tool_calls=tool_calls))
    )
    async with OllamaClient(config) as llm:
        resp = await llm.chat([{"role": "user", "content": "Search for cats"}], tools=[])

    assert resp.content is None
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].name == "search"
    assert resp.tool_calls[0].arguments == {"query": "cats"}


@respx.mock
@pytest.mark.anyio
async def test_http_error_raises_llm_error(config):
    respx.post("http://localhost:11434/api/chat").mock(
        return_value=Response(500, text="internal error")
    )
    async with OllamaClient(config) as llm:
        with pytest.raises(LLMError, match="500"):
            await llm.chat([{"role": "user", "content": "Hi"}])


@respx.mock
@pytest.mark.anyio
async def test_empty_content_becomes_none(config):
    respx.post("http://localhost:11434/api/chat").mock(
        return_value=Response(200, json=_chat_response(content=""))
    )
    async with OllamaClient(config) as llm:
        resp = await llm.chat([{"role": "user", "content": "Hi"}])

    assert resp.content is None
