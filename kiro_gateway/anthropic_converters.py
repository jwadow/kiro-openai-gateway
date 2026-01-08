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
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from kiro_gateway.anthropic_models import (
    AnthropicCountTokensRequest,
    AnthropicCreateMessageRequest,
    AnthropicMessageParam,
    AnthropicTool,
)
from kiro_gateway.models import ChatCompletionRequest, ChatMessage, Tool, ToolFunction


def anthropic_request_to_openai_chat_completion_request(
    request_data: AnthropicCreateMessageRequest,
) -> ChatCompletionRequest:
    messages: List[ChatMessage] = []

    system_text = _anthropic_content_to_text(request_data.system)
    if system_text:
        messages.append(ChatMessage(role="system", content=system_text))

    messages.extend(_anthropic_messages_to_openai_messages(request_data.messages))

    tools = _anthropic_tools_to_openai_tools(request_data.tools)
    tool_choice = _anthropic_tool_choice_to_openai_tool_choice(request_data.tool_choice)

    return ChatCompletionRequest(
        model=request_data.model,
        messages=messages,
        stream=request_data.stream,
        temperature=request_data.temperature,
        top_p=request_data.top_p,
        max_tokens=request_data.max_tokens,
        stop=request_data.stop_sequences,
        tools=tools,
        tool_choice=tool_choice,
    )


def anthropic_count_tokens_to_openai_messages_and_tools(
    request_data: AnthropicCountTokensRequest,
) -> Tuple[List[Dict[str, Any]], Optional[List[Dict[str, Any]]], Optional[str]]:
    messages: List[ChatMessage] = []

    system_text = _anthropic_content_to_text(request_data.system)
    if system_text:
        messages.append(ChatMessage(role="system", content=system_text))

    messages.extend(_anthropic_messages_to_openai_messages(request_data.messages))

    tools = _anthropic_tools_to_openai_tools(request_data.tools)

    messages_payload = [m.model_dump() for m in messages]
    tools_payload = [t.model_dump() for t in tools] if tools else None

    return messages_payload, tools_payload, None


def openai_chat_completion_to_anthropic_message(openai_response: Dict[str, Any]) -> Dict[str, Any]:
    choice = (openai_response.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    finish_reason = choice.get("finish_reason")

    content_text = message.get("content") or ""
    tool_calls = message.get("tool_calls") or []

    content_blocks: List[Dict[str, Any]] = []
    if content_text:
        content_blocks.append({"type": "text", "text": content_text})

    for tc in tool_calls:
        function = tc.get("function") or {}
        name = function.get("name") or ""
        arguments = function.get("arguments") or "{}"
        content_blocks.append(
            {
                "type": "tool_use",
                "id": tc.get("id") or "",
                "name": name,
                "input": _safe_json_loads(arguments),
            }
        )

    usage = openai_response.get("usage") or {}
    return {
        "id": openai_response.get("id") or "",
        "type": "message",
        "role": "assistant",
        "model": openai_response.get("model") or "",
        "content": content_blocks,
        "stop_reason": _finish_reason_to_stop_reason(finish_reason, tool_calls=tool_calls),
        "stop_sequence": None,
        "usage": {
            "input_tokens": int(usage.get("prompt_tokens") or 0),
            "output_tokens": int(usage.get("completion_tokens") or 0),
        },
    }


def _finish_reason_to_stop_reason(finish_reason: Optional[str], tool_calls: List[Dict[str, Any]]) -> Optional[str]:
    if finish_reason == "length":
        return "max_tokens"
    if finish_reason == "tool_calls" or tool_calls:
        return "tool_use"
    if finish_reason == "stop" or finish_reason is None:
        return "end_turn"
    return "end_turn"


def _anthropic_tool_choice_to_openai_tool_choice(
    tool_choice: Optional[Union[str, Dict[str, Any]]],
) -> Optional[Union[str, Dict[str, Any]]]:
    if tool_choice is None:
        return None
    if isinstance(tool_choice, str):
        if tool_choice == "any":
            return "required"
        return tool_choice
    if isinstance(tool_choice, dict):
        choice_type = tool_choice.get("type")
        name = tool_choice.get("name")
        if choice_type == "tool" and name:
            return {"type": "function", "function": {"name": name}}
        return tool_choice
    return None


def _anthropic_tools_to_openai_tools(tools: Optional[Iterable[AnthropicTool]]) -> Optional[List[Tool]]:
    if not tools:
        return None
    converted: List[Tool] = []
    for tool in tools:
        converted.append(
            Tool(
                type="function",
                function=ToolFunction(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.input_schema,
                ),
            )
        )
    return converted


def _anthropic_messages_to_openai_messages(messages: List[AnthropicMessageParam]) -> List[ChatMessage]:
    out: List[ChatMessage] = []

    for msg in messages:
        role = msg.role
        content = msg.content

        if role == "user":
            user_message, tool_messages = _convert_anthropic_user_message(content)
            if user_message is not None:
                out.append(user_message)
            out.extend(tool_messages)
            continue

        if role == "assistant":
            out.append(ChatMessage(role="assistant", content=_anthropic_content_passthrough(content)))
            continue

        if role == "system":
            system_text = _anthropic_content_to_text(content)
            if system_text:
                out.append(ChatMessage(role="system", content=system_text))
            continue

        out.append(ChatMessage(role=role, content=_anthropic_content_passthrough(content)))

    return out


def _convert_anthropic_user_message(
    content: Any,
) -> Tuple[Optional[ChatMessage], List[ChatMessage]]:
    if isinstance(content, str) or content is None:
        text = _anthropic_content_to_text(content)
        if text:
            return ChatMessage(role="user", content=text), []
        return None, []

    if not isinstance(content, list):
        text = _anthropic_content_to_text(content)
        if text:
            return ChatMessage(role="user", content=text), []
        return None, []

    text_blocks: List[Dict[str, Any]] = []
    tool_messages: List[ChatMessage] = []

    for block in content:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")

        if block_type == "tool_result":
            tool_use_id = block.get("tool_use_id") or ""
            tool_text = _anthropic_content_to_text(block.get("content"))
            tool_messages.append(
                ChatMessage(role="tool", content=tool_text, tool_call_id=tool_use_id)
            )
            continue

        if block_type == "text":
            text_blocks.append({"type": "text", "text": block.get("text") or ""})
            continue

        # Best-effort passthrough for non-text blocks (e.g. images) as text placeholder.
        text_blocks.append({"type": "text", "text": _anthropic_content_to_text(block)})

    user_message: Optional[ChatMessage] = None
    if text_blocks:
        user_message = ChatMessage(role="user", content=text_blocks)

    return user_message, tool_messages


def _anthropic_content_passthrough(content: Any) -> Any:
    if isinstance(content, list):
        # Keep blocks as-is so existing Kiro converters can detect tool_use/tool_result.
        return content
    return content


def _anthropic_content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text") or "")
            else:
                parts.append(_anthropic_content_to_text(item))
        return "".join(parts)
    if isinstance(content, dict):
        if content.get("type") == "text":
            return str(content.get("text") or "")
        if "text" in content and isinstance(content.get("text"), str):
            return content.get("text")
        return json.dumps(content, ensure_ascii=False)
    return str(content)


def _safe_json_loads(value: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(value)
    except Exception:
        return {"_raw": value}
    if isinstance(parsed, dict):
        return parsed
    return {"value": parsed}
