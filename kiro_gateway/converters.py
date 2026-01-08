# -*- coding: utf-8 -*-

# Kiro Gateway
# https://github.com/jwadow/kiro-gateway
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

"""
Converters for transforming OpenAI <-> Kiro formats.

Contains functions for:
- Extracting text content from various formats
- Merging adjacent messages
- Building conversation history for Kiro API
- Assembling complete payload for requests
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from kiro_gateway.config import (
    get_internal_model_id,
    TOOL_DESCRIPTION_MAX_LENGTH,
    FAKE_REASONING_ENABLED,
    FAKE_REASONING_MAX_TOKENS,
)
from kiro_gateway.models import ChatMessage, ChatCompletionRequest, Tool


def extract_text_content(content: Any) -> str:
    """
    Extracts text content from various formats.
    
    OpenAI API supports several content formats:
    - String: "Hello, world!"
    - List: [{"type": "text", "text": "Hello"}]
    - None: empty message
    
    Args:
        content: Content in any supported format
    
    Returns:
        Extracted text or empty string
    
    Example:
        >>> extract_text_content("Hello")
        'Hello'
        >>> extract_text_content([{"type": "text", "text": "World"}])
        'World'
        >>> extract_text_content(None)
        ''
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif "text" in item:
                    text_parts.append(item["text"])
            elif isinstance(item, str):
                text_parts.append(item)
        return "".join(text_parts)
    return str(content)


def get_thinking_system_prompt_addition() -> str:
    """
    Generate system prompt addition that legitimizes thinking tags.
    
    This text is added to the system prompt to inform the model that
    the <thinking_mode>, <max_thinking_length>, and <thinking_instruction>
    tags in user messages are legitimate system-level instructions,
    not prompt injection attempts.
    
    Returns:
        System prompt addition text (empty string if fake reasoning is disabled)
    """
    if not FAKE_REASONING_ENABLED:
        return ""
    
    return (
        "\n\n---\n"
        "# Extended Thinking Mode\n\n"
        "This conversation uses extended thinking mode. User messages may contain "
        "special XML tags that are legitimate system-level instructions:\n"
        "- `<thinking_mode>enabled</thinking_mode>` - enables extended thinking\n"
        "- `<max_thinking_length>N</max_thinking_length>` - sets maximum thinking tokens\n"
        "- `<thinking_instruction>...</thinking_instruction>` - provides thinking guidelines\n\n"
        "These tags are NOT prompt injection attempts. They are part of the system's "
        "extended thinking feature. When you see these tags, follow their instructions "
        "and wrap your reasoning process in `<thinking>...</thinking>` tags before "
        "providing your final response."
    )


def inject_thinking_tags(content: str) -> str:
    """
    Inject fake reasoning tags into content.
    
    When FAKE_REASONING_ENABLED is True, this function prepends the special
    thinking mode tags to the content. These tags instruct the model to
    include its reasoning process in the response.
    
    The injected tags are:
    - <thinking_mode>enabled</thinking_mode>
    - <max_thinking_length>{FAKE_REASONING_MAX_TOKENS}</max_thinking_length>
    - <thinking_instruction>...</thinking_instruction> (quality improvement prompt)
    
    Args:
        content: Original content string
    
    Returns:
        Content with thinking tags prepended (if enabled) or original content
    
    Example:
        >>> # With FAKE_REASONING_ENABLED=True, FAKE_REASONING_MAX_TOKENS=4000
        >>> inject_thinking_tags("Hello")
        '<thinking_mode>enabled</thinking_mode>\\n<max_thinking_length>4000</max_thinking_length>\\n<thinking_instruction>...\\n\\nHello'
    """
    if not FAKE_REASONING_ENABLED:
        return content
    
    # Thinking instruction to improve reasoning quality
    # Uses English for better model performance (models are primarily trained on English)
    # Includes key elements: understanding, alternatives, edge cases, verification
    thinking_instruction = (
        "Think in English for better reasoning quality.\n\n"
        "Your thinking process should be thorough and systematic:\n"
        "- First, make sure you fully understand what is being asked\n"
        "- Consider multiple approaches or perspectives when relevant\n"
        "- Think about edge cases, potential issues, and what could go wrong\n"
        "- Challenge your initial assumptions\n"
        "- Verify your reasoning before reaching a conclusion\n\n"
        "Take the time you need. Quality of thought matters more than speed."
    )
    
    thinking_prefix = (
        f"<thinking_mode>enabled</thinking_mode>\n"
        f"<max_thinking_length>{FAKE_REASONING_MAX_TOKENS}</max_thinking_length>\n"
        f"<thinking_instruction>{thinking_instruction}</thinking_instruction>\n\n"
    )
    
    logger.debug(f"Injecting fake reasoning tags with max_tokens={FAKE_REASONING_MAX_TOKENS}")
    
    return thinking_prefix + content


