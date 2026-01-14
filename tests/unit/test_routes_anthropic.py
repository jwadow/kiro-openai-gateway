# -*- coding: utf-8 -*-

"""
Unit tests for Anthropic API endpoints (routes_anthropic.py).

Tests the following endpoint:
- POST /v1/messages - Anthropic Messages API

For OpenAI API tests, see test_routes_openai.py.
"""

import pytest
from unittest.mock import patch, MagicMock

from fastapi import HTTPException

from kiro.routes_anthropic import verify_anthropic_api_key, router
from kiro.config import PROXY_API_KEY


# =============================================================================
# Tests for verify_anthropic_api_key function
# =============================================================================


class TestVerifyAnthropicApiKey:
    """Tests for the verify_anthropic_api_key authentication function."""

    @pytest.mark.asyncio
    async def test_valid_x_api_key_returns_true(self):
        """
        What it does: Verifies that a valid x-api-key header passes authentication.
        Purpose: Ensure Anthropic native authentication works.
        """
        print("Setup: Creating valid x-api-key...")

        print("Action: Calling verify_anthropic_api_key...")
        result = await verify_anthropic_api_key(
            x_api_key=PROXY_API_KEY, authorization=None
        )

        print(f"Comparing result: Expected True, Got {result}")
        assert result is True

    @pytest.mark.asyncio
    async def test_valid_bearer_token_returns_true(self):
        """
        What it does: Verifies that a valid Bearer token passes authentication.
        Purpose: Ensure OpenAI-style authentication also works.
        """
        print("Setup: Creating valid Bearer token...")
        valid_auth = f"Bearer {PROXY_API_KEY}"

        print("Action: Calling verify_anthropic_api_key...")
        result = await verify_anthropic_api_key(
            x_api_key=None, authorization=valid_auth
        )

        print(f"Comparing result: Expected True, Got {result}")
        assert result is True

    @pytest.mark.asyncio
    async def test_x_api_key_takes_precedence(self):
        """
        What it does: Verifies x-api-key is checked before Authorization header.
        Purpose: Ensure Anthropic native auth has priority.
        """
        print("Setup: Both headers provided...")

        print("Action: Calling verify_anthropic_api_key with both headers...")
        result = await verify_anthropic_api_key(
            x_api_key=PROXY_API_KEY, authorization="Bearer wrong_key"
        )

        print(f"Comparing result: Expected True, Got {result}")
        assert result is True

    @pytest.mark.asyncio
    async def test_invalid_x_api_key_raises_401(self):
        """
        What it does: Verifies that an invalid x-api-key is rejected.
        Purpose: Ensure unauthorized access is blocked.
        """
        print("Setup: Creating invalid x-api-key...")

        print("Action: Calling verify_anthropic_api_key with invalid key...")
        with pytest.raises(HTTPException) as exc_info:
            await verify_anthropic_api_key(x_api_key="wrong_key", authorization=None)

        print("Checking: HTTPException with status 401...")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_bearer_token_raises_401(self):
        """
        What it does: Verifies that an invalid Bearer token is rejected.
        Purpose: Ensure unauthorized access is blocked.
        """
        print("Setup: Creating invalid Bearer token...")

        print("Action: Calling verify_anthropic_api_key with invalid token...")
        with pytest.raises(HTTPException) as exc_info:
            await verify_anthropic_api_key(
                x_api_key=None, authorization="Bearer wrong_key"
            )

        print("Checking: HTTPException with status 401...")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_both_headers_raises_401(self):
        """
        What it does: Verifies that missing both headers is rejected.
        Purpose: Ensure authentication is required.
        """
        print("Setup: No authentication headers...")

        print("Action: Calling verify_anthropic_api_key with no headers...")
        with pytest.raises(HTTPException) as exc_info:
            await verify_anthropic_api_key(x_api_key=None, authorization=None)

        print("Checking: HTTPException with status 401...")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_x_api_key_raises_401(self):
        """
        What it does: Verifies that empty x-api-key is rejected.
        Purpose: Ensure empty credentials are blocked.
        """
        print("Setup: Empty x-api-key...")

        print("Action: Calling verify_anthropic_api_key with empty key...")
        with pytest.raises(HTTPException) as exc_info:
            await verify_anthropic_api_key(x_api_key="", authorization=None)

        print("Checking: HTTPException with status 401...")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_error_response_format_is_anthropic_style(self):
        """
        What it does: Verifies error response follows Anthropic format.
        Purpose: Ensure error format matches Anthropic API.
        """
        print("Setup: Invalid credentials...")

        print("Action: Calling verify_anthropic_api_key...")
        with pytest.raises(HTTPException) as exc_info:
            await verify_anthropic_api_key(x_api_key="wrong", authorization=None)

        print("Checking: Error format...")
        detail = exc_info.value.detail
        assert "type" in detail
        assert "error" in detail
        assert detail["error"]["type"] == "authentication_error"


