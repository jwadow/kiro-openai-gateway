# -*- coding: utf-8 -*-

"""
Request-driven thinking policy resolver.

This module resolves per-request thinking behavior from:
1. Request body (highest priority)
2. Request headers (fallback)
3. Existing FAKE_REASONING_* defaults (last resort)

It is intentionally stateless and does not modify payload formats.
"""

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple

from loguru import logger

from kiro.config import (
    FAKE_REASONING_ENABLED,
    FAKE_REASONING_MAX_TOKENS,
    THINKING_MIN_TOKENS,
    THINKING_MAX_TOKENS,
    THINKING_OPENAI_MINIMAL_TOKENS,
    THINKING_OPENAI_LOW_TOKENS,
    THINKING_OPENAI_MEDIUM_TOKENS,
    THINKING_OPENAI_HIGH_TOKENS,
    THINKING_OPENAI_XHIGH_TOKENS,
    THINKING_ANTHROPIC_HIGH_TOKENS,
    THINKING_ANTHROPIC_MAX_TOKENS,
)


@dataclass(frozen=True)
class ThinkingPolicy:
    """Resolved thinking policy for a single request.

    Attributes:
        inject_thinking: Whether thinking tags should be injected.
        thinking_max_tokens: Token budget for thinking (None when disabled).
        normalized_level: Internal normalized level label.
        source: Source of policy decision (for diagnostics/logging).
    """

    inject_thinking: bool
    thinking_max_tokens: Optional[int]
    normalized_level: Optional[str]
    source: str


def _normalize_headers(headers: Optional[Mapping[str, str]]) -> Dict[str, str]:
    """Return lowercase header map.

    Args:
        headers: Raw request headers.

    Returns:
        Dictionary with lowercase header names.
    """

    if not headers:
        return {}
    return {str(k).lower(): str(v) for k, v in headers.items()}


def _parse_int_budget(value: Any) -> Optional[int]:
    """Parse a strict integer budget value.

    Args:
        value: Raw budget value.

    Returns:
        Parsed integer if valid, otherwise None.
    """

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None


def _clamp_budget(value: int) -> int:
    """Clamp budget to configured min/max range.

    Args:
        value: Requested budget.

    Returns:
        Clamped budget.
    """

    return max(THINKING_MIN_TOKENS, min(THINKING_MAX_TOKENS, value))


def _default_policy() -> ThinkingPolicy:
    """Return policy from existing FAKE_REASONING defaults."""

    if not FAKE_REASONING_ENABLED:
        return ThinkingPolicy(False, None, "off", "default")
    return ThinkingPolicy(True, FAKE_REASONING_MAX_TOKENS, "default", "default")


def _warn_invalid(field_name: str, value: Any) -> None:
    """Log warning for invalid policy hints.

    Args:
        field_name: Hint field name.
        value: Invalid value.
    """

    logger.warning(f"Ignoring invalid thinking hint: {field_name}={value!r}")


def _openai_budget_for_level(level: str) -> Optional[int]:
    """Map OpenAI normalized effort level to budget.

    Args:
        level: Normalized effort level.

    Returns:
        Token budget or None for off.
    """

    if level == "off":
        return None
    if level == "minimal":
        return THINKING_OPENAI_MINIMAL_TOKENS
    if level == "low":
        return THINKING_OPENAI_LOW_TOKENS
    if level == "medium":
        return THINKING_OPENAI_MEDIUM_TOKENS
    if level == "high":
        return THINKING_OPENAI_HIGH_TOKENS
    if level == "max":
        return THINKING_ANTHROPIC_MAX_TOKENS
    if level == "xhigh":
        return THINKING_OPENAI_XHIGH_TOKENS
    return None


def _normalize_openai_level(value: Any) -> Optional[str]:
    """Normalize OpenAI effort aliases.

    Args:
        value: Raw effort value.

    Returns:
        Normalized level or None for unsupported values.
    """

    if not isinstance(value, str):
        return None
    raw = value.strip().lower()
    if raw in ("none", "off", "disabled"):
        return "off"
    if raw == "on":
        return "high"
    if raw == "minimal":
        return "minimal"
    if raw == "max":
        return "max"
    if raw in ("low", "medium", "high", "xhigh"):
        return raw
    return None


def _normalize_anthropic_level(value: Any) -> Optional[str]:
    """Normalize Anthropics-compatible effort/mode aliases.

    Args:
        value: Raw effort value.

    Returns:
        Normalized level or None.
    """

    if not isinstance(value, str):
        return None
    raw = value.strip().lower()
    if raw in ("none", "off", "disabled"):
        return "off"
    if raw == "max" or raw == "xhigh":
        return "max"
    if raw in ("high", "medium", "low", "minimal", "adaptive", "enabled"):
        return "high"
    return None


