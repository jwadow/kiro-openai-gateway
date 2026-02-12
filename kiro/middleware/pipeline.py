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
Middleware pipeline orchestrator.

Runs all message and tool validation middleware in the correct order.
This is the single entry point called by converters_core.build_kiro_payload().

Execution order matters:
  1. ToolPairingValidator  - Must run first to fix structural pairing issues
  2. MessageStructureValidator - Fixes role alternation after pairing repairs
  3. QueuedAnnounceCompactor - Compact large injected blocks before size checks
  4. PayloadSizeGuard (tool_results) - Enforce per-tool and total size budgets
  5. PayloadSizeGuard (tool_args) - Enforce tool call argument limits

Tool pipeline (separate):
  1. SchemaSanitizer - Clean tool JSON schemas
"""

from typing import List, Optional

from loguru import logger

from kiro.converters_core import UnifiedMessage, UnifiedTool
from kiro.middleware.tool_pairing_validator import validate_tool_pairing
from kiro.middleware.message_structure_validator import validate_message_structure
from kiro.middleware.payload_size_guard import (
    enforce_tool_result_limits,
    enforce_tool_call_args_limits,
)
from kiro.middleware.queued_announce_compactor import compact_queued_announces
from kiro.middleware.schema_sanitizer import sanitize_tool_schemas


def run_message_pipeline(
    messages: List[UnifiedMessage],
    tool_result_max_chars: int = 50_000,
    tool_result_total_max_chars: int = 200_000,
    tool_call_args_max_chars: int = 50_000,
    queued_announce_max_chars: int = 8_000,
    queued_announce_head_chars: int = 2_000,
    queued_announce_tail_chars: int = 2_000,
    enable_tool_pairing: bool = True,
    enable_structure_validation: bool = True,
    enable_size_guards: bool = True,
    enable_queued_announce: bool = True,
) -> List[UnifiedMessage]:
    """
    Run the full message validation pipeline.

    Each middleware is independently toggleable. The pipeline runs in a
    fixed order that ensures correctness (structural fixes before size checks).

    Args:
        messages: List of UnifiedMessage objects to validate
        tool_result_max_chars: Per-tool result size limit
        tool_result_total_max_chars: Total tool result budget
        tool_call_args_max_chars: Per-tool call arguments limit
        queued_announce_max_chars: Max chars for queued announce blocks
        queued_announce_head_chars: Head chars to preserve in compaction
        queued_announce_tail_chars: Tail chars to preserve in compaction
        enable_tool_pairing: Enable tool_use/tool_result pairing validation
        enable_structure_validation: Enable message structure validation
        enable_size_guards: Enable payload size guards
        enable_queued_announce: Enable queued announce compaction

    Returns:
        Validated and repaired message list
    """
    msg_count = len(messages)

    # 1. Fix orphaned tool_use/tool_result blocks
    if enable_tool_pairing:
        messages = validate_tool_pairing(messages)

    # 2. Fix role alternation, empty content, first-message role
    if enable_structure_validation:
        messages = validate_message_structure(messages)

    # 3. Compact large queued announce blocks
    if enable_queued_announce and queued_announce_max_chars > 0:
        messages = compact_queued_announces(
            messages,
            max_chars=queued_announce_max_chars,
            head_chars=queued_announce_head_chars,
            tail_chars=queued_announce_tail_chars,
        )

    # 4. Enforce tool_result size limits
    if enable_size_guards and tool_result_max_chars > 0:
        messages = enforce_tool_result_limits(
            messages,
            per_result_max_chars=tool_result_max_chars,
            total_max_chars=tool_result_total_max_chars,
        )

    # 5. Enforce tool_call arguments size limits
    if enable_size_guards and tool_call_args_max_chars > 0:
        messages = enforce_tool_call_args_limits(
            messages,
            max_chars=tool_call_args_max_chars,
        )

    if len(messages) != msg_count:
        logger.info(
            "[Pipeline] Message count changed: {} -> {} (synthetic messages injected)",
            msg_count,
            len(messages),
        )

    return messages


def run_tool_pipeline(
    tools: Optional[List[UnifiedTool]],
) -> Optional[List[UnifiedTool]]:
    """
    Run the tool definition validation pipeline.

    Args:
        tools: List of UnifiedTool objects, or None

    Returns:
        Validated and sanitized tools list
    """
    if not tools:
        return tools

    # 1. Sanitize JSON schemas and tool names
    tools = sanitize_tool_schemas(tools)

    return tools
