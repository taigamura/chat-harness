"""Unit tests for the Agent agentic loop."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from chat_harness.agent import Agent
from chat_harness.config import Config
from chat_harness.llm import ChatResponse, ToolCall


@pytest.fixture()
def config(tmp_path):
    return Config({}, tmp_path / "c.yaml")


def _make_mcp(tools=None, call_result=None):
    mcp = MagicMock()
    mcp.list_tools.return_value = tools or []
    mcp._tool_server = {}
    mcp.call_tool = AsyncMock(return_value=call_result)
    return mcp


def _make_llm(*responses: ChatResponse):
    llm = MagicMock()
    llm.chat = AsyncMock(side_effect=list(responses))
    return llm


@pytest.mark.anyio
async def test_single_turn_no_tools(config):
    mcp = _make_mcp()
    llm = _make_llm(ChatResponse(content="Hello!"))
    agent = Agent(config, mcp, llm)

    result = await agent.run("Hi")

    assert result == "Hello!"
    assert llm.chat.call_count == 1


@pytest.mark.anyio
async def test_tool_call_folded_back(config):
    tool = MagicMock()
    tool.name = "obsidian_search"
    tool.description = "Search vault"
    tool.inputSchema = {"type": "object", "properties": {}}

    mcp = _make_mcp(tools=[tool])
    mcp._tool_server = {"obsidian_search": "obsidian-vault"}

    tool_result = MagicMock()
    block = MagicMock()
    block.type = "text"
    block.text = "Found: note1"
    tool_result.content = [block]
    mcp.call_tool = AsyncMock(return_value=tool_result)

    llm = _make_llm(
        ChatResponse(content=None, tool_calls=[ToolCall(name="obsidian_search", arguments={"query": "test"})]),
        ChatResponse(content="Here is what I found: note1"),
    )
    agent = Agent(config, mcp, llm)

    result = await agent.run("Search for test")

    assert result == "Here is what I found: note1"
    assert llm.chat.call_count == 2
    mcp.call_tool.assert_called_once_with("obsidian_search", {"query": "test"})


@pytest.mark.anyio
async def test_max_iterations_guard(config):
    mcp = _make_mcp()
    # Always returns a tool call — should terminate at 10 iterations
    infinite_tool = ChatResponse(
        content=None,
        tool_calls=[ToolCall(name="fake_tool", arguments={})],
    )
    llm = _make_llm(*([infinite_tool] * 15))
    agent = Agent(config, mcp, llm)

    result = await agent.run("Loop forever")

    assert "maximum iterations" in result
    assert llm.chat.call_count == 10


@pytest.mark.anyio
async def test_unknown_tool_fed_back_as_error(config):
    mcp = _make_mcp()
    mcp._tool_server = {}
    mcp.call_tool = AsyncMock(side_effect=ValueError("Unknown tool: 'ghost'"))

    llm = _make_llm(
        ChatResponse(content=None, tool_calls=[ToolCall(name="ghost", arguments={})]),
        ChatResponse(content="I couldn't find that tool."),
    )
    agent = Agent(config, mcp, llm)

    result = await agent.run("Use ghost tool")

    assert result == "I couldn't find that tool."
    # Second chat call should have a tool-result message containing the error
    second_call_messages = llm.chat.call_args_list[1][1]["messages"] if llm.chat.call_args_list[1][1] else llm.chat.call_args_list[1][0][0]
    tool_msgs = [m for m in second_call_messages if m.get("role") == "tool"]
    assert any("Error" in m["content"] for m in tool_msgs)


@pytest.mark.anyio
async def test_history_persists_across_runs(config):
    mcp = _make_mcp()
    llm = _make_llm(
        ChatResponse(content="First answer"),
        ChatResponse(content="Second answer"),
    )
    agent = Agent(config, mcp, llm)

    await agent.run("First message")
    await agent.run("Second message")

    # Both calls should include accumulated history
    first_call_msgs = llm.chat.call_args_list[0][0][0] if llm.chat.call_args_list[0][0] else llm.chat.call_args_list[0][1]["messages"]
    second_call_msgs = llm.chat.call_args_list[1][0][0] if llm.chat.call_args_list[1][0] else llm.chat.call_args_list[1][1]["messages"]
    # Second call should have more messages (includes first turn)
    assert len(second_call_msgs) > len(first_call_msgs)


@pytest.mark.anyio
async def test_clear_history_resets(config):
    mcp = _make_mcp()
    llm = _make_llm(
        ChatResponse(content="Before clear"),
        ChatResponse(content="After clear"),
    )
    agent = Agent(config, mcp, llm)

    await agent.run("Before")
    agent.clear_history()
    await agent.run("After")

    first_msgs = llm.chat.call_args_list[0][0][0] if llm.chat.call_args_list[0][0] else llm.chat.call_args_list[0][1]["messages"]
    second_msgs = llm.chat.call_args_list[1][0][0] if llm.chat.call_args_list[1][0] else llm.chat.call_args_list[1][1]["messages"]
    # After clear, history resets — second call has same depth as first
    assert len(first_msgs) == len(second_msgs)
