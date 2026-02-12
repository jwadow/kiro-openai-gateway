# -*- coding: utf-8 -*-

"""Unit tests for request-driven thinking policy resolution.

All tests verify that the pipeline is purely numeric:
- String effort values are converted to token budgets in a single step.
- No intermediate string labels (normalized_level) exist.
- ThinkingPolicy only carries inject_thinking, thinking_max_tokens, source.
"""

from unittest.mock import patch

from kiro.converters_anthropic import anthropic_to_kiro
from kiro.converters_openai import build_kiro_payload as build_openai_payload
from kiro.models_anthropic import AnthropicMessagesRequest
from kiro.models_openai import ChatCompletionRequest, ChatMessage
from kiro.thinking_policy import resolve_anthropic_policy, resolve_openai_policy


# =========================================================================
# OpenAI route
# =========================================================================


class TestResolveOpenAIPolicy:
    """Tests for OpenAI route policy resolver."""

    # -- defaults ---------------------------------------------------------

    def test_uses_default_when_no_hints(self):
        """What it does: falls back to FAKE_REASONING defaults."""
        with patch("kiro.thinking_policy.FAKE_REASONING_ENABLED", True):
            with patch("kiro.thinking_policy.FAKE_REASONING_MAX_TOKENS", 4321):
                policy = resolve_openai_policy({"model": "claude-sonnet-4-5"})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 4321
        assert policy.source == "default"

    def test_default_disabled_when_fake_reasoning_off(self):
        """What it does: returns off when FAKE_REASONING_ENABLED is False."""
        with patch("kiro.thinking_policy.FAKE_REASONING_ENABLED", False):
            policy = resolve_openai_policy({"model": "claude-sonnet-4-5"})

        assert policy.inject_thinking is False
        assert policy.thinking_max_tokens is None
        assert policy.source == "default"

    # -- body budget (numeric) --------------------------------------------

    def test_body_budget_overrides_body_effort(self):
        """What it does: numeric body budget wins over body effort."""
        policy = resolve_openai_policy(
            {
                "reasoning_effort": "low",
                "reasoning": {"budget_tokens": 9000},
            }
        )

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 9000
        assert policy.source == "body_budget"

    def test_body_budget_zero_disables_thinking(self):
        """What it does: body budget=0 disables thinking."""
        policy = resolve_openai_policy({"reasoning": {"budget_tokens": 0}})

        assert policy.inject_thinking is False
        assert policy.thinking_max_tokens is None
        assert policy.source == "body_budget"

    def test_body_budget_clamped_to_max(self):
        """What it does: body budget is clamped to THINKING_MAX_TOKENS."""
        with patch("kiro.thinking_policy.THINKING_MAX_TOKENS", 5000):
            policy = resolve_openai_policy({"reasoning": {"budget_tokens": 999999}})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 5000

    def test_body_budget_clamped_to_min(self):
        """What it does: body budget is clamped to THINKING_MIN_TOKENS."""
        with patch("kiro.thinking_policy.THINKING_MIN_TOKENS", 256):
            policy = resolve_openai_policy({"reasoning": {"budget_tokens": 10}})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 256

    # -- body effort (string -> numeric) ----------------------------------

    def test_body_effort_low_returns_numeric_budget(self):
        """What it does: effort 'low' maps directly to OPENAI_LOW_TOKENS."""
        with patch("kiro.thinking_policy.THINKING_OPENAI_LOW_TOKENS", 600):
            policy = resolve_openai_policy({"reasoning_effort": "low"})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 600
        assert policy.source == "body_effort"

    def test_body_effort_medium_returns_numeric_budget(self):
        """What it does: effort 'medium' maps directly to OPENAI_MEDIUM_TOKENS."""
        with patch("kiro.thinking_policy.THINKING_OPENAI_MEDIUM_TOKENS", 1800):
            # Need to also patch the map since it reads at import time
            with patch.dict(
                "kiro.thinking_policy._OPENAI_EFFORT_MAP", {"medium": 1800}
            ):
                policy = resolve_openai_policy({"reasoning_effort": "medium"})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 1800
        assert policy.source == "body_effort"

    def test_body_effort_high_returns_numeric_budget(self):
        """What it does: effort 'high' maps directly to OPENAI_HIGH_TOKENS."""
        with patch.dict("kiro.thinking_policy._OPENAI_EFFORT_MAP", {"high": 3000}):
            policy = resolve_openai_policy({"reasoning_effort": "high"})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 3000
        assert policy.source == "body_effort"

    def test_body_effort_overrides_headers(self):
        """What it does: body effort has priority over header hints."""
        policy = resolve_openai_policy(
            {"reasoning_effort": "low"},
            headers={"x-reasoning-effort": "high", "x-thinking-budget": "9999"},
        )

        assert policy.inject_thinking is True
        assert policy.source == "body_effort"

    def test_body_effort_none_disables_thinking(self):
        """What it does: effort 'none' disables thinking."""
        policy = resolve_openai_policy({"reasoning_effort": "none"})

        assert policy.inject_thinking is False
        assert policy.thinking_max_tokens is None
        assert policy.source == "body_effort"

    def test_body_effort_off_disables_thinking(self):
        """What it does: effort 'off' disables thinking."""
        policy = resolve_openai_policy({"reasoning_effort": "off"})

        assert policy.inject_thinking is False
        assert policy.source == "body_effort"

    def test_body_effort_disabled_disables_thinking(self):
        """What it does: effort 'disabled' disables thinking."""
        policy = resolve_openai_policy({"reasoning_effort": "disabled"})

        assert policy.inject_thinking is False
        assert policy.source == "body_effort"

    def test_camel_case_reasoning_effort_is_supported(self):
        """What it does: supports AI SDK camelCase reasoningEffort field."""
        policy = resolve_openai_policy({"reasoningEffort": "none"})

        assert policy.inject_thinking is False
        assert policy.source == "body_effort"

    def test_nested_reasoning_effort_is_supported(self):
        """What it does: supports reasoning.effort nested field."""
        policy = resolve_openai_policy({"reasoning": {"effort": "low"}})

        assert policy.inject_thinking is True
        assert policy.source == "body_effort"

    def test_openai_supports_on_alias(self):
        """What it does: 'on' maps to high budget."""
        with patch.dict("kiro.thinking_policy._OPENAI_EFFORT_MAP", {"on": 3000}):
            policy = resolve_openai_policy({"reasoningEffort": "on"})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 3000

    def test_openai_supports_max(self):
        """What it does: 'max' maps to ANTHROPIC_MAX_TOKENS."""
        with patch("kiro.thinking_policy.THINKING_ANTHROPIC_MAX_TOKENS", 4444):
            with patch.dict("kiro.thinking_policy._OPENAI_EFFORT_MAP", {"max": 4444}):
                policy = resolve_openai_policy({"reasoningEffort": "max"})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 4444

    def test_openai_supports_xhigh(self):
        """What it does: 'xhigh' maps to OPENAI_XHIGH_TOKENS."""
        with patch.dict("kiro.thinking_policy._OPENAI_EFFORT_MAP", {"xhigh": 4000}):
            policy = resolve_openai_policy({"reasoning_effort": "xhigh"})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 4000

    def test_openai_supports_minimal(self):
        """What it does: 'minimal' maps to OPENAI_MINIMAL_TOKENS."""
        with patch.dict("kiro.thinking_policy._OPENAI_EFFORT_MAP", {"minimal": 600}):
            policy = resolve_openai_policy({"reasoning_effort": "minimal"})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 600

    # -- header budget ----------------------------------------------------

    def test_header_budget_zero_disables_thinking(self):
        """What it does: header budget=0 maps to off."""
        policy = resolve_openai_policy({}, headers={"x-thinking-budget": "0"})

        assert policy.inject_thinking is False
        assert policy.thinking_max_tokens is None
        assert policy.source == "header_budget"

    def test_header_budget_positive_enables_thinking(self):
        """What it does: header budget > 0 enables thinking with that budget."""
        policy = resolve_openai_policy({}, headers={"x-thinking-budget": "2500"})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 2500
        assert policy.source == "header_budget"

    # -- header effort ----------------------------------------------------

    def test_header_effort_is_used_when_body_absent(self):
        """What it does: falls back to x-reasoning-effort when no body hints."""
        with patch.dict("kiro.thinking_policy._OPENAI_EFFORT_MAP", {"high": 3000}):
            policy = resolve_openai_policy({}, headers={"x-reasoning-effort": "high"})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 3000
        assert policy.source == "header_effort"

    def test_header_effort_off_disables_thinking(self):
        """What it does: header effort 'off' disables thinking."""
        policy = resolve_openai_policy({}, headers={"x-reasoning-effort": "off"})

        assert policy.inject_thinking is False
        assert policy.source == "header_effort"

    # -- no normalized_level attribute ------------------------------------

    def test_no_normalized_level_attribute(self):
        """What it does: ThinkingPolicy has no normalized_level attribute."""
        policy = resolve_openai_policy({"reasoning_effort": "high"})
        assert not hasattr(policy, "normalized_level")


