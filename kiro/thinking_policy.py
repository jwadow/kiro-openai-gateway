# -*- coding: utf-8 -*-

"""
Request-driven thinking policy resolver.

This module resolves per-request thinking behavior from:
1. Request body (highest priority)
2. Request headers (fallback)
3. Existing FAKE_REASONING_* defaults (last resort)

It is intentionally stateless and does not modify payload formats.

All effort strings (e.g. "low", "high", "max") are converted to numeric
token budgets in a single step.  No intermediate string labels are stored.
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
    THINKING_ANTHROPIC_LOW_TOKENS,
    THINKING_ANTHROPIC_MEDIUM_TOKENS,
    THINKING_ANTHROPIC_HIGH_TOKENS,
    THINKING_ANTHROPIC_MAX_TOKENS,
)


# ---------------------------------------------------------------------------
# Effort-to-budget maps (single-step string -> int conversion)
# ---------------------------------------------------------------------------

# OpenAI effort strings mapped to numeric token budgets.
# 0 means thinking is disabled.  Keys cover all known aliases.
_OPENAI_EFFORT_MAP: Dict[str, int] = {
    "none": 0,
    "off": 0,
    "disabled": 0,
    "minimal": THINKING_OPENAI_MINIMAL_TOKENS,
    "low": THINKING_OPENAI_LOW_TOKENS,
    "medium": THINKING_OPENAI_MEDIUM_TOKENS,
    "high": THINKING_OPENAI_HIGH_TOKENS,
    "on": THINKING_OPENAI_HIGH_TOKENS,
    "xhigh": THINKING_OPENAI_XHIGH_TOKENS,
    "max": THINKING_ANTHROPIC_MAX_TOKENS,
}

# Anthropic effort strings mapped to numeric token budgets.
# Covers the 4 official Anthropic effort levels (low/medium/high/max)
# plus common aliases.
_ANTHROPIC_EFFORT_MAP: Dict[str, int] = {
    "none": 0,
    "off": 0,
    "disabled": 0,
    "low": THINKING_ANTHROPIC_LOW_TOKENS,
    "minimal": THINKING_ANTHROPIC_LOW_TOKENS,
    "medium": THINKING_ANTHROPIC_MEDIUM_TOKENS,
    "high": THINKING_ANTHROPIC_HIGH_TOKENS,
    "on": THINKING_ANTHROPIC_HIGH_TOKENS,
    "enabled": THINKING_ANTHROPIC_HIGH_TOKENS,
    "xhigh": THINKING_ANTHROPIC_MAX_TOKENS,
    "max": THINKING_ANTHROPIC_MAX_TOKENS,
}


@dataclass(frozen=True)
class ThinkingPolicy:
    """Resolved thinking policy for a single request.

    Attributes:
        inject_thinking: Whether thinking tags should be injected.
        thinking_max_tokens: Token budget for thinking (None when disabled).
        source: Source of policy decision (for diagnostics/logging).
    """

    inject_thinking: bool
    thinking_max_tokens: Optional[int]
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
    """Return policy from existing FAKE_REASONING defaults.

    Returns:
        ThinkingPolicy based on FAKE_REASONING_ENABLED / FAKE_REASONING_MAX_TOKENS.
    """

    if not FAKE_REASONING_ENABLED:
        return ThinkingPolicy(False, None, "default")
    return ThinkingPolicy(True, FAKE_REASONING_MAX_TOKENS, "default")


def _warn_invalid(field_name: str, value: Any) -> None:
    """Log warning for invalid policy hints.

    Args:
        field_name: Hint field name.
        value: Invalid value.
    """

    logger.warning(f"Ignoring invalid thinking hint: {field_name}={value!r}")


# ---------------------------------------------------------------------------
# Single-step effort string -> numeric budget converters
# ---------------------------------------------------------------------------


def _effort_to_budget_openai(value: Any) -> Optional[int]:
    """Convert an OpenAI effort string directly to a numeric token budget.

    Args:
        value: Raw effort string (e.g. "low", "high", "max").

    Returns:
        Token budget (0 = off), or None if the value is unrecognised.
    """

    if not isinstance(value, str):
        return None
    raw = value.strip().lower()
    return _OPENAI_EFFORT_MAP.get(raw)


def _effort_to_budget_anthropic(value: Any) -> Optional[int]:
    """Convert an Anthropic effort string directly to a numeric token budget.

    Args:
        value: Raw effort string (e.g. "low", "medium", "high", "max").

    Returns:
        Token budget (0 = off), or None if the value is unrecognised.
    """

    if not isinstance(value, str):
        return None
    raw = value.strip().lower()
    return _ANTHROPIC_EFFORT_MAP.get(raw)


# ---------------------------------------------------------------------------
# Body budget parsers (numeric)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Body effort parsers (string -> numeric budget in one step)
# ---------------------------------------------------------------------------


def _parse_body_effort_openai(request_data: Mapping[str, Any]) -> Optional[int]:
    """Extract effort from OpenAI-compatible request body as numeric budget.

    Checks top-level reasoning_effort / reasoningEffort and nested
    reasoning.effort / reasoning.reasoningEffort fields.

    Args:
        request_data: Request payload dictionary.

    Returns:
        Numeric token budget (0 = off), or None if no effort hint found.
    """

    top_level = _effort_to_budget_openai(
        request_data.get("reasoning_effort") or request_data.get("reasoningEffort")
    )
    if top_level is not None:
        return top_level

    reasoning = request_data.get("reasoning")
    if isinstance(reasoning, Mapping):
        nested = _effort_to_budget_openai(reasoning.get("effort"))
        if nested is not None:
            return nested
        nested = _effort_to_budget_openai(reasoning.get("reasoningEffort"))
        if nested is not None:
            return nested

    return None


def _parse_body_effort_anthropic(request_data: Mapping[str, Any]) -> Optional[int]:
    """Extract effort from Anthropic-compatible request body as numeric budget.

    Handles:
    - thinking.type: "disabled" -> 0 (off)
    - thinking.type: "enabled" / "on" -> ANTHROPIC_HIGH_TOKENS (default)
    - thinking.type: "adaptive" -> reads output_config.effort, defaults to HIGH
    - output_config.effort / outputConfig.effort -> effort string to budget

    Args:
        request_data: Request payload dictionary.

    Returns:
        Numeric token budget (0 = off), or None if no effort hint found.
    """

    thinking = request_data.get("thinking")
    if isinstance(thinking, Mapping):
        thinking_type = thinking.get("type")
        if isinstance(thinking_type, str):
            normalized_type = thinking_type.strip().lower()
            if normalized_type == "disabled":
                return 0

            if normalized_type == "adaptive":
                # Adaptive thinking: read effort from output_config, default high
                output_config = request_data.get("output_config")
                if output_config is None:
                    output_config = request_data.get("outputConfig")
                if isinstance(output_config, Mapping):
                    effort_budget = _effort_to_budget_anthropic(
                        output_config.get("effort")
                    )
                    if effort_budget is not None:
                        return effort_budget
                # Adaptive with no effort specified -> default high
                return THINKING_ANTHROPIC_HIGH_TOKENS

            if normalized_type in ("enabled", "on"):
                # Enabled without budget_tokens -> default high
                # (If budget_tokens was present, _parse_body_budget_anthropic
                #  would have already returned before this function is called)
                return THINKING_ANTHROPIC_HIGH_TOKENS

    # Standalone output_config.effort (without thinking block)
    output_config = request_data.get("output_config")
    if output_config is None:
        output_config = request_data.get("outputConfig")
    if isinstance(output_config, Mapping):
        effort_budget = _effort_to_budget_anthropic(output_config.get("effort"))
        if effort_budget is not None:
            return effort_budget

    return None


# ---------------------------------------------------------------------------
# Header parsers
# ---------------------------------------------------------------------------


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


def _parse_header_effort_openai(
    headers: Mapping[str, str],
) -> Tuple[Optional[int], Optional[str]]:
    """Extract OpenAI-style effort from fallback headers as numeric budget.

    Args:
        headers: Normalized lowercase headers.

    Returns:
        Tuple of (budget, source_header). Budget is 0 for off, None if absent.
    """

    candidates = (
        ("x-reasoning-effort", _effort_to_budget_openai),
        ("x-thinking-mode", _effort_to_budget_openai),
    )
    for name, converter in candidates:
        raw = headers.get(name)
        if raw is None:
            continue
        budget = converter(raw)
        if budget is not None:
            return budget, name
        _warn_invalid(name, raw)
    return None, None


def _parse_header_effort_anthropic(
    headers: Mapping[str, str],
) -> Tuple[Optional[int], Optional[str]]:
    """Extract Anthropic-style effort from fallback headers as numeric budget.

    Args:
        headers: Normalized lowercase headers.

    Returns:
        Tuple of (budget, source_header). Budget is 0 for off, None if absent.
    """

    candidates = (
        ("x-thinking-mode", _effort_to_budget_anthropic),
        ("x-reasoning-effort", _effort_to_budget_anthropic),
    )
    for name, converter in candidates:
        raw = headers.get(name)
        if raw is None:
            continue
        budget = converter(raw)
        if budget is not None:
            return budget, name
        _warn_invalid(name, raw)
    return None, None


# ---------------------------------------------------------------------------
# Helper to build ThinkingPolicy from a resolved numeric budget
# ---------------------------------------------------------------------------


def _policy_from_budget(budget: int, source: str) -> ThinkingPolicy:
    """Build a ThinkingPolicy from a resolved numeric budget.

    Args:
        budget: Token budget. 0 means off, >0 means enabled.
        source: Diagnostic source label.

    Returns:
        Resolved ThinkingPolicy.
    """

    if budget <= 0:
        return ThinkingPolicy(False, None, source)
    return ThinkingPolicy(True, _clamp_budget(budget), source)


# ---------------------------------------------------------------------------
# Public resolvers
# ---------------------------------------------------------------------------


def resolve_openai_policy(
    request_data: Mapping[str, Any], headers: Optional[Mapping[str, str]] = None
) -> ThinkingPolicy:
    """Resolve thinking policy for OpenAI route.

    Precedence:
    1. Explicit numeric budget from request body
    2. Effort value from request body (converted to numeric budget)
    3. Header fallback hints
    4. FAKE_REASONING_* defaults

    Args:
        request_data: OpenAI request payload as dictionary.
        headers: Raw request headers.

    Returns:
        Resolved thinking policy.
    """

    # 1. Body numeric budget (highest priority)
    body_budget = _parse_body_budget_openai(request_data)
    if body_budget is not None:
        if body_budget < 0:
            _warn_invalid("body_budget", body_budget)
        else:
            return _policy_from_budget(body_budget, "body_budget")

    # 2. Body effort string -> numeric budget
    body_effort_budget = _parse_body_effort_openai(request_data)
    if body_effort_budget is not None:
        return _policy_from_budget(body_effort_budget, "body_effort")

    # 3. Header fallbacks
    normalized_headers = _normalize_headers(headers)

    header_budget, budget_header = _parse_header_budget(normalized_headers)
    if header_budget is not None:
        if header_budget < 0:
            _warn_invalid(budget_header or "x-thinking-budget", header_budget)
        else:
            return _policy_from_budget(header_budget, "header_budget")

    header_effort_budget, _ = _parse_header_effort_openai(normalized_headers)
    if header_effort_budget is not None:
        return _policy_from_budget(header_effort_budget, "header_effort")

    # 4. Default
    return _default_policy()


def resolve_anthropic_policy(
    request_data: Mapping[str, Any], headers: Optional[Mapping[str, str]] = None
) -> ThinkingPolicy:
    """Resolve thinking policy for Anthropic route.

    Precedence:
    1. Explicit numeric budget from request body
    2. Effort/mode from request body (converted to numeric budget)
    3. Header fallback hints
    4. FAKE_REASONING_* defaults

    Args:
        request_data: Anthropic request payload as dictionary.
        headers: Raw request headers.

    Returns:
        Resolved thinking policy.
    """

    # 1. Body numeric budget (highest priority)
    body_budget = _parse_body_budget_anthropic(request_data)
    if body_budget is not None:
        if body_budget < 0:
            _warn_invalid("thinking.budget_tokens", body_budget)
        else:
            return _policy_from_budget(body_budget, "body_budget")

    # 2. Body effort/mode -> numeric budget
    body_effort_budget = _parse_body_effort_anthropic(request_data)
    if body_effort_budget is not None:
        return _policy_from_budget(body_effort_budget, "body_effort")

    # 3. Header fallbacks
    normalized_headers = _normalize_headers(headers)

    header_budget, budget_header = _parse_header_budget(normalized_headers)
    if header_budget is not None:
        if header_budget < 0:
            _warn_invalid(budget_header or "x-thinking-budget", header_budget)
        else:
            return _policy_from_budget(header_budget, "header_budget")

    header_effort_budget, _ = _parse_header_effort_anthropic(normalized_headers)
    if header_effort_budget is not None:
        return _policy_from_budget(header_effort_budget, "header_effort")

    # 4. Default
    return _default_policy()
