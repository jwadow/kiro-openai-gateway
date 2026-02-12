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
Request validation middleware pipeline for Kiro Gateway.

This package provides a layered defense system against malformed API requests
that cause HTTP 400 "Improperly formed request" errors from upstream APIs.

Architecture:
    Each middleware module is a pure function that takes a list of UnifiedMessage
    objects and returns a (possibly modified) list. The pipeline orchestrator
    runs them in a deterministic order before the Kiro payload is built.

Middleware execution order:
    1. ToolPairingValidator  - Fix orphaned tool_use/tool_result blocks
    2. MessageStructureValidator - Fix role alternation, empty content
    3. PayloadSizeGuard - Enforce per-tool and total size budgets
    4. QueuedAnnounceCompactor - Compact infrastructure-generated notices
    5. SchemaSanitizer - Clean tool JSON schemas

References:
    - BetterClaude Gateway (github.com/AkideLiu/betterclaude-workers)
    - Claude Code issues #8894, #21041, #13964, #14173
    - Anthropic API validation rules for tool_use/tool_result pairing
"""

from kiro.middleware.pipeline import run_message_pipeline, run_tool_pipeline

__all__ = ["run_message_pipeline", "run_tool_pipeline"]
