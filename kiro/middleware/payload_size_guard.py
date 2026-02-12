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
Payload size guard middleware.

Enforces per-tool and total size budgets on tool_result and tool_call payloads
to prevent upstream "Improperly formed request" errors caused by oversized content.

This is a refactored extraction of the guard logic previously embedded in
converters_core.py (apply_tool_result_guard, _is_tool_args_oversized, etc.)
into a proper middleware with clean interfaces.

Strategy:
  - Historical tool results (not in the last message) are aggressively trimmed
  - Active tool results (last message) are converted to tool errors for the model
  - Total budget is enforced by evicting largest historical entries first
  - Tool call arguments exceeding limits are replaced with empty objects
"""

import json
import re
from typing import Any, Dict, List, Tuple

from loguru import logger

from kiro.converters_core import UnifiedMessage

# Regex patterns for sanitizing tool output
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _stringify_content(content: Any) -> str:
    """Convert tool_result content to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return str(content) if content else ""


def _sanitize_text(text: str) -> str:
    """Remove ANSI escapes and control characters from tool output."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    without_ansi = _ANSI_ESCAPE_RE.sub("", normalized)
    return _CONTROL_CHAR_RE.sub("", without_ansi)


def _check_tool_args_oversized(arguments: Any, max_chars: int) -> Tuple[bool, int]:
    """Check whether tool call arguments exceed the configured limit."""
    if max_chars <= 0:
        return False, 0

    if isinstance(arguments, str):
        size = len(arguments)
    else:
        try:
            rendered = json.dumps(arguments, ensure_ascii=False)
        except (TypeError, ValueError):
            rendered = str(arguments)
        size = len(rendered)

    return size > max(256, max_chars), size


def enforce_tool_result_limits(
    messages: List[UnifiedMessage],
    per_result_max_chars: int = 50_000,
    total_max_chars: int = 200_000,
) -> List[UnifiedMessage]:
    """
    Enforce size limits on tool_result payloads across the conversation.

    Args:
        messages: List of UnifiedMessage objects
        per_result_max_chars: Maximum characters per individual tool_result
        total_max_chars: Maximum total characters across all tool_results

    Returns:
        Messages with oversized tool_results trimmed or replaced
    """
    if not messages:
        return messages

    max_chars = max(256, per_result_max_chars)
    total_limit = max(max_chars, total_max_chars)

    # Collect all tool_result entries with metadata
    entries: List[Dict[str, Any]] = []
    total_chars = 0
    last_msg_idx = len(messages) - 1

    for msg_idx, msg in enumerate(messages):
        if not msg.tool_results:
            continue
        for entry in msg.tool_results:
            if not isinstance(entry, dict):
                continue
            content_text = _sanitize_text(_stringify_content(entry.get("content", "")))
            size = len(content_text)
            total_chars += size
            entries.append(
                {
                    "ref": entry,
                    "tool_use_id": str(entry.get("tool_use_id", "unknown")),
                    "size": size,
                    "is_active": msg_idx == last_msg_idx,
                }
            )

    if not entries:
        return messages

    omitted_historical = 0
    converted_active = 0

    def _replace(item: Dict[str, Any], replacement: str) -> None:
        nonlocal total_chars
        old_size = item["size"]
        item["ref"]["content"] = replacement
        item["size"] = len(replacement)
        total_chars -= old_size - len(replacement)

    def _mark_error(item: Dict[str, Any], reason: str) -> None:
        error_text = (
            "[Tool output omitted by gateway]\n"
            f"tool_use_id={item['tool_use_id']}\n"
            f"reason={reason}\n"
            "retry_hint=use head/tail/grep/filter and retry"
        )
        _replace(item, error_text)
        item["ref"]["is_error"] = True
        item["ref"]["status"] = "error"

    historical = [e for e in entries if not e["is_active"]]
    active = [e for e in entries if e["is_active"]]

    # 1) Per-tool limit on historical results
    for item in historical:
        if item["size"] > max_chars:
            _replace(
                item,
                f"(historical tool output omitted by gateway: "
                f"{item['size']:,} chars > per-tool limit {max_chars:,})",
            )
            omitted_historical += 1

    # 2) Total budget recovery: evict largest historical first
    if total_chars > total_limit:
        for item in sorted(historical, key=lambda x: x["size"], reverse=True):
            if total_chars <= total_limit:
                break
            marker = (
                "(historical tool output omitted by gateway: total budget recovery)"
            )
            if item["size"] <= len(marker):
                continue
            _replace(item, marker)
            omitted_historical += 1

    # 3) Active entries over per-tool limit → tool error
    for item in active:
        if item["size"] > max_chars:
            _mark_error(item, "output_too_large")
            converted_active += 1

    # 4) If still over total budget, convert active entries
    if total_chars > total_limit:
        for item in sorted(active, key=lambda x: x["size"], reverse=True):
            if total_chars <= total_limit:
                break
            if item["ref"].get("status") == "error":
                continue
            _mark_error(item, "total_budget_exceeded")
            converted_active += 1

    # 5) Last-resort hard clamp
    if total_chars > total_limit:
        for item in historical:
            if total_chars <= total_limit:
                break
            marker = "(historical tool output omitted by gateway)"
            if item["size"] <= len(marker):
                continue
            _replace(item, marker)
            omitted_historical += 1

    if total_chars > total_limit:
        for item in active:
            if total_chars <= total_limit:
                break
            _mark_error(item, "hard_budget_clamp")

    if omitted_historical > 0 or converted_active > 0:
        logger.warning(
            "[PayloadSizeGuard] tool_result limits applied: "
            "omitted_historical={}, converted_active={}, "
            "total_chars={}, total_limit={}",
            omitted_historical,
            converted_active,
            total_chars,
            total_limit,
        )

    return messages


def enforce_tool_call_args_limits(
    messages: List[UnifiedMessage],
    max_chars: int = 50_000,
) -> List[UnifiedMessage]:
    """
    Enforce size limits on tool_call argument payloads.

    Oversized tool call arguments are replaced with empty objects to prevent
    upstream validation errors.

    Args:
        messages: List of UnifiedMessage objects
        max_chars: Maximum characters for tool call arguments

    Returns:
        Messages with oversized tool_call arguments replaced
    """
    if max_chars <= 0 or not messages:
        return messages

    replaced_count = 0

    for msg in messages:
        if not msg.tool_calls:
            continue
        for call in msg.tool_calls:
            func = call.get("function", {})
            args = func.get("arguments")
            if args is None:
                continue

            is_oversized, size = _check_tool_args_oversized(args, max_chars)
            if is_oversized:
                func["arguments"] = {}
                replaced_count += 1
                logger.warning(
                    "[PayloadSizeGuard] Tool call arguments omitted: "
                    "{} chars > {} limit",
                    size,
                    max(256, max_chars),
                )

    if replaced_count > 0:
        logger.warning(
            "[PayloadSizeGuard] tool_call args limits applied: replaced={}",
            replaced_count,
        )

    return messages
