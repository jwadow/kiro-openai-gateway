# -*- coding: utf-8 -*-

"""Unit tests for request-driven thinking policy resolution."""

from unittest.mock import patch

from kiro.converters_anthropic import anthropic_to_kiro
from kiro.converters_openai import build_kiro_payload as build_openai_payload
from kiro.models_anthropic import AnthropicMessagesRequest
from kiro.models_openai import ChatCompletionRequest, ChatMessage
from kiro.thinking_policy import resolve_anthropic_policy, resolve_openai_policy


class TestResolveOpenAIPolicy:
    """Tests for OpenAI route policy resolver."""

    def test_uses_default_when_no_hints(self):
        """What it does: falls back to FAKE_REASONING defaults."""
        with patch("kiro.thinking_policy.FAKE_REASONING_ENABLED", True):
            with patch("kiro.thinking_policy.FAKE_REASONING_MAX_TOKENS", 4321):
                policy = resolve_openai_policy({"model": "claude-sonnet-4-5"})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 4321
        assert policy.source == "default"

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

    def test_body_effort_overrides_headers(self):
        """What it does: body effort has priority over header hints."""
        policy = resolve_openai_policy(
            {"reasoning_effort": "low"},
            headers={"x-reasoning-effort": "high", "x-thinking-budget": "9999"},
        )

        assert policy.inject_thinking is True
        assert policy.source == "body_effort"
        assert policy.normalized_level == "low"

    def test_camel_case_reasoning_effort_is_supported(self):
        """What it does: supports AI SDK camelCase reasoningEffort field."""
        policy = resolve_openai_policy({"reasoningEffort": "none"})

        assert policy.inject_thinking is False
        assert policy.source == "body_effort"

    def test_header_budget_zero_disables_thinking(self):
        """What it does: header budget=0 maps to off."""
        policy = resolve_openai_policy({}, headers={"x-thinking-budget": "0"})

        assert policy.inject_thinking is False
        assert policy.thinking_max_tokens is None
        assert policy.source == "header_budget"

    def test_header_effort_is_used_when_body_absent(self):
        """What it does: falls back to x-reasoning-effort when no body hints."""
        policy = resolve_openai_policy({}, headers={"x-reasoning-effort": "high"})

        assert policy.inject_thinking is True
        assert policy.normalized_level == "high"
        assert policy.source == "header_effort"

    def test_openai_supports_off_high_max_aliases(self):
        """What it does: OpenAI path accepts off/high/max aliases for interoperability."""
        with patch("kiro.thinking_policy.THINKING_ANTHROPIC_MAX_TOKENS", 4444):
            policy_off = resolve_openai_policy({"reasoningEffort": "off"})
            policy_high = resolve_openai_policy({"reasoningEffort": "on"})
            policy_max = resolve_openai_policy({"reasoningEffort": "max"})

        assert policy_off.inject_thinking is False
        assert policy_high.inject_thinking is True
        assert policy_high.normalized_level == "high"
        assert policy_max.inject_thinking is True
        assert policy_max.thinking_max_tokens == 4444


class TestResolveAnthropicPolicy:
    """Tests for Anthropic route policy resolver."""

    def test_thinking_disabled_forces_off(self):
        """What it does: thinking.type=disabled disables injection."""
        policy = resolve_anthropic_policy({"thinking": {"type": "disabled"}})

        assert policy.inject_thinking is False
        assert policy.thinking_max_tokens is None
        assert policy.normalized_level == "off"

    def test_thinking_budget_uses_clamp(self):
        """What it does: explicit body budget is clamped by max."""
        with patch("kiro.thinking_policy.THINKING_MAX_TOKENS", 5000):
            policy = resolve_anthropic_policy(
                {"thinking": {"type": "enabled", "budget_tokens": 999999}}
            )

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 5000
        assert policy.source == "body_budget"

    def test_output_effort_max_maps_to_max_level(self):
        """What it does: output_config.effort=max uses anthropic max budget."""
        with patch("kiro.thinking_policy.THINKING_ANTHROPIC_MAX_TOKENS", 7777):
            policy = resolve_anthropic_policy({"output_config": {"effort": "max"}})

        assert policy.inject_thinking is True
        assert policy.thinking_max_tokens == 7777
        assert policy.normalized_level == "max"
        assert policy.source == "body_effort"


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
