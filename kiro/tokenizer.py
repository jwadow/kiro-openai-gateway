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
Module for fast token counting.

Uses tiktoken (OpenAI's Rust library) for approximate
token counting. The cl100k_base encoding is close to Claude tokenization.

Note: This is an approximate count, as the exact Claude tokenizer
is not public. Anthropic does not publish their tokenizer,
so tiktoken with a correction coefficient is used.

The correction coefficient CLAUDE_CORRECTION_FACTOR = 1.15 is based on
empirical observations: Claude tokenizes text approximately 15%
more than GPT-4 (cl100k_base). This is due to differences in BPE vocabularies.
"""

from typing import Any, List, Dict, Optional
from loguru import logger

# Lazy loading of tiktoken to speed up import
_encoding = None

# Correction coefficient for Claude models
# Claude tokenizes text approximately 15% more than GPT-4 (cl100k_base)
# This is an empirical value based on comparison with context_usage from API
CLAUDE_CORRECTION_FACTOR = 1.15


def _get_encoding():
    """
    Lazy initialization of tokenizer.
    
    Uses cl100k_base - encoding for GPT-4/ChatGPT,
    which is close enough to Claude tokenization.
    
    Returns:
        tiktoken.Encoding or None if tiktoken is unavailable
    """
    global _encoding
    if _encoding is None:
        try:
            import tiktoken
            _encoding = tiktoken.get_encoding("cl100k_base")
            logger.debug("[Tokenizer] Initialized tiktoken with cl100k_base encoding")
        except ImportError:
            logger.warning(
                "[Tokenizer] tiktoken not installed. "
                "Token counting will use fallback estimation. "
                "Install with: pip install tiktoken"
            )
            _encoding = False  # Marker that import failed
        except Exception as e:
            logger.error(f"[Tokenizer] Failed to initialize tiktoken: {e}")
            _encoding = False
    return _encoding if _encoding else None


def count_tokens(text: str, apply_claude_correction: bool = True) -> int:
    """
    Counts the number of tokens in text.
    
    Args:
        text: Text to count tokens for
        apply_claude_correction: Apply correction coefficient for Claude (default True)
    
    Returns:
        Number of tokens (approximate, with Claude correction)
    """
    if not text:
        return 0
    
    encoding = _get_encoding()
    if encoding:
        try:
            base_tokens = len(encoding.encode(text))
            if apply_claude_correction:
                return int(base_tokens * CLAUDE_CORRECTION_FACTOR)
            return base_tokens
        except Exception as e:
            logger.warning(f"[Tokenizer] Error encoding text: {e}")
    
    # Fallback: rough estimate ~4 characters per token for English,
    # ~2-3 characters for other languages (taking average ~3.5)
    # For Claude we add correction
    base_estimate = len(text) // 4 + 1
    if apply_claude_correction:
        return int(base_estimate * CLAUDE_CORRECTION_FACTOR)
    return base_estimate


def count_message_tokens(messages: List[Dict[str, Any]], apply_claude_correction: bool = True) -> int:
    """
    Counts tokens in a list of chat messages.
    
    Accounts for OpenAI/Claude message structure:
    - role: ~1 token
    - content: text tokens
    - Service tokens between messages: ~3-4 tokens
    
    Args:
        messages: List of messages in OpenAI format
        apply_claude_correction: Apply correction coefficient for Claude
    
    Returns:
        Approximate number of tokens (with Claude correction)
    """
    if not messages:
        return 0
    
    total_tokens = 0
    
    for message in messages:
        # Base tokens per message (role, delimiters)
        total_tokens += 4  # ~4 tokens for service information
        
        # Role tokens (without correction, these are short strings)
        role = message.get("role", "")
        total_tokens += count_tokens(role, apply_claude_correction=False)
        
        # Content tokens
        content = message.get("content")
        if content:
            if isinstance(content, str):
                total_tokens += count_tokens(content, apply_claude_correction=False)
            elif isinstance(content, list):
                # Multimodal content (text + images)
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            total_tokens += count_tokens(item.get("text", ""), apply_claude_correction=False)
                        elif item.get("type") == "image_url":
                            # Images take ~85-170 tokens depending on size
                            total_tokens += 100  # Average estimate
        
        # tool_calls tokens (if present)
        tool_calls = message.get("tool_calls")
        if tool_calls:
            for tc in tool_calls:
                total_tokens += 4  # Service tokens
                func = tc.get("function", {})
                total_tokens += count_tokens(func.get("name", ""), apply_claude_correction=False)
                total_tokens += count_tokens(func.get("arguments", ""), apply_claude_correction=False)
        
        # tool_call_id tokens (for tool responses)
        if message.get("tool_call_id"):
            total_tokens += count_tokens(message["tool_call_id"], apply_claude_correction=False)
    
    # Final service tokens
    total_tokens += 3
    
    # Apply correction to total count
    if apply_claude_correction:
        return int(total_tokens * CLAUDE_CORRECTION_FACTOR)
    return total_tokens


def count_tools_tokens(tools: Optional[List[Dict[str, Any]]], apply_claude_correction: bool = True) -> int:
    """
    Counts tokens in tool definitions.
    
    Args:
        tools: List of tools in OpenAI format
        apply_claude_correction: Apply correction coefficient for Claude
    
    Returns:
        Approximate number of tokens (with Claude correction)
    """
    if not tools:
        return 0
    
    total_tokens = 0
    
    for tool in tools:
        total_tokens += 4  # Service tokens
        
        if tool.get("type") == "function":
            func = tool.get("function", {})
            
            # Function name
            total_tokens += count_tokens(func.get("name", ""), apply_claude_correction=False)
            
            # Function description
            total_tokens += count_tokens(func.get("description", ""), apply_claude_correction=False)
            
            # Parameters (JSON schema)
            params = func.get("parameters")
            if params:
                import json
                params_str = json.dumps(params, ensure_ascii=False)
                total_tokens += count_tokens(params_str, apply_claude_correction=False)
    
    # Apply correction to total count
    if apply_claude_correction:
        return int(total_tokens * CLAUDE_CORRECTION_FACTOR)
    return total_tokens


def count_anthropic_content_block_tokens(block: Dict[str, Any]) -> int:
    """
    Counts tokens in a single Anthropic content block.

    Handles all Anthropic content block types:
    - text: tokenizes the text field
    - thinking: tokenizes the thinking field
    - image: estimates ~100 tokens per image (varies by size)
    - tool_use: tokenizes name + JSON-serialized input
    - tool_result: tokenizes tool_use_id + content (recursive for nested blocks)

    Args:
        block: Anthropic content block dict with "type" field

    Returns:
        Approximate number of tokens (without Claude correction)
    """
    import json

    block_type = block.get("type", "")
    tokens = 0

    if block_type == "text":
        tokens += count_tokens(block.get("text", ""), apply_claude_correction=False)

    elif block_type == "thinking":
        tokens += count_tokens(block.get("thinking", ""), apply_claude_correction=False)

    elif block_type == "image":
        # Images take ~85-170 tokens depending on size/resolution
        tokens += 100

    elif block_type == "tool_use":
        tokens += 4  # Service tokens for tool_use structure
        tokens += count_tokens(block.get("name", ""), apply_claude_correction=False)
        tool_input = block.get("input", {})
        if tool_input:
            input_str = json.dumps(tool_input, ensure_ascii=False) if not isinstance(tool_input, str) else tool_input
            tokens += count_tokens(input_str, apply_claude_correction=False)

    elif block_type == "tool_result":
        tokens += 4  # Service tokens for tool_result structure
        tokens += count_tokens(block.get("tool_use_id", ""), apply_claude_correction=False)
        result_content = block.get("content", "")
        if isinstance(result_content, str):
            tokens += count_tokens(result_content, apply_claude_correction=False)
        elif isinstance(result_content, list):
            # Nested content blocks inside tool_result (text, images)
            for nested_block in result_content:
                if isinstance(nested_block, dict):
                    tokens += count_anthropic_content_block_tokens(nested_block)

    return tokens


def count_anthropic_message_tokens(
    messages: List[Dict[str, Any]],
    apply_claude_correction: bool = True,
) -> int:
    """
    Counts tokens in a list of Anthropic-format messages.

    Handles Anthropic message structure where content can be:
    - A plain string
    - A list of typed content blocks (text, image, tool_use, tool_result, thinking)

    Per Anthropic docs: thinking blocks from previous assistant turns are
    ignored and do NOT count toward input tokens. Since all assistant messages
    in the input are previous turns, we skip thinking blocks in assistant messages.

    Args:
        messages: List of messages in Anthropic format
            Each message has "role" (user/assistant) and "content" (str or list)
        apply_claude_correction: Apply correction coefficient for Claude

    Returns:
        Approximate number of tokens (with Claude correction if enabled)
    """
    if not messages:
        return 0

    total_tokens = 0

    for message in messages:
        # Base tokens per message (role, delimiters)
        total_tokens += 4

        # Role tokens
        role = message.get("role", "")
        total_tokens += count_tokens(role, apply_claude_correction=False)

        # Content tokens
        content = message.get("content")
        if content:
            if isinstance(content, str):
                total_tokens += count_tokens(content, apply_claude_correction=False)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        # Per Anthropic docs: thinking blocks from previous
                        # assistant turns are ignored (not billed as input tokens).
                        # All assistant messages in the request are previous turns.
                        if role == "assistant" and block.get("type") == "thinking":
                            continue
                        total_tokens += count_anthropic_content_block_tokens(block)

    # Final service tokens
    total_tokens += 3

    if apply_claude_correction:
        return int(total_tokens * CLAUDE_CORRECTION_FACTOR)
    return total_tokens


def count_anthropic_tools_tokens(
    tools: Optional[List[Dict[str, Any]]],
    apply_claude_correction: bool = True,
) -> int:
    """
    Counts tokens in Anthropic-format tool definitions.

    Anthropic tools use a different structure than OpenAI:
    - name: Tool name
    - description: Tool description
    - input_schema: JSON Schema for parameters

    Args:
        tools: List of tools in Anthropic format
        apply_claude_correction: Apply correction coefficient for Claude

    Returns:
        Approximate number of tokens (with Claude correction if enabled)
    """
    import json

    if not tools:
        return 0

    total_tokens = 0

    for tool in tools:
        total_tokens += 4  # Service tokens per tool

        # Tool name
        total_tokens += count_tokens(tool.get("name", ""), apply_claude_correction=False)

        # Tool description
        description = tool.get("description", "")
        if description:
            total_tokens += count_tokens(description, apply_claude_correction=False)

        # Input schema (JSON Schema)
        input_schema = tool.get("input_schema")
        if input_schema:
            schema_str = json.dumps(input_schema, ensure_ascii=False)
            total_tokens += count_tokens(schema_str, apply_claude_correction=False)

    if apply_claude_correction:
        return int(total_tokens * CLAUDE_CORRECTION_FACTOR)
    return total_tokens


def count_anthropic_system_tokens(
    system: Any,
    apply_claude_correction: bool = True,
) -> int:
    """
    Counts tokens in an Anthropic system prompt.

    Anthropic system can be:
    - A plain string: "You are helpful"
    - A list of content blocks: [{"type": "text", "text": "...", "cache_control": {...}}]

    Args:
        system: System prompt in string or list format
        apply_claude_correction: Apply correction coefficient for Claude

    Returns:
        Approximate number of tokens (with Claude correction if enabled)
    """
    if not system:
        return 0

    if isinstance(system, str):
        return count_tokens(system, apply_claude_correction=apply_claude_correction)

    if isinstance(system, list):
        total_tokens = 0
        for block in system:
            if isinstance(block, dict):
                text = block.get("text", "")
                if text:
                    total_tokens += count_tokens(text, apply_claude_correction=False)
            elif hasattr(block, "text"):
                total_tokens += count_tokens(getattr(block, "text", ""), apply_claude_correction=False)

        if apply_claude_correction:
            return int(total_tokens * CLAUDE_CORRECTION_FACTOR)
        return total_tokens

    return count_tokens(str(system), apply_claude_correction=apply_claude_correction)


def estimate_anthropic_request_tokens(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    system: Any = None,
) -> int:
    """
    Estimates total input tokens for an Anthropic API request.

    Combines token counts from messages, tools, and system prompt
    to produce a single input_tokens value matching the Anthropic
    count_tokens API response format.

    Args:
        messages: List of messages in Anthropic format
        tools: List of tools in Anthropic format (optional)
        system: System prompt - string or list of content blocks (optional)

    Returns:
        Estimated total input tokens
    """
    messages_tokens = count_anthropic_message_tokens(messages)
    tools_tokens = count_anthropic_tools_tokens(tools)
    system_tokens = count_anthropic_system_tokens(system)

    return messages_tokens + tools_tokens + system_tokens


def estimate_request_tokens(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    system_prompt: Optional[str] = None
) -> Dict[str, int]:
    """
    Estimates total number of tokens in request.
    
    Args:
        messages: List of messages
        tools: List of tools (optional)
        system_prompt: System prompt (optional, if not in messages)
    
    Returns:
        Dictionary with token breakdown:
        - messages_tokens: message tokens
        - tools_tokens: tool tokens
        - system_tokens: system prompt tokens
        - total_tokens: total count
    """
    messages_tokens = count_message_tokens(messages)
    tools_tokens = count_tools_tokens(tools)
    system_tokens = count_tokens(system_prompt) if system_prompt else 0
    
    return {
        "messages_tokens": messages_tokens,
        "tools_tokens": tools_tokens,
        "system_tokens": system_tokens,
        "total_tokens": messages_tokens + tools_tokens + system_tokens
    }