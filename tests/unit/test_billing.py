# -*- coding: utf-8 -*-

"""
Unit tests for billing calculation and credit enforcement.
"""

from decimal import Decimal
import json

import pytest

import kiro.billing as billing


def _set_common_billing_config(monkeypatch: pytest.MonkeyPatch, prices_json: str) -> None:
    """Set common billing module config for deterministic tests."""
    monkeypatch.setattr(billing, "BILLING_ENABLED", True)
    monkeypatch.setattr(billing, "BILLING_DECIMAL_PLACES", 6)
    parsed_prices = json.loads(prices_json)
    monkeypatch.setattr(billing, "get_billing_model_prices", lambda: parsed_prices)
    monkeypatch.setattr(billing, "BILLING_DEFAULT_INPUT_PRICE_PER_MTOK", 3.0)
    monkeypatch.setattr(billing, "BILLING_DEFAULT_OUTPUT_PRICE_PER_MTOK", 14.0)
    monkeypatch.setattr(billing, "BILLING_DEFAULT_CACHE_WRITE_PRICE_PER_MTOK", 3.75)
    monkeypatch.setattr(billing, "BILLING_DEFAULT_CACHE_HIT_PRICE_PER_MTOK", 0.3)
    monkeypatch.setattr(billing, "BILLING_DEFAULT_MULTIPLIER", 1.1)
    billing.reset_model_pricing_cache()


class TestCalculateChargeFromUsage:
    """Tests for model pricing and charge calculation."""

    def test_known_model_returns_expected_charge(self, monkeypatch: pytest.MonkeyPatch):
        """
        What it does: Calculates charge for configured model with prompt/completion tokens.
        Purpose: Ensure pricing math matches expected formula.
        """
        _set_common_billing_config(
            monkeypatch,
            """[
                {
                    "id": "claude-sonnet-4-5-20250929",
                    "input_price_per_mtok": 3.0,
                    "output_price_per_mtok": 14.0,
                    "cache_write_price_per_mtok": 3.75,
                    "cache_hit_price_per_mtok": 0.3,
                    "billing_multiplier": 1.1
                }
            ]""",
        )
        monkeypatch.setattr(billing, "BILLING_UNKNOWN_MODEL_POLICY", "reject")

        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        result = billing.calculate_charge_from_usage("claude-sonnet-4-5-20250929", usage)

        # subtotal = ((1000*3)+(500*14))/1_000_000 = 0.01
        # charged = 0.01 * 1.1 = 0.011
        assert result == Decimal("0.011000")

    def test_unknown_model_reject_policy_raises(self, monkeypatch: pytest.MonkeyPatch):
        """
        What it does: Calculates charge for unknown model under reject policy.
        Purpose: Ensure unknown model is blocked when configured.
        """
        _set_common_billing_config(monkeypatch, "[]")
        monkeypatch.setattr(billing, "BILLING_UNKNOWN_MODEL_POLICY", "reject")

        with pytest.raises(billing.UnknownModelPricingError):
            billing.calculate_charge_from_usage("unknown-model", {"prompt_tokens": 10})

    def test_unknown_model_free_policy_returns_zero(self, monkeypatch: pytest.MonkeyPatch):
        """
        What it does: Calculates charge for unknown model under free policy.
        Purpose: Ensure unknown models can be allowed with no deduction.
        """
        _set_common_billing_config(monkeypatch, "[]")
        monkeypatch.setattr(billing, "BILLING_UNKNOWN_MODEL_POLICY", "free")

        result = billing.calculate_charge_from_usage("unknown-model", {"prompt_tokens": 10})
        assert result == Decimal("0.000000")


class TestCreditEnforcement:
    """Tests for sufficient-credit checks and atomic deduction."""

    def test_ensure_user_has_sufficient_credits_raises(self, monkeypatch: pytest.MonkeyPatch):
        """
        What it does: Runs preflight credit check when balance is insufficient.
        Purpose: Ensure requests are blocked before upstream call.
        """
        monkeypatch.setattr(billing, "BILLING_ENABLED", True)
        monkeypatch.setattr(billing, "BILLING_ENFORCE_SUFFICIENT_CREDITS", True)
        monkeypatch.setattr(billing, "has_sufficient_credits", lambda *_: False)

        with pytest.raises(billing.InsufficientCreditsError):
            billing.ensure_user_has_sufficient_credits("u-1", Decimal("0.01"))

    def test_deduct_credits_for_usage_returns_charge(self, monkeypatch: pytest.MonkeyPatch):
        """
        What it does: Deducts credits for known usage and returns charged amount.
        Purpose: Ensure deduction path computes and applies charge.
        """
        _set_common_billing_config(
            monkeypatch,
            """[
                {
                    "id": "claude-haiku-4-5-20251001",
                    "input_price_per_mtok": 1.0,
                    "output_price_per_mtok": 5.0,
                    "cache_write_price_per_mtok": 1.25,
                    "cache_hit_price_per_mtok": 0.1,
                    "billing_multiplier": 1.1
                }
            ]""",
        )
        monkeypatch.setattr(billing, "BILLING_UNKNOWN_MODEL_POLICY", "reject")
        monkeypatch.setattr(billing, "deduct_credits_atomic", lambda *_: True)

        charged = billing.deduct_credits_for_usage(
            user_id="u-1",
            model_id="claude-haiku-4-5-20251001",
            usage={"prompt_tokens": 1000, "completion_tokens": 0},
        )

        assert charged == Decimal("0.001100")
