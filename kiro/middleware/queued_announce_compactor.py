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
Queued announce compactor middleware.

OpenClaw and similar agentic clients inject large "queued announce" blocks
into user messages when subagents complete work while the main agent is busy.
These blocks can contain thousands of lines of subagent output, rapidly
inflating the context window and triggering "Improperly formed request" errors.

This middleware detects and compacts these blocks to a configurable size,
preserving the head and tail for context while removing the middle.
"""

from typing import List

from loguru import logger

from kiro.converters_core import UnifiedMessage

# Detection markers for queued announce blocks
_QUEUED_ANNOUNCE_MARKER = "[Queued announce messages while agent was busy]"
_QUEUED_ANNOUNCE_TASK_MARKER = 'A background task "'
_QUEUED_ANNOUNCE_FINDINGS_MARKER = "Findings:"


def _is_queued_announce(text: str) -> bool:
    """Detect OpenClaw queued-announce system notice blocks."""
    if _QUEUED_ANNOUNCE_MARKER in text:
        return True
    if (
        _QUEUED_ANNOUNCE_TASK_MARKER in text
        and _QUEUED_ANNOUNCE_FINDINGS_MARKER in text
    ):
        return True
    return False


def _compact_text(
    text: str,
    max_chars: int,
    head_chars: int,
    tail_chars: int,
) -> str:
    """
    Compact text by keeping head and tail, removing middle.

    Args:
        text: Full text to compact
        max_chars: Maximum allowed characters
        head_chars: Characters to keep from start
        tail_chars: Characters to keep from end

    Returns:
        Compacted text if over limit, original otherwise
    """
    if len(text) <= max_chars:
        return text

    # Ensure head + tail don't exceed max
    if head_chars + tail_chars >= max_chars:
        head_chars = max_chars // 2
        tail_chars = max_chars - head_chars

    head = text[:head_chars]
    tail = text[-tail_chars:] if tail_chars > 0 else ""
    omitted = len(text) - head_chars - tail_chars
    notice = (
        "\n\n[Gateway notice] Queued-announce findings truncated "
        f"({omitted:,} chars omitted) to avoid upstream validation errors.\n\n"
    )

    return f"{head}{notice}{tail}"


def compact_queued_announces(
    messages: List[UnifiedMessage],
    max_chars: int = 8_000,
    head_chars: int = 2_000,
    tail_chars: int = 2_000,
) -> List[UnifiedMessage]:
    """
    Detect and compact queued announce blocks in user messages.

    Args:
        messages: List of UnifiedMessage objects
        max_chars: Maximum characters for a queued announce block
        head_chars: Characters to preserve from start
        tail_chars: Characters to preserve from end

    Returns:
        Messages with compacted queued announce blocks
    """
    if max_chars <= 0 or not messages:
        return messages

    compacted_count = 0

    for msg in messages:
        if msg.role != "user":
            continue
        if isinstance(msg.content, str):
            if not _is_queued_announce(msg.content):
                continue
            if len(msg.content) <= max_chars:
                continue

            original_size = len(msg.content)
            msg.content = _compact_text(msg.content, max_chars, head_chars, tail_chars)
            compacted_count += 1

            logger.warning(
                "[QueuedAnnounceCompactor] Compacted queued announce: {} -> {} chars",
                original_size,
                len(msg.content),
            )
            continue

        if isinstance(msg.content, list):
            for block in msg.content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "text":
                    continue

                text = block.get("text", "")
                if not isinstance(text, str):
                    continue
                if not _is_queued_announce(text):
                    continue
                if len(text) <= max_chars:
                    continue

                original_size = len(text)
                block["text"] = _compact_text(text, max_chars, head_chars, tail_chars)
                compacted_count += 1

                logger.warning(
                    "[QueuedAnnounceCompactor] Compacted queued announce block: {} -> {} chars",
                    original_size,
                    len(block["text"]),
                )

    if compacted_count > 0:
        logger.warning(
            "[QueuedAnnounceCompactor] Completed: compacted={} blocks",
            compacted_count,
        )

    return messages
