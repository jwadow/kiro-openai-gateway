# -*- coding: utf-8 -*-

"""
Billing and credit deduction utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional

from loguru import logger

from kiro.config import (
    BILLING_ENABLED,
    BILLING_ENFORCE_SUFFICIENT_CREDITS,
    BILLING_DECIMAL_PLACES,
    BILLING_UNKNOWN_MODEL_POLICY,
    BILLING_DEFAULT_INPUT_PRICE_PER_MTOK,
    BILLING_DEFAULT_OUTPUT_PRICE_PER_MTOK,
    BILLING_DEFAULT_CACHE_WRITE_PRICE_PER_MTOK,
    BILLING_DEFAULT_CACHE_HIT_PRICE_PER_MTOK,
    BILLING_DEFAULT_MULTIPLIER,
    get_billing_model_prices,
)
from kiro.model_resolver import normalize_model_name
from kiro.mongodb_store import has_sufficient_credits, deduct_credits_atomic


class BillingError(Exception):
    """Base billing error."""


class UnknownModelPricingError(BillingError):
    """Raised when model pricing is missing and policy is reject."""


class InsufficientCreditsError(BillingError):
    """Raised when user has insufficient credits."""


@dataclass(frozen=True)
class ModelPricing:
    """
    Pricing config for one model.

    Attributes:
        model_id: Canonical model identifier.
        input_price_per_mtok: Input token price per 1,000,000 tokens.
        output_price_per_mtok: Output token price per 1,000,000 tokens.
        cache_write_price_per_mtok: Cache write token price per 1,000,000 tokens.
        cache_hit_price_per_mtok: Cache hit token price per 1,000,000 tokens.
        billing_multiplier: Final multiplier applied to total cost.
    """

    model_id: str
    input_price_per_mtok: Decimal
    output_price_per_mtok: Decimal
    cache_write_price_per_mtok: Decimal
    cache_hit_price_per_mtok: Decimal
    billing_multiplier: Decimal


_cached_pricing_index: Optional[Dict[str, ModelPricing]] = None


def reset_model_pricing_cache() -> None:
    """
    Reset in-memory pricing cache.

    Useful for unit tests that monkeypatch billing config.
    """
    global _cached_pricing_index
    _cached_pricing_index = None


def _quantize_decimal(value: Decimal) -> Decimal:
    """
    Quantize decimal value according to billing precision.

    Args:
        value: Decimal amount.

    Returns:
        Quantized decimal amount.
    """
    decimal_places = max(BILLING_DECIMAL_PLACES, 0)
    quantizer = Decimal("1") if decimal_places == 0 else Decimal(f"1e-{decimal_places}")
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)


def _safe_decimal(value: Any, fallback: Decimal = Decimal("0")) -> Decimal:
    """
    Convert value to Decimal using string conversion.

    Args:
        value: Numeric-like value.
        fallback: Fallback value when conversion fails.

    Returns:
        Decimal representation or fallback.
    """
    try:
        return Decimal(str(value))
    except (ArithmeticError, TypeError, ValueError):
        return fallback


def _normalize_pricing_key(model_id: str) -> str:
    """
    Normalize model ID for pricing lookup.

    Args:
        model_id: Raw model ID.

    Returns:
        Normalized, lowercased model key.
    """
    normalized = normalize_model_name(model_id)
    return normalized.lower() if normalized else model_id.lower()


def _build_pricing_index() -> Dict[str, ModelPricing]:
    """
    Build model pricing index from environment configuration.

    Returns:
        Mapping of model keys to pricing objects.
    """
    index: Dict[str, ModelPricing] = {}
    for raw_item in get_billing_model_prices():
        model_id = str(raw_item.get("id", "")).strip()
        if not model_id:
            continue

        pricing = ModelPricing(
            model_id=model_id,
            input_price_per_mtok=_safe_decimal(raw_item.get("input_price_per_mtok"), Decimal("0")),
            output_price_per_mtok=_safe_decimal(raw_item.get("output_price_per_mtok"), Decimal("0")),
            cache_write_price_per_mtok=_safe_decimal(raw_item.get("cache_write_price_per_mtok"), Decimal("0")),
            cache_hit_price_per_mtok=_safe_decimal(raw_item.get("cache_hit_price_per_mtok"), Decimal("0")),
            billing_multiplier=_safe_decimal(raw_item.get("billing_multiplier"), Decimal("1")),
        )

        raw_key = model_id.lower()
        normalized_key = _normalize_pricing_key(model_id)
        index[raw_key] = pricing
        index[normalized_key] = pricing

    return index


def _get_pricing_index() -> Dict[str, ModelPricing]:
    """
    Return cached model pricing index.

    Returns:
        Pricing index dictionary.
    """
    global _cached_pricing_index
    if _cached_pricing_index is None:
        _cached_pricing_index = _build_pricing_index()
    return _cached_pricing_index


def _default_pricing(model_id: str) -> ModelPricing:
    """
    Build default pricing from BILLING_DEFAULT_* config.

    Args:
        model_id: Model identifier for metadata.

    Returns:
        Default model pricing configuration.
    """
    return ModelPricing(
        model_id=model_id,
        input_price_per_mtok=Decimal(str(BILLING_DEFAULT_INPUT_PRICE_PER_MTOK)),
        output_price_per_mtok=Decimal(str(BILLING_DEFAULT_OUTPUT_PRICE_PER_MTOK)),
        cache_write_price_per_mtok=Decimal(str(BILLING_DEFAULT_CACHE_WRITE_PRICE_PER_MTOK)),
        cache_hit_price_per_mtok=Decimal(str(BILLING_DEFAULT_CACHE_HIT_PRICE_PER_MTOK)),
        billing_multiplier=Decimal(str(BILLING_DEFAULT_MULTIPLIER)),
    )


def _resolve_model_pricing(model_id: str) -> ModelPricing:
    """
    Resolve pricing config for model ID with fallback policy.

    Args:
        model_id: Requested model ID.

    Returns:
        Resolved pricing object.

    Raises:
        UnknownModelPricingError: If policy is reject and model is not configured.
    """
    pricing_index = _get_pricing_index()
    raw_key = model_id.lower()
    normalized_key = _normalize_pricing_key(model_id)

    pricing = pricing_index.get(raw_key) or pricing_index.get(normalized_key)
    if pricing:
        return pricing

    if BILLING_UNKNOWN_MODEL_POLICY == "free":
        return ModelPricing(
            model_id=model_id,
            input_price_per_mtok=Decimal("0"),
            output_price_per_mtok=Decimal("0"),
            cache_write_price_per_mtok=Decimal("0"),
            cache_hit_price_per_mtok=Decimal("0"),
            billing_multiplier=Decimal("1"),
        )

    if BILLING_UNKNOWN_MODEL_POLICY == "reject":
        raise UnknownModelPricingError(
            f"Model '{model_id}' not found in BILLING_MODEL_PRICES_JSON and policy=reject."
        )

    return _default_pricing(model_id)


def _extract_usage_tokens(usage: Dict[str, Any]) -> Dict[str, Decimal]:
    """
    Extract supported token counters from usage payload.

    Args:
        usage: Usage dictionary from OpenAI/Anthropic response.

    Returns:
        Dictionary with Decimal token counters.
    """
    prompt_tokens = _safe_decimal(usage.get("prompt_tokens", usage.get("input_tokens", 0)))
    completion_tokens = _safe_decimal(usage.get("completion_tokens", usage.get("output_tokens", 0)))
    cache_write_tokens = _safe_decimal(
        usage.get("cache_write_tokens", usage.get("cache_creation_input_tokens", 0))
    )
    cache_hit_tokens = _safe_decimal(
        usage.get("cache_hit_tokens", usage.get("cache_read_input_tokens", 0))
    )

    return {
        "prompt_tokens": max(prompt_tokens, Decimal("0")),
        "completion_tokens": max(completion_tokens, Decimal("0")),
        "cache_write_tokens": max(cache_write_tokens, Decimal("0")),
        "cache_hit_tokens": max(cache_hit_tokens, Decimal("0")),
    }


def calculate_charge_from_usage(model_id: str, usage: Dict[str, Any]) -> Decimal:
    """
    Calculate billed credits from usage and model pricing.

    Formula:
        total = (
            prompt_tokens * input_price_per_mtok
            + completion_tokens * output_price_per_mtok
            + cache_write_tokens * cache_write_price_per_mtok
            + cache_hit_tokens * cache_hit_price_per_mtok
        ) / 1_000_000
        charged = total * billing_multiplier

    Args:
        model_id: Requested model ID.
        usage: Usage dictionary.

    Returns:
        Charge amount quantized to BILLING_DECIMAL_PLACES.

    Raises:
        UnknownModelPricingError: If model is unknown and policy=reject.
    """
    if not BILLING_ENABLED:
        return Decimal("0")

    pricing = _resolve_model_pricing(model_id)
    tokens = _extract_usage_tokens(usage)
    per_million = Decimal("1000000")

    subtotal = (
        tokens["prompt_tokens"] * pricing.input_price_per_mtok
        + tokens["completion_tokens"] * pricing.output_price_per_mtok
        + tokens["cache_write_tokens"] * pricing.cache_write_price_per_mtok
        + tokens["cache_hit_tokens"] * pricing.cache_hit_price_per_mtok
    ) / per_million

    charged = subtotal * pricing.billing_multiplier
    return _quantize_decimal(max(charged, Decimal("0")))


def calculate_preflight_charge(model_id: str, prompt_tokens: int, tool_tokens: int = 0) -> Decimal:
    """
    Calculate preflight estimate using known request-side token counts.

    Args:
        model_id: Requested model ID.
        prompt_tokens: Counted message tokens.
        tool_tokens: Counted tool schema tokens.

    Returns:
        Estimated charge amount.
    """
    usage = {
        "prompt_tokens": max(prompt_tokens + tool_tokens, 0),
        "completion_tokens": 0,
        "cache_write_tokens": 0,
        "cache_hit_tokens": 0,
    }
    return calculate_charge_from_usage(model_id, usage)


def ensure_user_has_sufficient_credits(user_id: Any, required_credits: Decimal) -> None:
    """
    Enforce sufficient credits for a user before request execution.

    Args:
        user_id: User identifier.
        required_credits: Required credits for preflight check.

    Raises:
        InsufficientCreditsError: If billing enforcement is enabled and balance is insufficient.
    """
    if not BILLING_ENABLED or not BILLING_ENFORCE_SUFFICIENT_CREDITS:
        return

    if required_credits <= Decimal("0"):
        return

    if not has_sufficient_credits(user_id, required_credits):
        raise InsufficientCreditsError(
            f"Insufficient credits: requires at least {required_credits} credits."
        )


def deduct_credits_for_usage(user_id: Any, model_id: str, usage: Dict[str, Any]) -> Decimal:
    """
    Calculate and atomically deduct credits from user balance.

    Args:
        user_id: User identifier.
        model_id: Requested model ID.
        usage: Final usage payload.

    Returns:
        Deducted charge amount.

    Raises:
        InsufficientCreditsError: If atomic deduction fails due to insufficient credits.
        UnknownModelPricingError: If model pricing cannot be resolved and policy=reject.
    """
    charge = calculate_charge_from_usage(model_id, usage)
    if charge <= Decimal("0"):
        return Decimal("0")

    deduction_ok = deduct_credits_atomic(user_id, charge)
    if not deduction_ok:
        raise InsufficientCreditsError(
            f"Credit deduction failed for user due to insufficient balance: {charge}."
        )

    logger.info(f"Deducted {charge} credits for user request (model={model_id})")
    return charge