# =============================================================================
# Tests for /v1/messages endpoint authentication
# =============================================================================


class TestMessagesAuthentication:
    """Tests for authentication on /v1/messages endpoint."""

    def test_messages_requires_authentication(self, test_client):
        """
        What it does: Verifies messages endpoint requires authentication.
        Purpose: Ensure protected endpoint is secured.
        """
        print("Action: POST /v1/messages without auth...")
        response = test_client.post(
            "/v1/messages",
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 401

    def test_messages_accepts_x_api_key(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies messages endpoint accepts x-api-key header.
        Purpose: Ensure Anthropic native authentication works.
        """
        print("Action: POST /v1/messages with x-api-key...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        # Should pass auth (not 401)
        assert response.status_code != 401

    def test_messages_accepts_bearer_token(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies messages endpoint accepts Bearer token.
        Purpose: Ensure OpenAI-style authentication also works.
        """
        print("Action: POST /v1/messages with Bearer token...")
        response = test_client.post(
            "/v1/messages",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        # Should pass auth (not 401)
        assert response.status_code != 401

    def test_messages_rejects_invalid_x_api_key(
        self, test_client, invalid_proxy_api_key
    ):
        """
        What it does: Verifies messages endpoint rejects invalid x-api-key.
        Purpose: Ensure authentication is enforced.
        """
        print("Action: POST /v1/messages with invalid x-api-key...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": invalid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 401


# =============================================================================
# Tests for /v1/messages endpoint validation
# =============================================================================


class TestMessagesValidation:
    """Tests for request validation on /v1/messages endpoint."""

    def test_validates_missing_model(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies missing model field is rejected.
        Purpose: Ensure model is required.
        """
        print("Action: POST /v1/messages without model...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 422

    def test_validates_missing_max_tokens(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies missing max_tokens field is rejected.
        Purpose: Ensure max_tokens is required (Anthropic API requirement).
        """
        print("Action: POST /v1/messages without max_tokens...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 422

    def test_validates_missing_messages(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies missing messages field is rejected.
        Purpose: Ensure messages are required.
        """
        print("Action: POST /v1/messages without messages...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={"model": "claude-sonnet-4-5", "max_tokens": 1024},
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 422

    def test_validates_empty_messages_array(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies empty messages array is rejected.
        Purpose: Ensure at least one message is required.
        """
        print("Action: POST /v1/messages with empty messages...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={"model": "claude-sonnet-4-5", "max_tokens": 1024, "messages": []},
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 422

    def test_validates_invalid_json(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies invalid JSON is rejected.
        Purpose: Ensure proper JSON parsing.
        """
        print("Action: POST /v1/messages with invalid JSON...")
        response = test_client.post(
            "/v1/messages",
            headers={
                "x-api-key": valid_proxy_api_key,
                "Content-Type": "application/json",
            },
            content=b"not valid json {{{}",
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 422

    def test_validates_invalid_role(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies invalid message role is rejected.
        Purpose: Anthropic model strictly validates role (only 'user' or 'assistant').
        """
        print("Action: POST /v1/messages with invalid role...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "invalid_role", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        # Anthropic model strictly validates role - only 'user' or 'assistant' allowed
        assert response.status_code == 422

    def test_accepts_valid_request_format(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies valid request format passes validation.
        Purpose: Ensure Pydantic validation works correctly.
        """
        print("Action: POST /v1/messages with valid format...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        # Should pass validation (not 422)
        assert response.status_code != 422


# =============================================================================
# Tests for /v1/messages system prompt
# =============================================================================


class TestMessagesSystemPrompt:
    """Tests for system prompt handling on /v1/messages endpoint."""

    def test_accepts_system_as_separate_field(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies system prompt as separate field is accepted.
        Purpose: Ensure Anthropic-style system prompt works.
        """
        print("Action: POST /v1/messages with system field...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "system": "You are a helpful assistant.",
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        # Should pass validation
        assert response.status_code != 422

    def test_accepts_empty_system_prompt(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies empty system prompt is accepted.
        Purpose: Ensure system prompt is optional.
        """
        print("Action: POST /v1/messages with empty system...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "system": "",
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        # Should pass validation
        assert response.status_code != 422

    def test_accepts_no_system_prompt(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies request without system prompt is accepted.
        Purpose: Ensure system prompt is optional.
        """
        print("Action: POST /v1/messages without system field...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        # Should pass validation
        assert response.status_code != 422


# =============================================================================
# Tests for /v1/messages content blocks
# =============================================================================


class TestMessagesContentBlocks:
    """Tests for content block handling on /v1/messages endpoint."""

    def test_accepts_string_content(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies string content is accepted.
        Purpose: Ensure simple string content works.
        """
        print("Action: POST /v1/messages with string content...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422

    def test_accepts_content_block_array(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies content block array is accepted.
        Purpose: Ensure Anthropic content block format works.
        """
        print("Action: POST /v1/messages with content blocks...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": "Hello"}]}
                ],
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422

    def test_accepts_multiple_content_blocks(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies multiple content blocks are accepted.
        Purpose: Ensure complex content works.
        """
        print("Action: POST /v1/messages with multiple content blocks...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "First part"},
                            {"type": "text", "text": "Second part"},
                        ],
                    }
                ],
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422


# =============================================================================
# Tests for /v1/messages tool use
# =============================================================================


class TestMessagesToolUse:
    """Tests for tool use on /v1/messages endpoint."""

    def test_accepts_tool_definition(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies tool definition is accepted.
        Purpose: Ensure Anthropic tool format works.
        """
        print("Action: POST /v1/messages with tools...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "What's the weather?"}],
                "tools": [
                    {
                        "name": "get_weather",
                        "description": "Get weather for a location",
                        "input_schema": {
                            "type": "object",
                            "properties": {"location": {"type": "string"}},
                            "required": ["location"],
                        },
                    }
                ],
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422

    def test_accepts_multiple_tools(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies multiple tools are accepted.
        Purpose: Ensure multiple tool definitions work.
        """
        print("Action: POST /v1/messages with multiple tools...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
                "tools": [
                    {
                        "name": "get_weather",
                        "description": "Get weather",
                        "input_schema": {"type": "object", "properties": {}},
                    },
                    {
                        "name": "get_time",
                        "description": "Get time",
                        "input_schema": {"type": "object", "properties": {}},
                    },
                ],
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422

    def test_accepts_tool_result_message(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies tool result message is accepted.
        Purpose: Ensure tool result handling works.
        """
        print("Action: POST /v1/messages with tool result...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": "What's the weather?"},
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "call_123",
                                "name": "get_weather",
                                "input": {"location": "Moscow"},
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": "call_123",
                                "content": "Sunny, 25°C",
                            }
                        ],
                    },
                ],
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422


# =============================================================================
# Tests for /v1/messages optional parameters
# =============================================================================


class TestMessagesOptionalParams:
    """Tests for optional parameters on /v1/messages endpoint."""

    def test_accepts_temperature_parameter(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies temperature parameter is accepted.
        Purpose: Ensure temperature control works.
        """
        print("Action: POST /v1/messages with temperature...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": 0.7,
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422

    def test_accepts_top_p_parameter(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies top_p parameter is accepted.
        Purpose: Ensure nucleus sampling control works.
        """
        print("Action: POST /v1/messages with top_p...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
                "top_p": 0.9,
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422

    def test_accepts_top_k_parameter(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies top_k parameter is accepted.
        Purpose: Ensure top-k sampling control works.
        """
        print("Action: POST /v1/messages with top_k...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
                "top_k": 40,
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422

    def test_accepts_stream_true(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies stream=true is accepted.
        Purpose: Ensure streaming mode is supported.
        """
        print("Action: POST /v1/messages with stream=true...")

        # Mock the streaming function to avoid real HTTP requests
        async def mock_stream(*args, **kwargs):
            yield 'event: message_start\ndata: {"type":"message_start"}\n\n'
            yield 'event: message_stop\ndata: {"type":"message_stop"}\n\n'

        # Create mock response for HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200

        with (
            patch("kiro.routes_anthropic.stream_kiro_to_anthropic", mock_stream),
            patch(
                "kiro.http_client.KiroHttpClient.request_with_retry",
                return_value=mock_response,
            ),
        ):
            response = test_client.post(
                "/v1/messages",
                headers={"x-api-key": valid_proxy_api_key},
                json={
                    "model": "claude-sonnet-4-5",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": True,
                },
            )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422

    def test_accepts_stop_sequences(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies stop_sequences parameter is accepted.
        Purpose: Ensure stop sequence control works.
        """
        print("Action: POST /v1/messages with stop_sequences...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
                "stop_sequences": ["END", "STOP"],
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422

    def test_accepts_metadata(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies metadata parameter is accepted.
        Purpose: Ensure metadata passing works.
        """
        print("Action: POST /v1/messages with metadata...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
                "metadata": {"user_id": "test_user"},
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422


# =============================================================================
# Tests for /v1/messages anthropic-version header
# =============================================================================


class TestMessagesAnthropicVersion:
    """Tests for anthropic-version header handling."""

    def test_accepts_anthropic_version_header(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies anthropic-version header is accepted.
        Purpose: Ensure Anthropic SDK compatibility.
        """
        print("Action: POST /v1/messages with anthropic-version header...")
        response = test_client.post(
            "/v1/messages",
            headers={
                "x-api-key": valid_proxy_api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        # Should pass validation
        assert response.status_code != 422

    def test_works_without_anthropic_version_header(
        self, test_client, valid_proxy_api_key
    ):
        """
        What it does: Verifies request works without anthropic-version header.
        Purpose: Ensure header is optional.
        """
        print("Action: POST /v1/messages without anthropic-version header...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        # Should pass validation
        assert response.status_code != 422


# =============================================================================
# Tests for router integration
# =============================================================================


class TestAnthropicRouterIntegration:
    """Tests for Anthropic router configuration and integration."""

    def test_router_has_messages_endpoint(self):
        """
        What it does: Verifies messages endpoint is registered.
        Purpose: Ensure endpoint is available.
        """
        print("Checking: Router endpoints...")
        routes = [route.path for route in router.routes]

        print(f"Found routes: {routes}")
        assert "/v1/messages" in routes

    def test_messages_endpoint_uses_post_method(self):
        """
        What it does: Verifies messages endpoint uses POST method.
        Purpose: Ensure correct HTTP method.
        """
        print("Checking: HTTP methods...")
        for route in router.routes:
            if route.path == "/v1/messages":
                print(f"Route /v1/messages methods: {route.methods}")
                assert "POST" in route.methods
                return
        pytest.fail("Messages endpoint not found")

    def test_router_has_anthropic_tag(self):
        """
        What it does: Verifies router has Anthropic API tag.
        Purpose: Ensure proper API documentation grouping.
        """
        print("Checking: Router tags...")
        print(f"Router tags: {router.tags}")
        assert "Anthropic API" in router.tags


# =============================================================================
# Tests for conversation history
# =============================================================================


class TestMessagesConversationHistory:
    """Tests for conversation history handling on /v1/messages endpoint."""

    def test_accepts_multi_turn_conversation(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies multi-turn conversation is accepted.
        Purpose: Ensure conversation history works.
        """
        print("Action: POST /v1/messages with conversation history...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                    {"role": "user", "content": "How are you?"},
                ],
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422

    def test_accepts_long_conversation(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies long conversation is accepted.
        Purpose: Ensure many messages work.
        """
        print("Action: POST /v1/messages with long conversation...")
        messages = []
        for i in range(10):
            messages.append({"role": "user", "content": f"Message {i}"})
            messages.append({"role": "assistant", "content": f"Response {i}"})
        messages.append({"role": "user", "content": "Final question"})

        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": messages,
            },
        )

        print(f"Status: {response.status_code}")
        assert response.status_code != 422


# =============================================================================
# Tests for error response format
# =============================================================================


class TestMessagesErrorFormat:
    """Tests for error response format on /v1/messages endpoint."""

    def test_validation_error_format(self, test_client, valid_proxy_api_key):
        """
        What it does: Verifies validation error response format.
        Purpose: Ensure errors follow expected format.
        """
        print("Action: POST /v1/messages with invalid request...")
        response = test_client.post(
            "/v1/messages",
            headers={"x-api-key": valid_proxy_api_key},
            json={
                "model": "claude-sonnet-4-5"
                # Missing required fields
            },
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 422

    def test_auth_error_format_is_anthropic_style(self, test_client):
        """
        What it does: Verifies auth error follows Anthropic format.
        Purpose: Ensure error format matches Anthropic API.
        """
        print("Action: POST /v1/messages without auth...")
        response = test_client.post(
            "/v1/messages",
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 401

        # Check Anthropic error format
        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert "type" in detail
        assert "error" in detail