def merge_adjacent_messages(messages: List[ChatMessage]) -> List[ChatMessage]:
    """
    Merges adjacent messages with the same role and processes tool messages.
    
    Kiro API does not accept multiple consecutive messages from the same role.
    This function merges such messages into one.
    
    Tool messages (role="tool") are converted to user messages with tool_results.
    
    Args:
        messages: List of messages
    
    Returns:
        List of messages with merged adjacent messages
    
    Example:
        >>> msgs = [
        ...     ChatMessage(role="user", content="Hello"),
        ...     ChatMessage(role="user", content="World")
        ... ]
        >>> merged = merge_adjacent_messages(msgs)
        >>> len(merged)
        1
        >>> merged[0].content
        'Hello\\nWorld'
    """
    if not messages:
        return []
    
    # First, convert tool messages to user messages with tool_results
    processed = []
    pending_tool_results = []
    
    for msg in messages:
        if msg.role == "tool":
            # Collect tool results
            tool_result = {
                "type": "tool_result",
                "tool_use_id": msg.tool_call_id or "",
                "content": extract_text_content(msg.content) or "(empty result)"
            }
            pending_tool_results.append(tool_result)
            logger.debug(f"Collected tool result for tool_call_id={msg.tool_call_id}")
        else:
            # If there are accumulated tool results, create user message with them
            if pending_tool_results:
                # Create user message with tool_results
                tool_results_msg = ChatMessage(
                    role="user",
                    content=pending_tool_results.copy()
                )
                processed.append(tool_results_msg)
                pending_tool_results.clear()
                logger.debug(f"Created user message with {len(tool_results_msg.content)} tool results")
            
            processed.append(msg)
    
    # If tool results remain at the end
    if pending_tool_results:
        tool_results_msg = ChatMessage(
            role="user",
            content=pending_tool_results.copy()
        )
        processed.append(tool_results_msg)
        logger.debug(f"Created final user message with {len(pending_tool_results)} tool results")
    
    # Now merge adjacent messages with the same role
    merged = []
    for msg in processed:
        if not merged:
            merged.append(msg)
            continue
        
        last = merged[-1]
        if msg.role == last.role:
            # Merge content
            # If both contents are lists, merge lists
            if isinstance(last.content, list) and isinstance(msg.content, list):
                last.content = last.content + msg.content
            elif isinstance(last.content, list):
                last.content = last.content + [{"type": "text", "text": extract_text_content(msg.content)}]
            elif isinstance(msg.content, list):
                last.content = [{"type": "text", "text": extract_text_content(last.content)}] + msg.content
            else:
                last_text = extract_text_content(last.content)
                current_text = extract_text_content(msg.content)
                last.content = f"{last_text}\n{current_text}"
            
            # Merge tool_calls for assistant messages
            # Critical: without this, tool_calls from second and subsequent messages are lost,
            # leading to 400 error from Kiro API (toolResult without corresponding toolUse)
            if msg.role == "assistant" and msg.tool_calls:
                if last.tool_calls is None:
                    last.tool_calls = []
                last.tool_calls = list(last.tool_calls) + list(msg.tool_calls)
                logger.debug(f"Merged tool_calls: added {len(msg.tool_calls)} tool calls, total now: {len(last.tool_calls)}")
            
            logger.debug(f"Merged adjacent messages with role {msg.role}")
        else:
            merged.append(msg)
    
    return merged


