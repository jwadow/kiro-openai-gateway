# -*- coding: utf-8 -*-

"""
Unit tests for reactive retry helpers.
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from kiro.reactive_retry import (
    read_response_error_text,
    retry_on_improperly_formed_request,
    should_retry_improperly_formed,
)


def _mock_response(status_code: int, body: str) -> AsyncMock:
    """Create a mocked httpx.Response with async body reader."""
    response = AsyncMock(spec=httpx.Response)
    response.status_code = status_code
    response.aread = AsyncMock(return_value=body.encode("utf-8"))
    return response


class TestShouldRetryImproperlyFormed:
    """Tests for malformed-request detection."""

    def test_returns_true_for_matching_400_message(self):
        """What it does: detects retriable malformed-request response."""
        assert should_retry_improperly_formed(400, "Improperly formed request") is True

    def test_returns_false_for_non_400_status(self):
        """What it does: rejects non-400 statuses."""
        assert should_retry_improperly_formed(500, "Improperly formed request") is False


class TestReadResponseErrorText:
    """Tests for response error body reading helper."""

    @pytest.mark.asyncio
    async def test_reads_text_body(self):
        """What it does: reads and decodes upstream error body."""
        response = _mock_response(400, "bad request")

        result = await read_response_error_text(response)

        assert result == "bad request"

    @pytest.mark.asyncio
    async def test_returns_fallback_when_read_fails(self):
        """What it does: returns fallback text when body read fails."""
        response = AsyncMock(spec=httpx.Response)
        response.status_code = 400
        response.aread = AsyncMock(side_effect=httpx.ReadError("boom"))

        result = await read_response_error_text(response)

        assert result == "Unknown error"


class TestRetryOnImproperlyFormedRequest:
    """Tests for reactive retry execution path."""

    @pytest.mark.asyncio
    async def test_skips_when_condition_not_met(self):
        """What it does: returns original response when retry condition is not met."""
        initial_response = _mock_response(500, "server error")
        initial_client = AsyncMock()
        initial_client.close = AsyncMock()

        with patch("kiro.reactive_retry.REACTIVE_RETRY_ENABLED", True):
            result = await retry_on_improperly_formed_request(
                response=initial_response,
                error_text="server error",
                http_client=initial_client,
                request_url="https://example.test",
                rebuild_payload=Mock(return_value={}),
                new_http_client_factory=Mock(),
            )

        assert result.attempted is False
        assert result.response is initial_response
        initial_client.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_retries_and_returns_successful_response(self):
        """What it does: retries malformed 400 and returns successful retry response."""
        initial_response = _mock_response(400, "Improperly formed request")
        success_response = _mock_response(200, "ok")

        initial_client = AsyncMock()
        initial_client.close = AsyncMock()

        retry_client = AsyncMock()
        retry_client.request_with_retry = AsyncMock(return_value=success_response)
        retry_client.close = AsyncMock()

        rebuild_payload = Mock(return_value={"hello": "world"})
        make_retry_client = Mock(return_value=retry_client)

        with (
            patch("kiro.reactive_retry.REACTIVE_RETRY_ENABLED", True),
            patch("kiro.reactive_retry.REACTIVE_RETRY_MAX_ATTEMPTS", 1),
        ):
            result = await retry_on_improperly_formed_request(
                response=initial_response,
                error_text="Improperly formed request",
                http_client=initial_client,
                request_url="https://example.test",
                rebuild_payload=rebuild_payload,
                new_http_client_factory=make_retry_client,
            )

        assert result.attempted is True
        assert result.response is success_response
        assert result.http_client is retry_client
        initial_client.close.assert_awaited_once()
        rebuild_payload.assert_called_once()
        retry_client.request_with_retry.assert_awaited_once()
        retry_client.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_last_failure_after_exhausting_attempts(self):
        """What it does: returns final failing response when retries are exhausted."""
        initial_response = _mock_response(400, "Improperly formed request")
        retry_response_1 = _mock_response(400, "Improperly formed request #1")
        retry_response_2 = _mock_response(400, "Improperly formed request #2")

        initial_client = AsyncMock()
        initial_client.close = AsyncMock()

        retry_client_1 = AsyncMock()
        retry_client_1.request_with_retry = AsyncMock(return_value=retry_response_1)
        retry_client_1.close = AsyncMock()

        retry_client_2 = AsyncMock()
        retry_client_2.request_with_retry = AsyncMock(return_value=retry_response_2)
        retry_client_2.close = AsyncMock()

        make_retry_client = Mock(side_effect=[retry_client_1, retry_client_2])

        with (
            patch("kiro.reactive_retry.REACTIVE_RETRY_ENABLED", True),
            patch("kiro.reactive_retry.REACTIVE_RETRY_MAX_ATTEMPTS", 2),
        ):
            result = await retry_on_improperly_formed_request(
                response=initial_response,
                error_text="Improperly formed request",
                http_client=initial_client,
                request_url="https://example.test",
                rebuild_payload=Mock(return_value={}),
                new_http_client_factory=make_retry_client,
            )

        assert result.attempted is True
        assert result.response is retry_response_2
        assert result.error_text == "Improperly formed request #2"
        initial_client.close.assert_awaited_once()
        retry_client_1.close.assert_awaited_once()
        retry_client_2.close.assert_awaited_once()
