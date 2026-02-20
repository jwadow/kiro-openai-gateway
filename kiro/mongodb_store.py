# -*- coding: utf-8 -*-

"""
MongoDB data access helpers for API-key auth and credit billing.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

from loguru import logger

from kiro.config import (
    MONGODB_URI,
    MONGODB_DB_NAME,
    MONGODB_USERS_COLLECTION,
    MONGODB_CREDITS_COLLECTION,
    MONGODB_USER_API_KEY_FIELD,
    MONGODB_USER_ID_FIELD,
    MONGODB_USER_ACTIVE_FIELD,
    MONGODB_CREDITS_USER_ID_FIELD,
    MONGODB_CREDITS_BALANCE_FIELD,
)

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError as MongoPyError
except ImportError:  # pragma: no cover - exercised only when dependency missing
    MongoClient = None  # type: ignore[assignment]

    class MongoPyError(RuntimeError):
        """Fallback Mongo error type when pymongo is unavailable."""


_mongo_client: Optional[Any] = None


class MongoStoreUnavailableError(RuntimeError):
    """Raised when MongoDB operations fail due to connectivity or server issues."""


def _require_mongodb_dependency() -> None:
    """
    Ensure pymongo dependency is available before DB operations.

    Raises:
        RuntimeError: If pymongo is not installed.
    """
    if MongoClient is None:
        raise RuntimeError(
            "MongoDB mode requires 'pymongo'. Install dependencies from requirements.txt."
        )


def _get_client() -> Any:
    """
    Return a cached MongoDB client.

    Returns:
        Cached MongoDB client instance.

    Raises:
        RuntimeError: If MongoDB URI is missing or dependency is unavailable.
    """
    global _mongo_client
    _require_mongodb_dependency()

    if not MONGODB_URI:
        raise RuntimeError("MONGODB_URI is required when API_KEY_SOURCE=mongodb or billing is enabled.")

    if _mongo_client is None:
        client_factory = MongoClient
        if client_factory is None:
            raise RuntimeError("MongoDB mode requires 'pymongo'. Install dependencies from requirements.txt.")
        _mongo_client = client_factory(MONGODB_URI)

    return _mongo_client


def _get_collection(collection_name: str) -> Any:
    """
    Get MongoDB collection by name.

    Args:
        collection_name: Collection name.

    Returns:
        MongoDB collection object.
    """
    client = _get_client()
    db = client[MONGODB_DB_NAME]
    return db[collection_name]


def _to_decimal(value: Any) -> Decimal:
    """
    Convert numeric value from DB into Decimal.

    Args:
        value: Value from MongoDB document.

    Returns:
        Decimal representation.

    Raises:
        ValueError: If the value cannot be converted to Decimal.
    """
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric value in credits field: {value!r}") from exc


def find_active_user_by_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Find active user by API key.

    Args:
        api_key: Incoming API key.

    Returns:
        User document if found and active, else None.
    """
    try:
        users = _get_collection(MONGODB_USERS_COLLECTION)
        query = {
            MONGODB_USER_API_KEY_FIELD: api_key,
            MONGODB_USER_ACTIVE_FIELD: True,
        }
        return users.find_one(query)
    except MongoPyError as exc:
        logger.error(f"MongoDB user lookup failed: {exc}")
        raise MongoStoreUnavailableError("MongoDB user lookup failed") from exc


def get_user_id_from_doc(user_doc: Dict[str, Any]) -> Any:
    """
    Extract user identifier from user document.

    Args:
        user_doc: MongoDB user document.

    Returns:
        User identifier value.

    Raises:
        KeyError: If user ID field is missing.
    """
    if MONGODB_USER_ID_FIELD not in user_doc:
        raise KeyError(f"User document missing ID field '{MONGODB_USER_ID_FIELD}'")
    return user_doc[MONGODB_USER_ID_FIELD]


def get_credit_balance(user_id: Any) -> Optional[Decimal]:
    """
    Get current credit balance for a user.

    Args:
        user_id: User identifier.

    Returns:
        Credit balance as Decimal, or None if record is missing.
    """
    try:
        credits_collection = _get_collection(MONGODB_CREDITS_COLLECTION)
        query = {MONGODB_CREDITS_USER_ID_FIELD: user_id}
        projection = {MONGODB_CREDITS_BALANCE_FIELD: 1}
        doc = credits_collection.find_one(query, projection)
        if not doc or MONGODB_CREDITS_BALANCE_FIELD not in doc:
            return None
        return _to_decimal(doc[MONGODB_CREDITS_BALANCE_FIELD])
    except (MongoPyError, ValueError) as exc:
        logger.error(f"MongoDB credit balance lookup failed: {exc}")
        return None


def has_sufficient_credits(user_id: Any, required_credits: Decimal) -> bool:
    """
    Check whether user has enough credits.

    Args:
        user_id: User identifier.
        required_credits: Required credits.

    Returns:
        True if balance exists and is greater than or equal to required amount.
    """
    balance = get_credit_balance(user_id)
    if balance is None:
        return False
    return balance >= required_credits


def deduct_credits_atomic(user_id: Any, amount: Decimal) -> bool:
    """
    Atomically deduct credits from user balance.

    Args:
        user_id: User identifier.
        amount: Amount to deduct.

    Returns:
        True when one record is updated; False when balance is insufficient or record missing.
    """
    if amount <= Decimal("0"):
        return True

    try:
        credits_collection = _get_collection(MONGODB_CREDITS_COLLECTION)
        amount_float = float(amount)
        result = credits_collection.update_one(
            {
                MONGODB_CREDITS_USER_ID_FIELD: user_id,
                MONGODB_CREDITS_BALANCE_FIELD: {"$gte": amount_float},
            },
            {
                "$inc": {MONGODB_CREDITS_BALANCE_FIELD: -amount_float},
            },
        )
        return result.modified_count == 1
    except MongoPyError as exc:
        logger.error(f"MongoDB atomic credit deduction failed: {exc}")
        return False
