# -*- coding: utf-8 -*-

import pytest

from kiro_gateway.anthropic_streaming import stream_openai_sse_to_anthropic_sse


@pytest.mark.asyncio
async def test_openai_sse_is_wrapped_as_anthropic_sse():
    async def openai_gen():
        yield 'data: {"choices":[{"index":0,"delta":{"role":"assistant","content":"Hello"},"finish_reason":null}],"model":"m"}\n\n'
        yield 'data: {"choices":[{"index":0,"delta":{"content":" world"},"finish_reason":null}],"model":"m"}\n\n'
        yield 'data: {"choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"id":"call_1","type":"function","function":{"name":"t","arguments":"{\\"a\\":1}"}}]},"finish_reason":null}],"model":"m"}\n\n'
        yield 'data: {"choices":[{"index":0,"delta":{},"finish_reason":"tool_calls"}],"usage":{"prompt_tokens":2,"completion_tokens":3,"total_tokens":5},"model":"m"}\n\n'
        yield 'data: [DONE]\n\n'

    out = []
    async for chunk in stream_openai_sse_to_anthropic_sse(openai_gen(), model="m"):
        out.append(chunk)

    joined = "".join(out)
    assert "event: message_start" in joined
    assert "event: content_block_start" in joined
    assert "event: content_block_delta" in joined
    assert "event: message_delta" in joined
    assert "event: message_stop" in joined
    assert "tool_use" in joined