# =========================================================================
# Anthropic route
# =========================================================================


class TestResolveAnthropicPolicy:
    """Tests for Anthropic route policy resolver."""

    # -- thinking.type disabled -------------------------------------------

    def test_thinking_disabled_forces_off(self):
        """What it does: thinking.type=disabled disables injection."""
        policy = resolve_anthropic_policy({"thinking": {"type": "disabled"}})

        assert policy.inject_thinking is False
        assert policy.thinking_max_tokens is None
        assert policy.source == "body_effort"

    # -- thinking.budget_tokens (numeric) ---------------------------------

    def test_thinking_budget_uses_clamp(self):
        """What it does: explicit body budget is clamped by max."""
        with patch("kiro.thinking_policy.THINKING_MAX_TOKENS", 5000):
            policy = resolve_anthropic_policy(
                {"thinking": {"type": "enabled", "budget_tokens": 999999}}
            )

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 5000
        assert policy.source == "body_budget"

    def test_thinking_budget_zero_disables(self):
        """What it does: budget_tokens=0 disables thinking."""
        policy = resolve_anthropic_policy(
            {"thinking": {"type": "enabled", "budget_tokens": 0}}
        )

        assert policy.inject_thinking is False
        assert policy.thinking_max_tokens is None
        assert policy.source == "body_budget"

    def test_thinking_budget_camel_case(self):
        """What it does: supports camelCase budgetTokens."""
        policy = resolve_anthropic_policy(
            {"thinking": {"type": "enabled", "budgetTokens": 2000}}
        )

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 2000
        assert policy.source == "body_budget"

    def test_thinking_budget_overrides_effort(self):
        """What it does: numeric budget wins over effort string."""
        policy = resolve_anthropic_policy(
            {
                "thinking": {"type": "enabled", "budget_tokens": 5000},
                "output_config": {"effort": "low"},
            }
        )

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 5000
        assert policy.source == "body_budget"

    # -- thinking.type enabled (no budget) --------------------------------

    def test_thinking_enabled_without_budget_uses_high_default(self):
        """What it does: enabled without budget_tokens defaults to HIGH."""
        with patch.dict(
            "kiro.thinking_policy._ANTHROPIC_EFFORT_MAP",
            {"enabled": 3000},
        ):
            with patch("kiro.thinking_policy.THINKING_ANTHROPIC_HIGH_TOKENS", 3000):
                policy = resolve_anthropic_policy({"thinking": {"type": "enabled"}})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 3000
        assert policy.source == "body_effort"

    # -- output_config.effort (string -> numeric) -------------------------

    def test_output_effort_max_maps_to_max_budget(self):
        """What it does: output_config.effort=max uses anthropic max budget."""
        with patch("kiro.thinking_policy.THINKING_ANTHROPIC_MAX_TOKENS", 7777):
            with patch.dict(
                "kiro.thinking_policy._ANTHROPIC_EFFORT_MAP", {"max": 7777}
            ):
                policy = resolve_anthropic_policy({"output_config": {"effort": "max"}})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 7777
        assert policy.source == "body_effort"

    def test_output_effort_high_maps_to_high_budget(self):
        """What it does: output_config.effort=high uses anthropic high budget."""
        with patch.dict("kiro.thinking_policy._ANTHROPIC_EFFORT_MAP", {"high": 3000}):
            policy = resolve_anthropic_policy({"output_config": {"effort": "high"}})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 3000
        assert policy.source == "body_effort"

    def test_output_effort_medium_maps_to_medium_budget(self):
        """What it does: output_config.effort=medium uses anthropic medium budget."""
        with patch.dict("kiro.thinking_policy._ANTHROPIC_EFFORT_MAP", {"medium": 1800}):
            policy = resolve_anthropic_policy({"output_config": {"effort": "medium"}})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 1800
        assert policy.source == "body_effort"

    def test_output_effort_low_maps_to_low_budget(self):
        """What it does: output_config.effort=low uses anthropic low budget."""
        with patch.dict("kiro.thinking_policy._ANTHROPIC_EFFORT_MAP", {"low": 600}):
            policy = resolve_anthropic_policy({"output_config": {"effort": "low"}})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 600
        assert policy.source == "body_effort"

    def test_output_effort_off_disables_thinking(self):
        """What it does: output_config.effort=off disables thinking."""
        policy = resolve_anthropic_policy({"output_config": {"effort": "off"}})

        assert policy.inject_thinking is False
        assert policy.thinking_max_tokens is None
        assert policy.source == "body_effort"

    def test_output_config_camel_case(self):
        """What it does: supports camelCase outputConfig."""
        with patch.dict("kiro.thinking_policy._ANTHROPIC_EFFORT_MAP", {"high": 3000}):
            policy = resolve_anthropic_policy({"outputConfig": {"effort": "high"}})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 3000
        assert policy.source == "body_effort"

    # -- adaptive thinking ------------------------------------------------

    def test_adaptive_with_effort_medium(self):
        """What it does: adaptive thinking + effort=medium uses medium budget."""
        with patch.dict("kiro.thinking_policy._ANTHROPIC_EFFORT_MAP", {"medium": 1800}):
            policy = resolve_anthropic_policy(
                {
                    "thinking": {"type": "adaptive"},
                    "output_config": {"effort": "medium"},
                }
            )

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 1800
        assert policy.source == "body_effort"

    def test_adaptive_with_effort_low(self):
        """What it does: adaptive thinking + effort=low uses low budget."""
        with patch.dict("kiro.thinking_policy._ANTHROPIC_EFFORT_MAP", {"low": 600}):
            policy = resolve_anthropic_policy(
                {
                    "thinking": {"type": "adaptive"},
                    "output_config": {"effort": "low"},
                }
            )

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 600
        assert policy.source == "body_effort"

    def test_adaptive_with_effort_max(self):
        """What it does: adaptive thinking + effort=max uses max budget."""
        with patch.dict("kiro.thinking_policy._ANTHROPIC_EFFORT_MAP", {"max": 4000}):
            policy = resolve_anthropic_policy(
                {
                    "thinking": {"type": "adaptive"},
                    "output_config": {"effort": "max"},
                }
            )

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 4000
        assert policy.source == "body_effort"

    def test_adaptive_without_effort_defaults_to_high(self):
        """What it does: adaptive thinking without effort defaults to HIGH."""
        with patch("kiro.thinking_policy.THINKING_ANTHROPIC_HIGH_TOKENS", 3000):
            policy = resolve_anthropic_policy({"thinking": {"type": "adaptive"}})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 3000
        assert policy.source == "body_effort"

    def test_adaptive_with_effort_off(self):
        """What it does: adaptive thinking + effort=off disables thinking."""
        policy = resolve_anthropic_policy(
            {
                "thinking": {"type": "adaptive"},
                "output_config": {"effort": "off"},
            }
        )

        assert policy.inject_thinking is False
        assert policy.thinking_max_tokens is None
        assert policy.source == "body_effort"

    # -- header fallbacks -------------------------------------------------

    def test_header_budget_used_when_body_absent(self):
        """What it does: header budget is used when no body hints."""
        policy = resolve_anthropic_policy({}, headers={"x-thinking-budget": "2500"})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 2500
        assert policy.source == "header_budget"

    def test_header_effort_used_when_body_absent(self):
        """What it does: header effort is used when no body hints."""
        with patch.dict("kiro.thinking_policy._ANTHROPIC_EFFORT_MAP", {"high": 3000}):
            policy = resolve_anthropic_policy(
                {}, headers={"x-reasoning-effort": "high"}
            )

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 3000
        assert policy.source == "header_effort"

    def test_header_budget_zero_disables(self):
        """What it does: header budget=0 disables thinking."""
        policy = resolve_anthropic_policy({}, headers={"x-thinking-budget": "0"})

        assert policy.inject_thinking is False
        assert policy.thinking_max_tokens is None
        assert policy.source == "header_budget"

    # -- defaults ---------------------------------------------------------

    def test_uses_default_when_no_hints(self):
        """What it does: falls back to FAKE_REASONING defaults."""
        with patch("kiro.thinking_policy.FAKE_REASONING_ENABLED", True):
            with patch("kiro.thinking_policy.FAKE_REASONING_MAX_TOKENS", 4321):
                policy = resolve_anthropic_policy({})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 4321
        assert policy.source == "default"

    # -- no normalized_level attribute ------------------------------------

    def test_no_normalized_level_attribute(self):
        """What it does: ThinkingPolicy has no normalized_level attribute."""
        policy = resolve_anthropic_policy({"thinking": {"type": "enabled"}})
        assert not hasattr(policy, "normalized_level")


