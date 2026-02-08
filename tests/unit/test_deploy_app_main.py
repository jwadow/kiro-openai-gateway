# -*- coding: utf-8 -*-

"""Tests for deploy_app.main minimal OpenAI-compatible proxy."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from deploy_app.main import create_app


class StubStreamResponse:
    """Stub streaming response used to emulate upstream SSE behavior."""

    def __init__(self, status_code: int, chunks: list[bytes], body: bytes = b"") -> None:
        """
        Initialize stream response stub.

        Args:
            status_code: Upstream HTTP status code.
            chunks: SSE chunks for successful stream.
            body: Raw response body for error responses.
        """
        self.status_code = status_code
        self._chunks = chunks
        self._body = body
        self.closed = False

    async def aiter_raw(self):
        """Yield raw bytes chunks."""
        for chunk in self._chunks:
            yield chunk

    async def aread(self) -> bytes:
        """Return full error body."""
        return self._body

    async def aclose(self) -> None:
        """Mark response as closed."""
        self.closed = True


class StubAsyncClient:
    """Stub AsyncClient supporting both regular and streaming paths."""

    def __init__(
        self,
        post_response: httpx.Response | None = None,
        send_response: StubStreamResponse | None = None,
    ) -> None:
        """
        Initialize HTTP client stub.

        Args:
            post_response: Response returned by post().
            send_response: Response returned by send(..., stream=True).
        """
        self._post_response = post_response
        self._send_response = send_response
        self.post_calls: list[dict[str, Any]] = []
        self.send_calls: list[dict[str, Any]] = []
        self.closed = False

    async def __aenter__(self) -> "StubAsyncClient":
        """Return self for async context manager usage."""
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Close client on context manager exit."""
        await self.aclose()

    async def post(self, url: str, headers: dict[str, str], json: dict[str, Any]) -> httpx.Response:
        """Record and return stubbed post response."""
        self.post_calls.append({"url": url, "headers": headers, "json": json})
        if self._post_response is None:
            raise AssertionError("post_response not configured")
        return self._post_response

    def build_request(self, method: str, url: str, headers: dict[str, str], json: dict[str, Any]) -> dict[str, Any]:
        """Build a simple dictionary request object for tests."""
        return {"method": method, "url": url, "headers": headers, "json": json}

    async def send(self, request: dict[str, Any], stream: bool) -> StubStreamResponse:
        """Record and return stubbed streaming response."""
        self.send_calls.append({"request": request, "stream": stream})
        if self._send_response is None:
            raise AssertionError("send_response not configured")
        return self._send_response

    async def aclose(self) -> None:
        """Mark client as closed."""
        self.closed = True


@pytest.fixture
def proxy_client(monkeypatch: pytest.MonkeyPatch):
    """Create test client with required environment settings."""
    monkeypatch.setenv("APP_API_KEY", "local-test-key")
    monkeypatch.setenv("UPSTREAM_BASE_URL", "https://upstream.example")
    monkeypatch.setenv("UPSTREAM_API_KEY", "upstream-test-key")
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "30")

    app = create_app()
    with TestClient(app) as client:
        yield client


def test_startup_fails_when_required_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Startup should fail fast when required configuration is missing."""
    monkeypatch.delenv("APP_API_KEY", raising=False)
    monkeypatch.delenv("UPSTREAM_BASE_URL", raising=False)
    monkeypatch.delenv("UPSTREAM_API_KEY", raising=False)

    app = create_app()

    with pytest.raises(RuntimeError, match="Invalid configuration"):
        with TestClient(app):
            pass


def test_chat_completion_rejects_missing_api_key(proxy_client: TestClient) -> None:
    """Request should be rejected when Authorization header is missing."""
    response = proxy_client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_chat_completion_non_stream_success(proxy_client: TestClient) -> None:
    """Non-stream request should be forwarded and return upstream JSON."""
    upstream_response = httpx.Response(
        status_code=200,
        json={"id": "chatcmpl_123", "choices": [{"index": 0}]},
    )
    stub_client = StubAsyncClient(post_response=upstream_response)

    with patch("deploy_app.main.httpx.AsyncClient", return_value=stub_client):
        response = proxy_client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer local-test-key"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": False,
            },
        )

    assert response.status_code == 200
    assert response.json()["id"] == "chatcmpl_123"
    assert len(stub_client.post_calls) == 1
    assert stub_client.post_calls[0]["url"] == "https://upstream.example/v1/chat/completions"
    assert stub_client.post_calls[0]["headers"]["Authorization"] == "Bearer upstream-test-key"


def test_chat_completion_non_stream_upstream_error(proxy_client: TestClient) -> None:
    """Upstream non-stream errors should be mapped to structured proxy errors."""
    upstream_response = httpx.Response(
        status_code=400,
        json={"error": {"message": "bad payload"}},
    )
    stub_client = StubAsyncClient(post_response=upstream_response)

    with patch("deploy_app.main.httpx.AsyncClient", return_value=stub_client):
        response = proxy_client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer local-test-key"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": False,
            },
        )

    assert response.status_code == 400
    assert response.json()["error"] == "UPSTREAM_ERROR"
    assert response.json()["detail"] == "bad payload"


def test_chat_completion_stream_success(proxy_client: TestClient) -> None:
    """Stream request should proxy SSE chunks without modification."""
    stream_response = StubStreamResponse(
        status_code=200,
        chunks=[b"data: hello\n\n", b"data: [DONE]\n\n"],
    )
    stub_client = StubAsyncClient(send_response=stream_response)

    with patch("deploy_app.main.httpx.AsyncClient", return_value=stub_client):
        response = proxy_client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer local-test-key"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": True,
            },
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "data: [DONE]" in response.text
    assert stub_client.closed is True
    assert stream_response.closed is True


def test_chat_completion_stream_upstream_error(proxy_client: TestClient) -> None:
    """Stream upstream error should return JSON error payload."""
    stream_response = StubStreamResponse(
        status_code=401,
        chunks=[],
        body=b'{"error": {"reason": "invalid upstream key"}}',
    )
    stub_client = StubAsyncClient(send_response=stream_response)

    with patch("deploy_app.main.httpx.AsyncClient", return_value=stub_client):
        response = proxy_client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer local-test-key"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": True,
            },
        )

    assert response.status_code == 401
    assert response.json()["error"] == "UPSTREAM_ERROR"
    assert response.json()["detail"] == "invalid upstream key"
    assert stub_client.closed is True
    assert stream_response.closed is True
