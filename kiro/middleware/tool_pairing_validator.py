# -*- coding: utf-8 -*-

# Kiro Gateway
# https://github.com/jwadow/kiro-gateway
# Copyright (C) 2025 Jwadow
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Tool pairing validator middleware.

Ensures every tool_use block in an assistant message has a corresponding
tool_result block in the immediately following user message, and vice versa.

This is the single most impactful fix for "Improperly formed request" errors.
Orphaned tool_use/tool_result blocks are the #1 cause of HTTP 400 from the
Anthropic/Kiro API, especially during:
  - Subagent execution (OpenClaw injects multiple tool calls in one message)
  - Context truncation / compaction
  - Parallel tool call timeouts
  - Streaming interruptions

References:
  - Claude Code issues: #8894, #21041, #13964, #14173, #8004, #1894
  - BetterClaude Gateway: github.com/AkideLiu/betterclaude-workers
  - Anthropic API rule: "Each tool_use block must have a corresponding
    tool_result block in the next message"
"""

from typing import Any, Dict, List, Set

from loguru import logger

from kiro.converters_core import UnifiedMessage


def _collect_tool_use_ids(message: UnifiedMessage) -> Set[str]:
    """Extract all tool_use IDs from an assistant message's tool_calls."""
    ids: Set[str] = set()
    if not message.tool_calls:
        return ids
    for call in message.tool_calls:
        call_id = call.get("id") or ""
        if call_id:
            ids.add(call_id)
    return ids


def _collect_tool_result_ids(message: UnifiedMessage) -> Set[str]:
    """Extract all tool_use_ids referenced by tool_results in a user message."""
    ids: Set[str] = set()
    if not message.tool_results:
        return ids
    for result in message.tool_results:
        ref_id = result.get("tool_use_id") or ""
        if ref_id:
            ids.add(ref_id)
    return ids


def _make_placeholder_tool_result(tool_use_id: str) -> Dict[str, Any]:
    """
    Create a synthetic tool_result for an orphaned tool_use.

    The result is marked as an error so the model knows the tool call
    was interrupted and should not be retried blindly.
    """
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": (
            "[Gateway] Tool call was interrupted or its result was lost. "
            "Do not retry the same operation blindly."
        ),
        "is_error": True,
    }


def _make_placeholder_tool_use(tool_use_id: str) -> Dict[str, Any]:
    """
    Create a synthetic tool_use for an orphaned tool_result.

    This is a last-resort patch: if a tool_result references a tool_use_id
    that doesn't exist in the preceding assistant message, we inject a
    minimal tool_use so the API doesn't reject the conversation.
    """
    return {
        "id": tool_use_id,
        "type": "function",
        "function": {
            "name": "_gateway_synthetic_tool",
            "arguments": {},
        },
    }


