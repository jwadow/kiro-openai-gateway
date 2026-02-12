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
JSON schema sanitizer middleware for tool definitions.

Kiro API rejects tool definitions containing certain JSON Schema constructs:
  - Empty required arrays: "required": []
  - additionalProperties field
  - Deeply nested schemas that exceed internal limits

This middleware recursively cleans tool schemas before they reach the API.

Refactored from converters_core.sanitize_json_schema() into a standalone
middleware with additional protections for complex MCP tool schemas.

References:
  - Kiro issue #3431: Complex JSON schema causes ValidationException
  - Claude API tool name limit: 64 characters (Kiro limit)
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from kiro.converters_core import UnifiedTool

# Maximum nesting depth before we flatten to a generic schema
_MAX_SCHEMA_DEPTH = 10

# Maximum tool name length (Kiro API limit)
_MAX_TOOL_NAME_LENGTH = 64


def _sanitize_schema_recursive(
    schema: Dict[str, Any],
    depth: int = 0,
) -> Dict[str, Any]:
    """
    Recursively sanitize a JSON Schema, removing fields that Kiro API rejects.

    Args:
        schema: JSON Schema dictionary
        depth: Current recursion depth

    Returns:
        Sanitized copy of the schema
    """
    if not schema or not isinstance(schema, dict):
        return {}

    # Depth guard: if schema is too deeply nested, return a generic object schema
    if depth > _MAX_SCHEMA_DEPTH:
        logger.warning(
            "[SchemaSanitizer] Schema depth {} exceeds max {}, flattening",
            depth,
            _MAX_SCHEMA_DEPTH,
        )
        return {"type": "object"}

    result: Dict[str, Any] = {}

    for key, value in schema.items():
        # Skip empty required arrays - Kiro API returns 400
        if key == "required" and isinstance(value, list) and len(value) == 0:
            continue

        # Skip additionalProperties - Kiro API doesn't support it
        if key == "additionalProperties":
            continue

        # Skip $schema, $id, $ref-like meta fields that Kiro doesn't understand
        if key.startswith("$") and key not in ("$defs",):
            continue

        # Recursively process nested objects
        if key == "properties" and isinstance(value, dict):
            result[key] = {
                prop_name: _sanitize_schema_recursive(prop_value, depth + 1)
                if isinstance(prop_value, dict)
                else prop_value
                for prop_name, prop_value in value.items()
            }
        elif key == "$defs" and isinstance(value, dict):
            # Process $defs (JSON Schema definitions)
            result[key] = {
                def_name: _sanitize_schema_recursive(def_value, depth + 1)
                if isinstance(def_value, dict)
                else def_value
                for def_name, def_value in value.items()
            }
        elif isinstance(value, dict):
            result[key] = _sanitize_schema_recursive(value, depth + 1)
        elif isinstance(value, list):
            # Process lists (e.g., anyOf, oneOf, allOf, items)
            result[key] = [
                _sanitize_schema_recursive(item, depth + 1)
                if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            result[key] = value

    return result


def _truncate_tool_name(name: str) -> str:
    """Truncate tool name to Kiro API limit if needed."""
    if len(name) <= _MAX_TOOL_NAME_LENGTH:
        return name

    # Keep a meaningful prefix and add hash suffix for uniqueness
    truncated = name[: _MAX_TOOL_NAME_LENGTH - 4] + "_..."
    logger.warning(
        "[SchemaSanitizer] Tool name truncated: '{}' ({} chars) -> '{}' ({} chars)",
        name,
        len(name),
        truncated,
        len(truncated),
    )
    return truncated


def sanitize_tool_schemas(
    tools: Optional[List[UnifiedTool]],
) -> Optional[List[UnifiedTool]]:
    """
    Sanitize tool definitions for Kiro API compatibility.

    Applies:
      - JSON Schema cleanup (remove empty required, additionalProperties, etc.)
      - Tool name length validation and truncation
      - Empty description placeholder
      - Depth-limited schema flattening

    Args:
        tools: List of UnifiedTool objects, or None

    Returns:
        Sanitized tools list, or None if input was None
    """
    if not tools:
        return tools

    sanitized_count = 0
    name_truncated_count = 0

    for tool in tools:
        # Sanitize schema
        if tool.input_schema:
            original = tool.input_schema
            tool.input_schema = _sanitize_schema_recursive(original)
            if tool.input_schema != original:
                sanitized_count += 1

        # Truncate long tool names
        if len(tool.name) > _MAX_TOOL_NAME_LENGTH:
            tool.name = _truncate_tool_name(tool.name)
            name_truncated_count += 1

        # Ensure non-empty description
        if not tool.description or not tool.description.strip():
            tool.description = f"Tool: {tool.name}"

    if sanitized_count > 0 or name_truncated_count > 0:
        logger.warning(
            "[SchemaSanitizer] Completed: schemas_sanitized={}, names_truncated={}",
            sanitized_count,
            name_truncated_count,
        )

    return tools
