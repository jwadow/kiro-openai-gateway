# -*- coding: utf-8 -*-

"""
Unit tests for exception handlers.
Tests validation error handling and debug logging integration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from fastapi.exceptions import RequestValidationError


class TestSanitizeValidationErrors:
    """Tests for sanitize_validation_errors function."""

    def test_sanitizes_bytes_in_input_field(self):
        """
        What it does: Verifies that bytes in 'input' field are converted to strings.
        Purpose: Ensure JSON serialization works for bytes objects.
        """
        print("Setup: Creating error with bytes in input field...")
        from kiro.exceptions import sanitize_validation_errors

        errors = [
            {
                "type": "json_invalid",
                "loc": ["body", 0],
                "msg": "Invalid JSON",
                "input": b'{"invalid": json}',
            }
        ]

        print("Action: Calling sanitize_validation_errors...")
        result = sanitize_validation_errors(errors)

        print(f"Comparing input type: Expected str, Got {type(result[0]['input'])}")
        assert isinstance(result[0]["input"], str)
        assert result[0]["input"] == '{"invalid": json}'

    def test_sanitizes_bytes_in_list_values(self):
        """
        What it does: Verifies that bytes in list values are converted to strings.
        Purpose: Ensure nested bytes are handled.
        """
        print("Setup: Creating error with bytes in list...")
        from kiro.exceptions import sanitize_validation_errors

        errors = [
            {
                "type": "value_error",
                "loc": ["body", "messages"],
                "msg": "Invalid value",
                "input": [b"bytes1", "string", b"bytes2"],
            }
        ]

        print("Action: Calling sanitize_validation_errors...")
        result = sanitize_validation_errors(errors)

        print("Checking list values are converted...")
        assert result[0]["input"] == ["bytes1", "string", "bytes2"]

    def test_preserves_non_bytes_values(self):
        """
        What it does: Verifies that non-bytes values are preserved.
        Purpose: Ensure normal values are not modified.
        """
        print("Setup: Creating error with normal values...")
        from kiro.exceptions import sanitize_validation_errors

        errors = [
            {
                "type": "missing",
                "loc": ["body", "model"],
                "msg": "Field required",
                "input": {"messages": []},
            }
        ]

        print("Action: Calling sanitize_validation_errors...")
        result = sanitize_validation_errors(errors)

        print("Checking values are preserved...")
        assert result[0]["input"] == {"messages": []}
        assert result[0]["type"] == "missing"


class TestValidationExceptionHandler:
    """Tests for validation_exception_handler function."""

    @pytest.mark.asyncio
    async def test_returns_422_status_code(self):
        """
        What it does: Verifies that handler returns 422 status code.
        Purpose: Ensure proper HTTP status for validation errors.
        """
        print("Setup: Creating mock request and exception...")
        from kiro.exceptions import validation_exception_handler

        mock_request = MagicMock(spec=Request)
        mock_request.body = AsyncMock(return_value=b'{"invalid": json}')

        mock_exc = MagicMock(spec=RequestValidationError)
        mock_exc.errors.return_value = [
            {
                "type": "json_invalid",
                "loc": ["body"],
                "msg": "Invalid JSON",
                "input": {},
            }
        ]

        # Patch debug_logger at the source module
        with patch("kiro.debug_logger.debug_logger"):
            print("Action: Calling validation_exception_handler...")
            response = await validation_exception_handler(mock_request, mock_exc)

            print(f"Comparing status_code: Expected 422, Got {response.status_code}")
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_calls_flush_on_error_with_422(self):
        """
        What it does: Verifies that handler calls flush_on_error(422).
        Purpose: Ensure debug logs are flushed for validation errors.
        """
        print("Setup: Creating mock request and exception...")
        from kiro.exceptions import validation_exception_handler

        mock_request = MagicMock(spec=Request)
        mock_request.body = AsyncMock(return_value=b'{"test": "data"}')

        mock_exc = MagicMock(spec=RequestValidationError)
        mock_exc.errors.return_value = [
            {
                "type": "missing",
                "loc": ["body", "model"],
                "msg": "Field required",
                "input": {},
            }
        ]

        # Patch debug_logger at the source module
        with patch("kiro.debug_logger.debug_logger") as mock_logger:
            print("Action: Calling validation_exception_handler...")
            await validation_exception_handler(mock_request, mock_exc)

            print("Verifying flush_on_error was called with 422...")
            mock_logger.flush_on_error.assert_called_once()
            call_args = mock_logger.flush_on_error.call_args
            assert call_args[0][0] == 422  # First positional argument is status_code

    @pytest.mark.asyncio
    async def test_includes_sanitized_errors_in_response(self):
        """
        What it does: Verifies that response includes sanitized errors.
        Purpose: Ensure error details are returned to client.
        """
        print("Setup: Creating mock request and exception...")
        from kiro.exceptions import validation_exception_handler
        import json

        mock_request = MagicMock(spec=Request)
        mock_request.body = AsyncMock(return_value=b'{"test": "data"}')

        mock_exc = MagicMock(spec=RequestValidationError)
        mock_exc.errors.return_value = [
            {
                "type": "missing",
                "loc": ["body", "model"],
                "msg": "Field required",
                "input": {},
            }
        ]

        with patch("kiro.debug_logger.debug_logger"):
            print("Action: Calling validation_exception_handler...")
            response = await validation_exception_handler(mock_request, mock_exc)

            print("Parsing response body...")
            body = json.loads(response.body.decode())

            print("Verifying 'detail' is in response...")
            assert "detail" in body
            assert len(body["detail"]) == 1
            assert body["detail"][0]["type"] == "missing"

    @pytest.mark.asyncio
    async def test_truncates_body_in_response(self):
        """
        What it does: Verifies that body is truncated to 500 chars in response.
        Purpose: Ensure large bodies don't bloat error responses.
        """
        print("Setup: Creating mock request with large body...")
        from kiro.exceptions import validation_exception_handler
        import json

        large_body = b'{"data": "' + b"x" * 1000 + b'"}'

        mock_request = MagicMock(spec=Request)
        mock_request.body = AsyncMock(return_value=large_body)

        mock_exc = MagicMock(spec=RequestValidationError)
        mock_exc.errors.return_value = [
            {"type": "json_invalid", "loc": ["body"], "msg": "Invalid", "input": {}}
        ]

        with patch("kiro.debug_logger.debug_logger"):
            print("Action: Calling validation_exception_handler...")
            response = await validation_exception_handler(mock_request, mock_exc)

            print("Parsing response body...")
            body = json.loads(response.body.decode())

            print("Verifying body is truncated to 500 chars...")
            assert len(body["body"]) <= 500


class TestValidationExceptionHandlerLogging:
    """Tests for logging behavior in validation_exception_handler."""

    @pytest.mark.asyncio
    async def test_logs_error_at_error_level(self):
        """
        What it does: Verifies that validation error is logged at ERROR level.
        Purpose: Ensure errors are visible in logs.
        """
        print("Setup: Creating mock request and exception...")
        from kiro.exceptions import validation_exception_handler

        mock_request = MagicMock(spec=Request)
        mock_request.body = AsyncMock(return_value=b'{"test": "data"}')

        mock_exc = MagicMock(spec=RequestValidationError)
        mock_exc.errors.return_value = [
            {
                "type": "missing",
                "loc": ["body", "model"],
                "msg": "Field required",
                "input": {},
            }
        ]

        with patch("kiro.debug_logger.debug_logger"):
            with patch("kiro.exceptions.logger") as mock_logger:
                print("Action: Calling validation_exception_handler...")
                await validation_exception_handler(mock_request, mock_exc)

                print("Verifying logger.error was called...")
                mock_logger.error.assert_called()


class TestValidationExceptionHandlerEdgeCases:
    """Tests for edge cases in validation_exception_handler."""

    @pytest.mark.asyncio
    async def test_handles_empty_errors_list(self):
        """
        What it does: Verifies that handler works with empty errors list.
        Purpose: Ensure edge case doesn't cause crash.
        """
        print("Setup: Creating mock request with empty errors...")
        from kiro.exceptions import validation_exception_handler
        import json

        mock_request = MagicMock(spec=Request)
        mock_request.body = AsyncMock(return_value=b"{}")

        mock_exc = MagicMock(spec=RequestValidationError)
        mock_exc.errors.return_value = []

        with patch("kiro.debug_logger.debug_logger"):
            print("Action: Calling validation_exception_handler...")
            response = await validation_exception_handler(mock_request, mock_exc)

            print("Verifying response is valid...")
            assert response.status_code == 422

            body = json.loads(response.body.decode())
            assert body["detail"] == []

    @pytest.mark.asyncio
    async def test_handles_unicode_in_body(self):
        """
        What it does: Verifies that handler works with unicode in body.
        Purpose: Ensure international characters are handled.
        """
        print("Setup: Creating mock request with unicode body...")
        from kiro.exceptions import validation_exception_handler
        import json

        unicode_body = '{"message": "Привет мир 🌍"}'.encode("utf-8")

        mock_request = MagicMock(spec=Request)
        mock_request.body = AsyncMock(return_value=unicode_body)

        mock_exc = MagicMock(spec=RequestValidationError)
        mock_exc.errors.return_value = [
            {
                "type": "missing",
                "loc": ["body", "model"],
                "msg": "Field required",
                "input": {},
            }
        ]

        with patch("kiro.debug_logger.debug_logger"):
            print("Action: Calling validation_exception_handler...")
            response = await validation_exception_handler(mock_request, mock_exc)

            print("Verifying response is valid...")
            assert response.status_code == 422

            body = json.loads(response.body.decode())
            assert "Привет мир" in body["body"]