def _parse_body_budget_openai(request_data: Mapping[str, Any]) -> Optional[int]:
    """Extract explicit numeric budget from OpenAI-compatible request body.

    Args:
        request_data: Request payload dictionary.

    Returns:
        Parsed budget or None.
    """

    direct_candidates = (
        request_data.get("thinking_budget"),
        request_data.get("reasoning_budget"),
        request_data.get("max_thinking_tokens"),
        request_data.get("thinkingBudget"),
        request_data.get("reasoningBudget"),
        request_data.get("maxThinkingTokens"),
    )
    for value in direct_candidates:
        parsed = _parse_int_budget(value)
        if parsed is not None:
            return parsed

    reasoning = request_data.get("reasoning")
    if isinstance(reasoning, Mapping):
        nested_candidates = (
            reasoning.get("budget_tokens"),
            reasoning.get("max_tokens"),
            reasoning.get("max_output_tokens"),
            reasoning.get("budgetTokens"),
            reasoning.get("maxTokens"),
            reasoning.get("maxOutputTokens"),
        )
        for value in nested_candidates:
            parsed = _parse_int_budget(value)
            if parsed is not None:
                return parsed

    return None


def _parse_body_effort_openai(request_data: Mapping[str, Any]) -> Optional[str]:
    """Extract effort/mode from OpenAI-compatible request body.

    Args:
        request_data: Request payload dictionary.

    Returns:
        Normalized level or None.
    """

    top_level = _normalize_openai_level(
        request_data.get("reasoning_effort") or request_data.get("reasoningEffort")
    )
    if top_level:
        return top_level

    reasoning = request_data.get("reasoning")
    if isinstance(reasoning, Mapping):
        nested = _normalize_openai_level(reasoning.get("effort"))
        if nested:
            return nested
        nested = _normalize_openai_level(reasoning.get("reasoningEffort"))
        if nested:
            return nested

    return None


def _parse_body_budget_anthropic(request_data: Mapping[str, Any]) -> Optional[int]:
    """Extract explicit numeric budget from Anthropic-compatible request body.

    Args:
        request_data: Request payload dictionary.

    Returns:
        Parsed budget or None.
    """

    thinking = request_data.get("thinking")
    if isinstance(thinking, Mapping):
        parsed = _parse_int_budget(thinking.get("budget_tokens"))
        if parsed is None:
            parsed = _parse_int_budget(thinking.get("budgetTokens"))
        if parsed is not None:
            return parsed

    parsed_direct = _parse_int_budget(request_data.get("thinking_budget"))
    if parsed_direct is not None:
        return parsed_direct

    output_config = request_data.get("output_config")
    if output_config is None:
        output_config = request_data.get("outputConfig")
    if isinstance(output_config, Mapping):
        parsed = _parse_int_budget(output_config.get("budget_tokens"))
        if parsed is None:
            parsed = _parse_int_budget(output_config.get("budgetTokens"))
        if parsed is not None:
            return parsed

    return None


def _parse_body_effort_anthropic(request_data: Mapping[str, Any]) -> Optional[str]:
    """Extract effort/mode from Anthropic-compatible request body.

    Args:
        request_data: Request payload dictionary.

    Returns:
        Normalized level or None.
    """

    thinking = request_data.get("thinking")
    if isinstance(thinking, Mapping):
        thinking_type = thinking.get("type")
        if isinstance(thinking_type, str):
            normalized_type = thinking_type.strip().lower()
            if normalized_type == "disabled":
                return "off"
            if normalized_type in ("enabled", "adaptive", "on"):
                return "high"

    output_config = request_data.get("output_config")
    if output_config is None:
        output_config = request_data.get("outputConfig")
    if isinstance(output_config, Mapping):
        effort = _normalize_anthropic_level(output_config.get("effort"))
        if effort:
            return effort

    return None


def _parse_header_budget(
    headers: Mapping[str, str],
) -> Tuple[Optional[int], Optional[str]]:
    """Extract numeric budget from fallback headers.

    Args:
        headers: Normalized lowercase headers.

    Returns:
        Tuple of (budget, source_header).
    """

    value = headers.get("x-thinking-budget")
    if value is None:
        return None, None
    parsed = _parse_int_budget(value)
    if parsed is None:
        _warn_invalid("x-thinking-budget", value)
        return None, None
    return parsed, "x-thinking-budget"


def _parse_header_level_openai(
    headers: Mapping[str, str],
) -> Tuple[Optional[str], Optional[str]]:
    """Extract OpenAI-style effort level from fallback headers.

    Args:
        headers: Normalized lowercase headers.

    Returns:
        Tuple of (level, source_header).
    """

    candidates = (
        ("x-reasoning-effort", _normalize_openai_level),
        ("x-thinking-mode", _normalize_openai_level),
    )
    for name, parser in candidates:
        raw = headers.get(name)
        if raw is None:
            continue
        level = parser(raw)
        if level:
            return level, name
        _warn_invalid(name, raw)
    return None, None


def _parse_header_level_anthropic(
    headers: Mapping[str, str],
) -> Tuple[Optional[str], Optional[str]]:
    """Extract Anthropic-style effort level from fallback headers.

    Args:
        headers: Normalized lowercase headers.

    Returns:
        Tuple of (level, source_header).
    """

    candidates = (
        ("x-thinking-mode", _normalize_anthropic_level),
        ("x-reasoning-effort", _normalize_anthropic_level),
    )
    for name, parser in candidates:
        raw = headers.get(name)
        if raw is None:
            continue
        level = parser(raw)
        if level:
            return level, name
        _warn_invalid(name, raw)
    return None, None


