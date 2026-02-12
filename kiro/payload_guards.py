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
Payload-level guards for Kiro request bodies.

This module handles only payload-envelope safeguards that are specific to Kiro
upstream behavior:

1) Empty assistant toolUses arrays are stripped.
2) Oversized payloads are trimmed by removing oldest history entries.
3) Orphaned toolResults created by trimming are repaired.

These guards operate on already-built Kiro payloads, not raw client messages.
"""

from dataclasses import dataclass
import json
from typing import Any, Dict, List, Tuple


@dataclass
class PayloadGuardConfig:
    """Configuration for payload-level guard behavior."""

    max_payload_bytes: int
    max_history_entries: int = 0
    orphaned_marker: str = "[Orphaned tool result]"


@dataclass
class PayloadGuardStats:
    """Execution stats emitted by payload guards."""

    original_payload_bytes: int = 0
    final_payload_bytes: int = 0
    original_history_entries: int = 0
    final_history_entries: int = 0
    stripped_empty_tool_uses: int = 0
    removed_orphaned_history_tool_results: int = 0
    removed_orphaned_current_tool_results: int = 0


def apply_payload_guards(
    payload: Dict[str, Any],
    config: PayloadGuardConfig,
) -> PayloadGuardStats:
    """
    Apply Kiro payload envelope guards in a deterministic order.

    Args:
        payload: Kiro payload object (modified in place)
        config: Guard configuration

    Returns:
        PayloadGuardStats with mutation counters and size metrics
    """
    stats = PayloadGuardStats()
    stats.original_payload_bytes = _payload_size_bytes(payload)

    history = _get_history(payload)
    stats.original_history_entries = len(history)

    if history:
        stats.stripped_empty_tool_uses = _strip_empty_tool_uses(history)
        history = _trim_history_to_limits(payload, history, config)
        _repair_orphaned_tool_results(payload, history, config, stats)

    stats.final_history_entries = len(_get_history(payload))
    stats.final_payload_bytes = _payload_size_bytes(payload)
    return stats


def _payload_size_bytes(payload: Dict[str, Any]) -> int:
    """Return UTF-8 serialized payload size in bytes."""
    return len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))


def _get_history(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Read payload history safely."""
    state = payload.get("conversationState", {})
    history = state.get("history", [])
    if isinstance(history, list):
        return history
    return []


def _set_history(payload: Dict[str, Any], history: List[Dict[str, Any]]) -> None:
    """Write payload history, removing field when empty."""
    state = payload.setdefault("conversationState", {})
    if history:
        state["history"] = history
    else:
        state.pop("history", None)


def _strip_empty_tool_uses(history: List[Dict[str, Any]]) -> int:
    """Strip empty assistantResponseMessage.toolUses arrays from history."""
    removed = 0
    for entry in history:
        arm = entry.get("assistantResponseMessage")
        if not isinstance(arm, dict):
            continue
        tool_uses = arm.get("toolUses")
        if isinstance(tool_uses, list) and len(tool_uses) == 0:
            arm.pop("toolUses", None)
            removed += 1
    return removed


def _align_start_to_user(history: List[Dict[str, Any]], start_idx: int) -> int:
    """Move window start to the next userInputMessage entry."""
    i = max(0, start_idx)
    n = len(history)
    while i < n and "userInputMessage" not in history[i]:
        i += 1
    return i


def _trim_history_to_limits(
    payload: Dict[str, Any],
    history: List[Dict[str, Any]],
    config: PayloadGuardConfig,
) -> List[Dict[str, Any]]:
    """
    Trim oldest history entries to satisfy configured history and payload limits.

    Strategy:
      - Optional hard cap by history count (disabled when max_history_entries == 0)
      - Payload-bytes cap by advancing window start from oldest messages
      - Always align history start to a user entry for Kiro compatibility
    """
    start_idx = 0
    total = len(history)

    if config.max_history_entries > 0 and total > config.max_history_entries:
        start_idx = total - config.max_history_entries
        start_idx = _align_start_to_user(history, start_idx)

    trimmed = history[start_idx:]
    _set_history(payload, trimmed)

    # Enforce payload-byte cap
    while (
        _payload_size_bytes(payload) > config.max_payload_bytes
        and len(trimmed) > 2
        and start_idx < total
    ):
        # Drop roughly one user/assistant pair per iteration.
        start_idx += 2
        start_idx = _align_start_to_user(history, start_idx)
        trimmed = history[start_idx:]
        _set_history(payload, trimmed)

    return trimmed


