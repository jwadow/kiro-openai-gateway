# -*- coding: utf-8 -*-

# Kiro OpenAI Gateway
# https://github.com/jwadow/kiro-openai-gateway
# Copyright (C) 2025 Jwadow
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import json
import uuid
from typing import Any, AsyncGenerator, Dict, Optional

from kiro_gateway.anthropic_converters import _finish_reason_to_stop_reason, _safe_json_loads


def _sse_event(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_openai_sse_to_anthropic_sse(
    openai_sse: AsyncGenerator[str, None],
    model: str,
) -> AsyncGenerator[str, None]:
    message_id = f"msg_{uuid.uuid4().hex}"

    content_block_index = 0
    text_block_open = True

    tool_calls_seen: list[dict] = []
    finish_reason: Optional[str] = None
    usage: Optional[dict] = None

    yield _sse_event(
        "message_start",
        {
            "type": "message_start",
            "message": {
                "id": message_id,
                "type": "message",
                "role": "assistant",
                "model": model,
                "content": [],
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        },
    )

    yield _sse_event(
        "content_block_start",
        {
            "type": "content_block_start",
            "index": content_block_index,
            "content_block": {"type": "text", "text": ""},
        },
    )

    try:
        async for chunk_str in openai_sse:
            if not chunk_str.startswith("data:"):
                continue
            data_str = chunk_str[len("data:") :].strip()
            if not data_str or data_str == "[DONE]":
                continue

            try:
                chunk = json.loads(data_str)
            except Exception:
                continue

            choice = (chunk.get("choices") or [{}])[0]
            delta = choice.get("delta") or {}

            if choice.get("finish_reason") is not None:
                finish_reason = choice.get("finish_reason")
            if chunk.get("usage") is not None:
                usage = chunk.get("usage")

            text_delta = delta.get("content")
            if text_delta:
                yield _sse_event(
                    "content_block_delta",
                    {
                        "type": "content_block_delta",
                        "index": content_block_index,
                        "delta": {"type": "text_delta", "text": text_delta},
                    },
                )

            delta_tool_calls = delta.get("tool_calls")
            if delta_tool_calls:
                tool_calls_seen.extend(delta_tool_calls)

                if text_block_open:
                    yield _sse_event(
                        "content_block_stop",
                        {"type": "content_block_stop", "index": content_block_index},
                    )
                    text_block_open = False

                for tc in delta_tool_calls:
                    content_block_index += 1
                    func = tc.get("function") or {}
                    args_raw = func.get("arguments") or "{}"
                    tool_block = {
                        "type": "tool_use",
                        "id": tc.get("id") or "",
                        "name": func.get("name") or "",
                        "input": _safe_json_loads(args_raw),
                    }

                    yield _sse_event(
                        "content_block_start",
                        {
                            "type": "content_block_start",
                            "index": content_block_index,
                            "content_block": tool_block,
                        },
                    )
                    yield _sse_event(
                        "content_block_stop",
                        {"type": "content_block_stop", "index": content_block_index},
                    )

    except Exception as e:
        yield _sse_event(
            "error",
            {"type": "error", "error": {"type": "internal_error", "message": str(e)}},
        )
        return

    if text_block_open:
        yield _sse_event(
            "content_block_stop",
            {"type": "content_block_stop", "index": content_block_index},
        )

    stop_reason = _finish_reason_to_stop_reason(finish_reason, tool_calls=tool_calls_seen)
    output_tokens = int((usage or {}).get("completion_tokens") or 0)
    input_tokens = int((usage or {}).get("prompt_tokens") or 0)

    yield _sse_event(
        "message_delta",
        {
            "type": "message_delta",
            "delta": {"stop_reason": stop_reason, "stop_sequence": None},
            "usage": {"output_tokens": output_tokens, "input_tokens": input_tokens},
        },
    )
    yield _sse_event("message_stop", {"type": "message_stop"})