def build_kiro_history(messages: List[ChatMessage], model_id: str) -> List[Dict[str, Any]]:
    """
    Builds history array for Kiro API from OpenAI messages.
    
    Kiro API expects alternating userInputMessage and assistantResponseMessage.
    This function converts OpenAI format to Kiro format.
    
    Args:
        messages: List of messages in OpenAI format
        model_id: Internal Kiro model ID
    
    Returns:
        List of dictionaries for history field in Kiro API
    
    Example:
        >>> msgs = [ChatMessage(role="user", content="Hello")]
        >>> history = build_kiro_history(msgs, "claude-sonnet-4")
        >>> history[0]["userInputMessage"]["content"]
        'Hello'
    """
    history = []
    
    for msg in messages:
        if msg.role == "user":
            content = extract_text_content(msg.content)
            
            user_input = {
                "content": content,
                "modelId": model_id,
                "origin": "AI_EDITOR",
            }
            
            # Process tool_results (responses to tool calls)
            tool_results = _extract_tool_results(msg.content)
            if tool_results:
                user_input["userInputMessageContext"] = {"toolResults": tool_results}
            
            history.append({"userInputMessage": user_input})
            
        elif msg.role == "assistant":
            content = extract_text_content(msg.content)
            
            assistant_response = {"content": content}
            
            # Process tool_calls
            tool_uses = _extract_tool_uses(msg)
            if tool_uses:
                assistant_response["toolUses"] = tool_uses
            
            history.append({"assistantResponseMessage": assistant_response})
            
        elif msg.role == "system":
            # System prompt is handled separately in build_kiro_payload
            pass
    
    return history


def _extract_tool_results(content: Any) -> List[Dict[str, Any]]:
    """
    Extracts tool results from message content.
    
    Args:
        content: Message content (can be a list)
    
    Returns:
        List of tool results in Kiro format
    """
    tool_results = []
    
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_result":
                tool_results.append({
                    "content": [{"text": extract_text_content(item.get("content", ""))}],
                    "status": "success",
                    "toolUseId": item.get("tool_use_id", "")
                })
    
    return tool_results


def process_tools_with_long_descriptions(
    tools: Optional[List[Tool]]
) -> Tuple[Optional[List[Tool]], str]:
    """
    Processes tools with long descriptions.
    
    Kiro API has a limit on description length in toolSpecification.
    If description exceeds the limit, full description is moved to system prompt,
    and a reference to documentation remains in the tool.
    
    Args:
        tools: List of tools from OpenAI request
    
    Returns:
        Tuple of:
        - List of tools with processed descriptions (or None if tools is empty)
        - String with documentation to add to system prompt (empty if all descriptions are short)
    
    Example:
        >>> tools = [Tool(type="function", function=ToolFunction(name="bash", description="Very long..."))]
        >>> processed_tools, doc = process_tools_with_long_descriptions(tools)
        >>> "## Tool: bash" in doc
        True
    """
    if not tools:
        return None, ""
    
    # If limit is disabled (0), return tools unchanged
    if TOOL_DESCRIPTION_MAX_LENGTH <= 0:
        return tools, ""
    
    tool_documentation_parts = []
    processed_tools = []
    
    for tool in tools:
        if tool.type != "function":
            processed_tools.append(tool)
            continue
        
        description = tool.function.description or ""
        
        if len(description) <= TOOL_DESCRIPTION_MAX_LENGTH:
            # Description is short - leave as is
            processed_tools.append(tool)
        else:
            # Description is too long - move to system prompt
            tool_name = tool.function.name
            
            logger.debug(
                f"Tool '{tool_name}' has long description ({len(description)} chars > {TOOL_DESCRIPTION_MAX_LENGTH}), "
                f"moving to system prompt"
            )
            
            # Create documentation for system prompt
            tool_documentation_parts.append(f"## Tool: {tool_name}\n\n{description}")
            
            # Create copy of tool with reference description
            # Use Tool model to create new copy
            from kiro_gateway.models import ToolFunction
            
            reference_description = f"[Full documentation in system prompt under '## Tool: {tool_name}']"
            
            processed_tool = Tool(
                type=tool.type,
                function=ToolFunction(
                    name=tool.function.name,
                    description=reference_description,
                    parameters=tool.function.parameters
                )
            )
            processed_tools.append(processed_tool)
    
    # Form final documentation
    tool_documentation = ""
    if tool_documentation_parts:
        tool_documentation = (
            "\n\n---\n"
            "# Tool Documentation\n"
            "The following tools have detailed documentation that couldn't fit in the tool definition.\n\n"
            + "\n\n---\n\n".join(tool_documentation_parts)
        )
    
    return processed_tools if processed_tools else None, tool_documentation