# =========================================================================
# Converter wiring
# =========================================================================


class TestConverterWiring:
    """Tests for converter integration with policy resolver."""

    def test_openai_converter_respects_off(self):
        """What it does: OpenAI reasoning_effort=none disables thinking tag injection."""
        request = ChatCompletionRequest.model_validate(
            {
                "model": "claude-sonnet-4-5",
                "messages": [{"role": "user", "content": "hello"}],
                "reasoning_effort": "none",
            }
        )

        payload = build_openai_payload(request, "conv-123", "")
        content = payload["conversationState"]["currentMessage"]["userInputMessage"][
            "content"
        ]

        assert not content.startswith("<thinking_mode>enabled</thinking_mode>")

    def test_openai_converter_uses_header_budget(self):
        """What it does: OpenAI converter uses header-only budget fallback."""
        request = ChatCompletionRequest(
            model="claude-sonnet-4-5",
            messages=[ChatMessage(role="user", content="hello")],
        )

        payload = build_openai_payload(
            request,
            "conv-123",
            "",
            headers={"x-thinking-budget": "3456"},
        )
        content = payload["conversationState"]["currentMessage"]["userInputMessage"][
            "content"
        ]

        assert "<max_thinking_length>3456</max_thinking_length>" in content

    def test_anthropic_converter_respects_disabled(self):
        """What it does: Anthropic thinking.type=disabled disables thinking tags."""
        request = AnthropicMessagesRequest.model_validate(
            {
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "hello"}],
                "thinking": {"type": "disabled"},
            }
        )

        payload = anthropic_to_kiro(request, "conv-123", "")
        content = payload["conversationState"]["currentMessage"]["userInputMessage"][
            "content"
        ]

        assert not content.startswith("<thinking_mode>enabled</thinking_mode>")

    def test_openai_converter_uses_body_effort(self):
        """What it does: OpenAI converter injects thinking tags from body effort."""
        request = ChatCompletionRequest.model_validate(
            {
                "model": "claude-sonnet-4-5",
                "messages": [{"role": "user", "content": "hello"}],
                "reasoning_effort": "high",
            }
        )

        payload = build_openai_payload(request, "conv-123", "")
        content = payload["conversationState"]["currentMessage"]["userInputMessage"][
            "content"
        ]

        assert "<thinking_mode>enabled</thinking_mode>" in content
        assert "<max_thinking_length>" in content

    def test_anthropic_converter_uses_numeric_budget(self):
        """What it does: Anthropic converter injects thinking tags from numeric budget."""
        request = AnthropicMessagesRequest.model_validate(
            {
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "hello"}],
                "thinking": {"type": "enabled", "budget_tokens": 5000},
            }
        )

        payload = anthropic_to_kiro(request, "conv-123", "")
        content = payload["conversationState"]["currentMessage"]["userInputMessage"][
            "content"
        ]

        assert "<thinking_mode>enabled</thinking_mode>" in content
        assert "<max_thinking_length>5000</max_thinking_length>" in content