def resolve_openai_policy(
    request_data: Mapping[str, Any], headers: Optional[Mapping[str, str]] = None
) -> ThinkingPolicy:
    """Resolve thinking policy for OpenAI route.

    Precedence:
    1. Explicit numeric budget from request body
    2. Effort value from request body
    3. Header fallback hints
    4. FAKE_REASONING_* defaults

    Args:
        request_data: OpenAI request payload as dictionary.
        headers: Raw request headers.

    Returns:
        Resolved thinking policy.
    """

    body_budget = _parse_body_budget_openai(request_data)
    if body_budget is not None:
        if body_budget < 0:
            _warn_invalid("body_budget", body_budget)
        elif body_budget == 0:
            return ThinkingPolicy(False, None, "off", "body_budget")
        else:
            return ThinkingPolicy(
                True, _clamp_budget(body_budget), "budget", "body_budget"
            )

    body_effort = _parse_body_effort_openai(request_data)
    if body_effort:
        if body_effort == "off":
            return ThinkingPolicy(False, None, "off", "body_effort")
        if body_effort == "minimal":
            return ThinkingPolicy(
                True, THINKING_OPENAI_MINIMAL_TOKENS, "low", "body_effort"
            )
        mapped = _openai_budget_for_level(body_effort)
        if mapped is not None:
            return ThinkingPolicy(True, mapped, body_effort, "body_effort")

    normalized_headers = _normalize_headers(headers)

    header_budget, budget_header = _parse_header_budget(normalized_headers)
    if header_budget is not None:
        if header_budget < 0:
            _warn_invalid(budget_header or "x-thinking-budget", header_budget)
        elif header_budget == 0:
            return ThinkingPolicy(False, None, "off", "header_budget")
        else:
            return ThinkingPolicy(
                True, _clamp_budget(header_budget), "budget", "header_budget"
            )

    header_level, level_header = _parse_header_level_openai(normalized_headers)
    if header_level:
        if header_level == "off":
            return ThinkingPolicy(False, None, "off", "header_effort")
        if header_level == "minimal":
            return ThinkingPolicy(
                True, THINKING_OPENAI_MINIMAL_TOKENS, "low", "header_effort"
            )
        mapped = _openai_budget_for_level(header_level)
        if mapped is not None:
            return ThinkingPolicy(True, mapped, header_level, "header_effort")
        _warn_invalid(level_header or "header_effort", header_level)

    return _default_policy()


def resolve_anthropic_policy(
    request_data: Mapping[str, Any], headers: Optional[Mapping[str, str]] = None
) -> ThinkingPolicy:
    """Resolve thinking policy for Anthropic route.

    Precedence:
    1. Explicit numeric budget from request body
    2. Effort/mode from request body
    3. Header fallback hints
    4. FAKE_REASONING_* defaults

    Args:
        request_data: Anthropic request payload as dictionary.
        headers: Raw request headers.

    Returns:
        Resolved thinking policy.
    """

    body_budget = _parse_body_budget_anthropic(request_data)
    if body_budget is not None:
        if body_budget < 0:
            _warn_invalid("thinking.budget_tokens", body_budget)
        elif body_budget == 0:
            return ThinkingPolicy(False, None, "off", "body_budget")
        else:
            return ThinkingPolicy(
                True, _clamp_budget(body_budget), "budget", "body_budget"
            )

    body_effort = _parse_body_effort_anthropic(request_data)
    if body_effort:
        if body_effort == "off":
            return ThinkingPolicy(False, None, "off", "body_effort")
        if body_effort == "max":
            return ThinkingPolicy(
                True, THINKING_ANTHROPIC_MAX_TOKENS, "max", "body_effort"
            )
        return ThinkingPolicy(
            True, THINKING_ANTHROPIC_HIGH_TOKENS, "high", "body_effort"
        )

    normalized_headers = _normalize_headers(headers)

    header_budget, budget_header = _parse_header_budget(normalized_headers)
    if header_budget is not None:
        if header_budget < 0:
            _warn_invalid(budget_header or "x-thinking-budget", header_budget)
        elif header_budget == 0:
            return ThinkingPolicy(False, None, "off", "header_budget")
        else:
            return ThinkingPolicy(
                True, _clamp_budget(header_budget), "budget", "header_budget"
            )

    header_level, _ = _parse_header_level_anthropic(normalized_headers)
    if header_level:
        if header_level == "off":
            return ThinkingPolicy(False, None, "off", "header_effort")
        if header_level == "max":
            return ThinkingPolicy(
                True, THINKING_ANTHROPIC_MAX_TOKENS, "max", "header_effort"
            )
        return ThinkingPolicy(
            True, THINKING_ANTHROPIC_HIGH_TOKENS, "high", "header_effort"
        )

    return _default_policy()