def validate_tool_pairing(
    messages: List[UnifiedMessage],
) -> List[UnifiedMessage]:
    """
    Validate and repair tool_use / tool_result pairing across the message list.

    Anthropic API enforces strict rules:
      1. Every tool_use in an assistant message MUST have a matching tool_result
         in the immediately following user message.
      2. Every tool_result in a user message MUST reference a tool_use_id from
         the immediately preceding assistant message.

    This function scans the conversation and:
      - Injects placeholder tool_results for orphaned tool_use blocks
      - Removes orphaned tool_results that reference non-existent tool_use blocks
      - Handles edge cases: consecutive same-role messages, missing messages

    Strategy: First collect ALL tool_result IDs in the entire conversation to
    distinguish truly orphaned tool_uses from those whose results appear later
    (e.g., after consecutive assistant messages in OpenAI multi-tool patterns).

    Args:
        messages: List of UnifiedMessage objects (modified in-place where safe)

    Returns:
        The repaired message list
    """
    if len(messages) < 2:
        return messages

    repaired_orphaned_uses = 0
    removed_orphaned_results = 0
    injected_synthetic_messages = 0

    # --- Pre-pass: Collect ALL tool_result IDs across the entire conversation ---
    # This prevents false positives when tool_results appear later than expected
    # (e.g., OpenAI pattern: assistant1(tool_use_A) -> assistant2(tool_use_B) -> user(result_A, result_B))
    all_tool_result_ids: Set[str] = set()
    for msg in messages:
        if msg.tool_results:
            for result in msg.tool_results:
                ref_id = result.get("tool_use_id") or ""
                if ref_id:
                    all_tool_result_ids.add(ref_id)

    # --- Pass 1: Fix orphaned tool_use blocks (assistant has tool_use, no matching tool_result anywhere) ---
    i = 0
    while i < len(messages):
        msg = messages[i]

        # Only check assistant messages with tool_calls
        if msg.role != "assistant" or not msg.tool_calls:
            i += 1
            continue

        tool_use_ids = _collect_tool_use_ids(msg)
        if not tool_use_ids:
            i += 1
            continue

        # Check which tool_use IDs have NO matching tool_result anywhere
        truly_orphaned = tool_use_ids - all_tool_result_ids
        if not truly_orphaned:
            i += 1
            continue

        # Find the next message
        next_idx = i + 1

        # Case A: No next message at all (assistant with tool_use is the last message)
        if next_idx >= len(messages):
            synthetic_results = [
                _make_placeholder_tool_result(tid) for tid in truly_orphaned
            ]
            synthetic_user = UnifiedMessage(
                role="user",
                content="",
                tool_results=synthetic_results,
            )
            messages.append(synthetic_user)
            repaired_orphaned_uses += len(truly_orphaned)
            injected_synthetic_messages += 1
            logger.warning(
                "[ToolPairingValidator] Injected synthetic user message with {} "
                "placeholder tool_result(s) at end of conversation",
                len(truly_orphaned),
            )
            i += 2
            continue

        next_msg = messages[next_idx]

        # Case B: Next message is not a user message
        if next_msg.role != "user":
            synthetic_results = [
                _make_placeholder_tool_result(tid) for tid in truly_orphaned
            ]
            synthetic_user = UnifiedMessage(
                role="user",
                content="",
                tool_results=synthetic_results,
            )
            messages.insert(next_idx, synthetic_user)
            repaired_orphaned_uses += len(truly_orphaned)
            injected_synthetic_messages += 1
            logger.warning(
                "[ToolPairingValidator] Injected synthetic user message with {} "
                "placeholder tool_result(s) before message at index {}",
                len(truly_orphaned),
                next_idx,
            )
            i += 2
            continue

        # Case C: Next message IS a user message - check for missing tool_results
        existing_result_ids = _collect_tool_result_ids(next_msg)
        missing_ids = truly_orphaned - existing_result_ids

        if missing_ids:
            if next_msg.tool_results is None:
                next_msg.tool_results = []

            for missing_id in missing_ids:
                next_msg.tool_results.append(_make_placeholder_tool_result(missing_id))
                repaired_orphaned_uses += 1

            logger.warning(
                "[ToolPairingValidator] Added {} placeholder tool_result(s) "
                "to user message at index {} for orphaned tool_use IDs: {}",
                len(missing_ids),
                next_idx,
                missing_ids,
            )

        i += 1

    # --- Pass 2: Remove orphaned tool_results (tool_result references non-existent tool_use) ---
    # Collect ALL tool_use IDs from ALL assistant messages in the conversation.
    # This is necessary because OpenAI-style clients batch tool_results from
    # multiple assistant messages into a single user message.
    all_tool_use_ids: Set[str] = set()
    for msg in messages:
        if msg.role == "assistant" and msg.tool_calls:
            all_tool_use_ids.update(_collect_tool_use_ids(msg))

    for i in range(len(messages)):
        msg = messages[i]

        if msg.role != "user" or not msg.tool_results:
            continue

        # Filter out tool_results that reference non-existent tool_use IDs
        # Preserve their content as text so information is not lost
        valid_results = []
        preserved_text_parts = []
        for result in msg.tool_results:
            ref_id = result.get("tool_use_id") or ""
            if ref_id in all_tool_use_ids:
                valid_results.append(result)
            else:
                # Preserve content as text before removing the structured block
                content = result.get("content", "")
                if content and isinstance(content, str) and content.strip():
                    preserved_text_parts.append(content)
                removed_orphaned_results += 1
                logger.warning(
                    "[ToolPairingValidator] Removed orphaned tool_result "
                    "referencing non-existent tool_use_id='{}' at message index {} "
                    "(content preserved as text)",
                    ref_id,
                    i,
                )

        # Append preserved content to message text
        if preserved_text_parts:
            existing_text = msg.content if isinstance(msg.content, str) else ""
            preserved = "\n".join(preserved_text_parts)
            if existing_text:
                msg.content = existing_text + "\n" + preserved
            else:
                msg.content = preserved

        msg.tool_results = valid_results if valid_results else None

    # --- Summary ---
    total_repairs = repaired_orphaned_uses + removed_orphaned_results
    if total_repairs > 0:
        logger.warning(
            "[ToolPairingValidator] Completed: "
            "repaired_orphaned_uses={}, removed_orphaned_results={}, "
            "injected_synthetic_messages={}",
            repaired_orphaned_uses,
            removed_orphaned_results,
            injected_synthetic_messages,
        )

    return messages
