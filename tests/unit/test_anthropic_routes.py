# -*- coding: utf-8 -*-

from unittest.mock import AsyncMock, patch

import pytest


class TestAnthropicRoutes:
    def test_count_tokens_works(self, test_client, valid_proxy_api_key):
        resp = test_client.post(
            "/v1/messages/count_tokens",
            headers={"x-api-key": valid_proxy_api_key, "anthropic-version": "2023-06-01"},
            json={
                "model": "claude-sonnet-4-5",
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert resp.status_code == 200
        assert resp.json()["input_tokens"] > 0

    def test_models_anthropic_version_returns_anthropic_shape(self, test_client, valid_proxy_api_key):
        resp = test_client.get(
            "/v1/models",
            headers={"x-api-key": valid_proxy_api_key, "anthropic-version": "2023-06-01"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "has_more" in body

    def test_model_by_id_requires_anthropic_version(self, test_client, valid_proxy_api_key):
        resp = test_client.get(
            "/v1/models/claude-sonnet-4-5",
            headers={"x-api-key": valid_proxy_api_key},
        )
        assert resp.status_code == 404

        resp2 = test_client.get(
            "/v1/models/claude-sonnet-4-5",
            headers={"x-api-key": valid_proxy_api_key, "anthropic-version": "2023-06-01"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["id"] == "claude-sonnet-4-5"

    def test_messages_non_stream_returns_message(self, test_client, valid_proxy_api_key, mock_httpx_response, mock_kiro_simple_text_chunks):
        async def _fake_request_with_retry(self, method, url, json_data, stream=False):
            self.client = AsyncMock()
            self.client.is_closed = False
            self.client.aclose = AsyncMock()
            return mock_httpx_response(status_code=200, stream_chunks=mock_kiro_simple_text_chunks)

        with patch("kiro_gateway.routes.KiroHttpClient.request_with_retry", new=_fake_request_with_retry):
            resp = test_client.post(
                "/v1/messages",
                headers={"x-api-key": valid_proxy_api_key, "anthropic-version": "2023-06-01"},
                json={
                    "model": "claude-sonnet-4-5",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": False,
                },
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["type"] == "message"
        assert body["role"] == "assistant"