def _tool_use_ids(entry: Dict[str, Any]) -> List[str]:
    """Extract toolUse IDs from an assistant history entry."""
    arm = entry.get("assistantResponseMessage")
    if not isinstance(arm, dict):
        return []
    tool_uses = arm.get("toolUses", [])
    if not isinstance(tool_uses, list):
        return []
    ids = []
    for tool_use in tool_uses:
        if isinstance(tool_use, dict):
            tool_use_id = tool_use.get("toolUseId")
            if isinstance(tool_use_id, str) and tool_use_id:
                ids.append(tool_use_id)
    return ids


def _extract_tool_result_text(tool_result: Dict[str, Any]) -> str:
    """Extract human-readable text from toolResult content."""
    content = tool_result.get("content", [])
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""

    parts: List[str] = []
    for block in content:
        if isinstance(block, dict):
            text = block.get("text")
            if isinstance(text, str) and text:
                parts.append(text)
    return "\n".join(parts).strip()


def _repair_tool_results_against_allowed_ids(
    user_message: Dict[str, Any],
    allowed_tool_use_ids: List[str],
    marker: str,
) -> Tuple[int, int]:
    """
    Remove orphaned toolResults from one user message and preserve text in content.

    Returns:
        (removed_count, preserved_count)
    """
    if not isinstance(user_message, dict):
        return 0, 0

    ctx = user_message.get("userInputMessageContext", {})
    if not isinstance(ctx, dict):
        return 0, 0

    tool_results = ctx.get("toolResults")
    if not isinstance(tool_results, list) or not tool_results:
        return 0, 0

    allowed = set(allowed_tool_use_ids)
    valid_results: List[Dict[str, Any]] = []
    preserved_texts: List[str] = []
    removed = 0

    for tool_result in tool_results:
        if not isinstance(tool_result, dict):
            removed += 1
            continue

        tool_use_id = tool_result.get("toolUseId")
        if isinstance(tool_use_id, str) and tool_use_id in allowed:
            valid_results.append(tool_result)
            continue

        removed += 1
        preserved = _extract_tool_result_text(tool_result)
        if preserved:
            preserved_texts.append(preserved)

    if preserved_texts:
        existing = user_message.get("content")
        existing_text = existing if isinstance(existing, str) else ""
        merged = f"{existing_text}\n\n{marker}\n" + "\n\n".join(preserved_texts)
        user_message["content"] = merged.strip()

    if valid_results:
        ctx["toolResults"] = valid_results
        user_message["userInputMessageContext"] = ctx
    else:
        ctx.pop("toolResults", None)
        if ctx:
            user_message["userInputMessageContext"] = ctx
        else:
            user_message.pop("userInputMessageContext", None)

    return removed, len(preserved_texts)


def _repair_orphaned_tool_results(
    payload: Dict[str, Any],
    history: List[Dict[str, Any]],
    config: PayloadGuardConfig,
    stats: PayloadGuardStats,
) -> None:
    """Repair orphaned toolResults in history and current message after trimming."""
    # History: each user entry is validated against the immediately preceding assistant.
    for idx, entry in enumerate(history):
        user_msg = entry.get("userInputMessage")
        if not isinstance(user_msg, dict):
            continue

        prev_ids: List[str] = []
        if idx > 0:
            prev_ids = _tool_use_ids(history[idx - 1])

        removed, _ = _repair_tool_results_against_allowed_ids(
            user_msg,
            prev_ids,
            config.orphaned_marker,
        )
        stats.removed_orphaned_history_tool_results += removed

    # Current message: validate against the last assistant from history.
    conversation_state = payload.get("conversationState", {})
    current_message = conversation_state.get("currentMessage", {})
    user_msg = current_message.get("userInputMessage")
    if isinstance(user_msg, dict):
        allowed_current_ids: List[str] = []
        if history:
            allowed_current_ids = _tool_use_ids(history[-1])

        removed, _ = _repair_tool_results_against_allowed_ids(
            user_msg,
            allowed_current_ids,
            config.orphaned_marker,
        )
        stats.removed_orphaned_current_tool_results += removed
