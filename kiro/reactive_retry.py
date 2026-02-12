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
Reactive retry helpers for upstream 400 "Improperly formed request" responses.

Both OpenAI and Anthropic routes use the same retry strategy:
1. Detect specific malformed-request response pattern.
2. Rebuild payload (middleware pipeline runs again inside converter).
3. Retry with a fresh HTTP client.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict

import httpx
from fastapi import HTTPException
from loguru import logger

from kiro.config import REACTIVE_RETRY_ENABLED, REACTIVE_RETRY_MAX_ATTEMPTS
from kiro.http_client import KiroHttpClient


@dataclass
class ReactiveRetryResult:
    """Result of reactive retry processing.

    Attributes:
        response: Last upstream response (possibly successful retry response).
        http_client: Active HTTP client to continue with (open on success).
        error_text: Last known upstream error text.
        attempted: Whether reactive retry logic was executed.
    """

    response: httpx.Response
    http_client: KiroHttpClient
    error_text: str
    attempted: bool


def should_retry_improperly_formed(status_code: int, error_text: str) -> bool:
    """Check whether response matches reactive-retry conditions.

    Args:
        status_code: Upstream HTTP status code.
        error_text: Upstream response text.

    Returns:
        True when the response is 400 and includes "improperly formed" marker.
    """

    if status_code != 400:
        return False
    return "improperly formed" in error_text.lower()


async def read_response_error_text(response: httpx.Response) -> str:
    """Read upstream response body as text for error handling.

    Args:
        response: Upstream HTTP response.

    Returns:
        Decoded text body or fallback string on read failure.
    """

    try:
        error_content = await response.aread()
    except (httpx.HTTPError, RuntimeError, ValueError):
        error_content = b"Unknown error"
    return error_content.decode("utf-8", errors="replace")


async def retry_on_improperly_formed_request(
    *,
    response: httpx.Response,
    error_text: str,
    http_client: KiroHttpClient,
    request_url: str,
    rebuild_payload: Callable[[], Dict[str, Any]],
    new_http_client_factory: Callable[[], KiroHttpClient],
) -> ReactiveRetryResult:
    """Retry malformed upstream requests with rebuilt payload.

    Args:
        response: Initial upstream response.
        error_text: Initial upstream error text.
        http_client: Current HTTP client instance used for initial request.
        request_url: Upstream URL.
        rebuild_payload: Callback to rebuild payload for retry attempt.
        new_http_client_factory: Factory for fresh HTTP client per retry attempt.

    Returns:
        ReactiveRetryResult with last response and active client.
    """

    if not REACTIVE_RETRY_ENABLED:
        return ReactiveRetryResult(
            response=response,
            http_client=http_client,
            error_text=error_text,
            attempted=False,
        )

    if REACTIVE_RETRY_MAX_ATTEMPTS <= 0:
        return ReactiveRetryResult(
            response=response,
            http_client=http_client,
            error_text=error_text,
            attempted=False,
        )

    if not should_retry_improperly_formed(response.status_code, error_text):
        return ReactiveRetryResult(
            response=response,
            http_client=http_client,
            error_text=error_text,
            attempted=False,
        )

    await http_client.close()
    logger.warning(
        "[ReactiveRetry] Detected 'Improperly formed request' (400). "
        "Attempting sanitized retry..."
    )

    last_response = response
    last_error_text = error_text

    for retry_attempt in range(1, REACTIVE_RETRY_MAX_ATTEMPTS + 1):
        retry_client: KiroHttpClient | None = None
        keep_client_open = False

        try:
            payload = rebuild_payload()
            retry_client = new_http_client_factory()
            retry_response = await retry_client.request_with_retry(
                "POST",
                request_url,
                payload,
                stream=True,
            )
            last_response = retry_response

            if retry_response.status_code == 200:
                keep_client_open = True
                logger.info(
                    "[ReactiveRetry] Retry {} succeeded after sanitization",
                    retry_attempt,
                )
                return ReactiveRetryResult(
                    response=retry_response,
                    http_client=retry_client,
                    error_text=last_error_text,
                    attempted=True,
                )

            last_error_text = await read_response_error_text(retry_response)
            logger.warning(
                "[ReactiveRetry] Retry {} failed with HTTP {}: {}",
                retry_attempt,
                retry_response.status_code,
                last_error_text[:200],
            )
        except (ValueError, RuntimeError, httpx.HTTPError, HTTPException) as retry_exc:
            last_error_text = f"Reactive retry failed: {retry_exc}"
            logger.error(
                "[ReactiveRetry] Retry {} raised exception: {}",
                retry_attempt,
                retry_exc,
            )
        finally:
            if retry_client is not None and not keep_client_open:
                await retry_client.close()

    return ReactiveRetryResult(
        response=last_response,
        http_client=http_client,
        error_text=last_error_text,
        attempted=True,
    )