def _extract_tool_uses(msg: ChatMessage) -> List[Dict[str, Any]]:
    """
    Extracts tool uses from assistant message.
    
    Args:
        msg: Assistant message
    
    Returns:
        List of tool uses in Kiro format
    """
    tool_uses = []
    
    # From tool_calls field
    if msg.tool_calls:
        for tc in msg.tool_calls:
            if isinstance(tc, dict):
                tool_uses.append({
                    "name": tc.get("function", {}).get("name", ""),
                    "input": json.loads(tc.get("function", {}).get("arguments", "{}")),
                    "toolUseId": tc.get("id", "")
                })
    
    # From content (if it contains tool_use)
    if isinstance(msg.content, list):
        for item in msg.content:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                tool_uses.append({
                    "name": item.get("name", ""),
                    "input": item.get("input", {}),
                    "toolUseId": item.get("id", "")
                })
    
    return tool_uses


def build_kiro_payload(
    request_data: ChatCompletionRequest,
    conversation_id: str,
    profile_arn: str
) -> dict:
    """
    Builds complete payload for Kiro API.
    
    Includes:
    - Full message history
    - System prompt (added to first user message)
    - Tools definitions (with long description handling)
    - Current message
    
    If tools contain descriptions that are too long, they are automatically
    moved to system prompt, and a reference to documentation remains in the tool.
    
    Args:
        request_data: Request in OpenAI format
        conversation_id: Unique conversation ID
        profile_arn: AWS CodeWhisperer profile ARN
    
    Returns:
        Payload dictionary for POST request to Kiro API
    
    Raises:
        ValueError: If there are no messages to send
    """
    messages = list(request_data.messages)
    
    # Process tools with long descriptions
    processed_tools, tool_documentation = process_tools_with_long_descriptions(request_data.tools)
    
    # Extract system prompt
    system_prompt = ""
    non_system_messages = []
    for msg in messages:
        if msg.role == "system":
            system_prompt += extract_text_content(msg.content) + "\n"
        else:
            non_system_messages.append(msg)
    system_prompt = system_prompt.strip()
    
    # Add tool documentation to system prompt if present
    if tool_documentation:
        system_prompt = system_prompt + tool_documentation if system_prompt else tool_documentation.strip()
    
    # Add thinking mode legitimization to system prompt if enabled
    thinking_system_addition = get_thinking_system_prompt_addition()
    if thinking_system_addition:
        system_prompt = system_prompt + thinking_system_addition if system_prompt else thinking_system_addition.strip()
    
    # Merge adjacent messages with the same role
    merged_messages = merge_adjacent_messages(non_system_messages)
    
    if not merged_messages:
        raise ValueError("No messages to send")
    
    # Get internal model ID
    model_id = get_internal_model_id(request_data.model)
    
    # Build history (all messages except the last one)
    history_messages = merged_messages[:-1] if len(merged_messages) > 1 else []
    
    # If there's a system prompt, add it to the first user message in history
    if system_prompt and history_messages:
        first_msg = history_messages[0]
        if first_msg.role == "user":
            original_content = extract_text_content(first_msg.content)
            first_msg.content = f"{system_prompt}\n\n{original_content}"
    
    history = build_kiro_history(history_messages, model_id)
    
    # Current message (the last one)
    current_message = merged_messages[-1]
    current_content = extract_text_content(current_message.content)
    
    # If system prompt exists but history is empty - add to current message
    if system_prompt and not history:
        current_content = f"{system_prompt}\n\n{current_content}"
    
    # If current message is assistant, need to add it to history
    # and create user message "Continue"
    if current_message.role == "assistant":
        history.append({
            "assistantResponseMessage": {
                "content": current_content
            }
        })
        current_content = "Continue"
    
    # If content is empty - use "Continue"
    if not current_content:
        current_content = "Continue"
    
    # Build user_input_context first to check for toolResults
    # Use processed tools (with short descriptions)
    user_input_context = _build_user_input_context(request_data, current_message, processed_tools)
    
    # Inject thinking tags if enabled (only for the current/last user message)
    # Must be AFTER empty content check to avoid injecting tags into "Continue"
    # Skip injection when toolResults are present - Kiro API rejects this combination
    # (causes "Improperly formed request" 400 error, see GitHub issue #20)
    has_tool_results = user_input_context and "toolResults" in user_input_context
    if current_message.role == "user" and not has_tool_results:
        current_content = inject_thinking_tags(current_content)
    elif has_tool_results:
        logger.debug("Skipping thinking tag injection: toolResults present in current message")
    
    # Build userInputMessage
    user_input_message = {
        "content": current_content,
        "modelId": model_id,
        "origin": "AI_EDITOR",
    }
    
    # Add user_input_context if present
    if user_input_context:
        user_input_message["userInputMessageContext"] = user_input_context
    
    # Assemble final payload
    payload = {
        "conversationState": {
            "chatTriggerType": "MANUAL",
            "conversationId": conversation_id,
            "currentMessage": {
                "userInputMessage": user_input_message
            }
        }
    }
    
    # Add history only if not empty
    if history:
        payload["conversationState"]["history"] = history
    
    # Add profileArn
    if profile_arn:
        payload["profileArn"] = profile_arn
    
    return payload


