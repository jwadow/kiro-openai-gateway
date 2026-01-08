# -*- coding: utf-8 -*-

import pytest

from kiro_gateway.anthropic_converters import (
    anthropic_request_to_openai_chat_completion_request,
    openai_chat_completion_to_anthropic_message,
)
from kiro_gateway.anthropic_models import AnthropicCreateMessageRequest


def test_anthropic_request_converts_system_and_user():
    req = AnthropicCreateMessageRequest(
        model="claude-sonnet-4-5",
        max_tokens=10,
        messages=[{"role": "user", "content": "Hello"}],
        system="You are helpful",
    )

    openai_req = anthropic_request_to_openai_chat_completion_request(req)
    assert openai_req.model == "claude-sonnet-4-5"
    assert openai_req.max_tokens == 10
    assert openai_req.messages[0].role == "system"
    assert "You are helpful" in (openai_req.messages[0].content or "")
    assert openai_req.messages[1].role == "user"


def test_anthropic_tool_result_becomes_tool_message():
    req = AnthropicCreateMessageRequest(
        model="claude-sonnet-4-5",
        max_tokens=10,
        messages=[
            {"role": "assistant", "content": [{"type": "tool_use", "id": "call_1", "name": "t", "input": {"a": 1}}]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_1", "content": "ok"}]},
        ],
    )

    openai_req = anthropic_request_to_openai_chat_completion_request(req)
    roles = [m.role for m in openai_req.messages]
    assert roles == ["assistant", "tool"]
    assert openai_req.messages[1].tool_call_id == "call_1"


def test_openai_response_converts_tool_calls_to_tool_use_blocks():
    openai_response = {
        "id": "chatcmpl_1",
        "model": "claude-sonnet-4-5",
        "choices": [
            {
                "index": 0,
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_abc",
                            "type": "function",
                            "function": {"name": "get_weather", "arguments": "{\"city\":\"Paris\"}"},
                        }
                    ],
                },
            }
        ],
        "usage": {"prompt_tokens": 3, "completion_tokens": 5, "total_tokens": 8},
    }

    msg = openai_chat_completion_to_anthropic_message(openai_response)
    assert msg["type"] == "message"
    assert msg["stop_reason"] == "tool_use"
    tool_blocks = [b for b in msg["content"] if b.get("type") == "tool_use"]
    assert tool_blocks[0]["id"] == "call_abc"
    assert tool_blocks[0]["input"]["city"] == "Paris"
