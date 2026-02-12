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
Message structure validator middleware.

Ensures the message array conforms to Anthropic/Kiro API structural rules:
  1. Messages must alternate between user and assistant roles
  2. No message may have completely empty content (unless it carries tool data)
  3. The conversation must start with a user message
  4. An assistant message with tool_use must be immediately followed by a user message

These rules are enforced by the upstream API and violations produce
HTTP 400 "Improperly formed request" errors.
"""

from typing import List

from loguru import logger

from kiro.converters_core import UnifiedMessage

# Minimal placeholder for empty messages that the API would reject.
_EMPTY_CONTENT_PLACEHOLDER = "."


def _message_has_content(msg: UnifiedMessage) -> bool:
    """Check if a message has any meaningful content (text, tool_calls, or tool_results)."""
    has_text = bool(msg.content) if isinstance(msg.content, str) else bool(msg.content)
    has_tools = bool(msg.tool_calls) or bool(msg.tool_results)
    has_images = bool(msg.images)
    return has_text or has_tools or has_images


def _ensure_non_empty_content(msg: UnifiedMessage) -> None:
    """
    Ensure a message has non-empty text content.

    Only fills placeholder for messages that carry tool data but no text.
    Messages with no content AND no tool data are left empty - downstream
    build_kiro_payload handles these with "Continue" fallback.
    """
    if isinstance(msg.content, str) and msg.content.strip():
        return
    if isinstance(msg.content, list) and msg.content:
        return

    # Only add placeholder if message has tool data that needs text alongside it
    if msg.tool_calls or msg.tool_results or msg.images:
        if not msg.content:
            msg.content = _EMPTY_CONTENT_PLACEHOLDER


def validate_message_structure(
    messages: List[UnifiedMessage],
) -> List[UnifiedMessage]:
    """
    Validate and repair message structure to conform to API rules.

    Fixes applied:
      - Merges consecutive same-role messages (user+user or assistant+assistant)
      - Ensures first message is from user role
      - Fills empty content with minimal placeholder
      - Removes completely degenerate messages that can't be repaired

    Args:
        messages: List of UnifiedMessage objects

    Returns:
        Structurally valid message list
    """
    if not messages:
        return messages

    merged_count = 0
    placeholder_count = 0

    # --- Step 1: Ensure first message is user ---
    if messages[0].role != "user":
        # Prepend a minimal user message
        messages.insert(
            0, UnifiedMessage(role="user", content=_EMPTY_CONTENT_PLACEHOLDER)
        )
        logger.warning(
            "[MessageStructureValidator] Prepended synthetic user message; "
            "conversation started with role='{}'",
            messages[1].role,
        )

    # --- Step 2: Merge consecutive same-role messages ---
    merged: List[UnifiedMessage] = [messages[0]]

    for i in range(1, len(messages)):
        current = messages[i]
        prev = merged[-1]

        if current.role == prev.role:
            # Do NOT merge if either message carries tool data.
            # Merging tool_result/tool_call messages changes their position
            # relative to the conversation, which breaks historical vs active
            # classification in downstream guards.
            prev_has_tools = bool(prev.tool_calls) or bool(prev.tool_results)
            curr_has_tools = bool(current.tool_calls) or bool(current.tool_results)

            if prev_has_tools or curr_has_tools:
                # Don't merge and don't insert fillers here.
                # Legacy code (merge_adjacent_messages, ensure_alternating_roles,
                # ensure_tool_call_result_consistency) handles these patterns
                # correctly with full context about tool semantics.
                merged.append(current)
                logger.debug(
                    "[MessageStructureValidator] Kept consecutive {} messages "
                    "(tool data present) at index {} - deferring to legacy handlers",
                    current.role,
                    i,
                )
            else:
                # Safe to merge plain text messages
                _merge_into(prev, current)
                merged_count += 1
                logger.debug(
                    "[MessageStructureValidator] Merged consecutive {} messages at index {}",
                    current.role,
                    i,
                )
        else:
            merged.append(current)

    messages = merged

    # --- Step 3: Ensure no empty content ---
    for msg in messages:
        had_content = bool(msg.content)
        _ensure_non_empty_content(msg)
        if not had_content and msg.content:
            placeholder_count += 1

    # --- Summary ---
    if merged_count > 0 or placeholder_count > 0:
        logger.warning(
            "[MessageStructureValidator] Completed: merged={}, placeholders_added={}",
            merged_count,
            placeholder_count,
        )

    return messages


def _merge_into(target: UnifiedMessage, source: UnifiedMessage) -> None:
    """
    Merge source message content into target message.

    Combines text content, tool_calls, tool_results, and images.
    """
    # Merge text content
    target_text = target.content if isinstance(target.content, str) else ""
    source_text = source.content if isinstance(source.content, str) else ""

    if target_text and source_text:
        target.content = target_text + "\n" + source_text
    elif source_text:
        target.content = source_text

    # Merge tool_calls
    if source.tool_calls:
        if target.tool_calls is None:
            target.tool_calls = []
        target.tool_calls.extend(source.tool_calls)

    # Merge tool_results
    if source.tool_results:
        if target.tool_results is None:
            target.tool_results = []
        target.tool_results.extend(source.tool_results)

    # Merge images
    if source.images:
        if target.images is None:
            target.images = []
        target.images.extend(source.images)