def _sanitize_json_schema(schema: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sanitizes JSON Schema from fields that Kiro API doesn't accept.
    
    Kiro API returns 400 "Improperly formed request" error if:
    - required is an empty array []
    - additionalProperties is present in schema
    
    This function recursively processes the schema and removes problematic fields.
    
    Args:
        schema: JSON Schema to sanitize
    
    Returns:
        Sanitized copy of schema
    """
    if not schema:
        return {}
    
    # Create copy to avoid mutating original
    result = {}
    
    for key, value in schema.items():
        # Skip empty required arrays
        if key == "required" and isinstance(value, list) and len(value) == 0:
            continue
        
        # Skip additionalProperties - Kiro API doesn't support it
        if key == "additionalProperties":
            continue
        
        # Recursively process nested objects
        if key == "properties" and isinstance(value, dict):
            result[key] = {
                prop_name: _sanitize_json_schema(prop_value) if isinstance(prop_value, dict) else prop_value
                for prop_name, prop_value in value.items()
            }
        elif isinstance(value, dict):
            result[key] = _sanitize_json_schema(value)
        elif isinstance(value, list):
            # Process lists (e.g., anyOf, oneOf)
            result[key] = [
                _sanitize_json_schema(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    
    return result


def _build_user_input_context(
    request_data: ChatCompletionRequest,
    current_message: ChatMessage,
    processed_tools: Optional[List[Tool]] = None
) -> Dict[str, Any]:
    """
    Builds userInputMessageContext for current message.
    
    Includes tools definitions and tool_results.
    
    Args:
        request_data: Request with tools
        current_message: Current message
        processed_tools: Processed tools with short descriptions (optional).
                        If None, tools from request_data are used.
    
    Returns:
        Dictionary with context or empty dictionary
    """
    context = {}
    
    # Use processed tools if provided, otherwise original
    tools_to_use = processed_tools if processed_tools is not None else request_data.tools
    
    # Add tools if present
    if tools_to_use:
        tools_list = []
        for tool in tools_to_use:
            if tool.type == "function":
                # Sanitize parameters from fields that Kiro API doesn't accept
                sanitized_params = _sanitize_json_schema(tool.function.parameters)
                
                # Kiro API requires non-empty description
                # If description is empty or None, use placeholder
                description = tool.function.description
                if not description or not description.strip():
                    description = f"Tool: {tool.function.name}"
                    logger.debug(f"Tool '{tool.function.name}' has empty description, using placeholder")
                
                tools_list.append({
                    "toolSpecification": {
                        "name": tool.function.name,
                        "description": description,
                        "inputSchema": {"json": sanitized_params}
                    }
                })
        if tools_list:
            context["tools"] = tools_list
    
    # Process tool_results in current message
    tool_results = _extract_tool_results(current_message.content)
    if tool_results:
        context["toolResults"] = tool_results
    
    return context