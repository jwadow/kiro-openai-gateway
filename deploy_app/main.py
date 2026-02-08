# -*- coding: utf-8 -*-

"""
Minimal OpenAI-compatible proxy service for Zeabur deployment.

This service exposes:
- GET /health
- POST /v1/chat/completions

It validates a local API key, then forwards chat completions to an upstream
OpenAI-compatible provider.
"""

from __future__ import annotations

import json
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncGenerator

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response, Security
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import APIKeyHeader
from loguru import logger


api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


@dataclass(frozen=True)
class AppSettings:
    """
    Runtime settings loaded from environment variables.

    Attributes:
        app_api_key: API key expected from clients in Authorization header.
        upstream_base_url: Base URL of upstream OpenAI-compatible provider.
        upstream_api_key: API key used when calling upstream provider.
        request_timeout_seconds: Timeout for upstream requests.
    """

    app_api_key: str
    upstream_base_url: str
    upstream_api_key: str
    request_timeout_seconds: float


def load_settings() -> AppSettings:
    """
    Load and validate settings from environment.

    Required env vars:
    - APP_API_KEY
    - UPSTREAM_BASE_URL
    - UPSTREAM_API_KEY

    Optional env vars:
    - REQUEST_TIMEOUT_SECONDS (default: 120)

    Returns:
        Validated AppSettings instance.

    Raises:
        ValueError: If required values are missing or invalid.
    """
    app_api_key = os.getenv("APP_API_KEY", "").strip()
    upstream_base_url = os.getenv("UPSTREAM_BASE_URL", "").strip().rstrip("/")
    upstream_api_key = os.getenv("UPSTREAM_API_KEY", "").strip()
    timeout_raw = os.getenv("REQUEST_TIMEOUT_SECONDS", "120").strip()

    missing_keys = [
        key
        for key, value in {
            "APP_API_KEY": app_api_key,
            "UPSTREAM_BASE_URL": upstream_base_url,
            "UPSTREAM_API_KEY": upstream_api_key,
        }.items()
        if not value
    ]
    if missing_keys:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")

    if not upstream_base_url.startswith(("http://", "https://")):
        raise ValueError("UPSTREAM_BASE_URL must start with http:// or https://")

    try:
        request_timeout_seconds = float(timeout_raw)
    except ValueError as error:
        raise ValueError("REQUEST_TIMEOUT_SECONDS must be a number") from error

    if request_timeout_seconds <= 0:
        raise ValueError("REQUEST_TIMEOUT_SECONDS must be greater than 0")

    return AppSettings(
        app_api_key=app_api_key,
        upstream_base_url=upstream_base_url,
        upstream_api_key=upstream_api_key,
        request_timeout_seconds=request_timeout_seconds,
    )


def _extract_bearer_token(auth_header: str | None) -> str:
    """
    Extract token from Authorization header.

    Args:
        auth_header: Raw Authorization header value.

    Returns:
        Extracted token or empty string when invalid/missing.
    """
    if not auth_header:
        return ""
    prefix = "Bearer "
    if not auth_header.startswith(prefix):
        return ""
    return auth_header[len(prefix):].strip()


def _extract_upstream_error_message(raw_body: bytes) -> str:
    """
    Extract readable error message from upstream response body.

    Args:
        raw_body: Raw response bytes from upstream.

    Returns:
        Human-readable error message.
    """
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        text = raw_body.decode("utf-8", errors="ignore").strip()
        return text or "Upstream provider returned an unknown error"

    if isinstance(payload, dict):
        error_payload = payload.get("error")
        if isinstance(error_payload, dict):
            message = error_payload.get("message")
            reason = error_payload.get("reason")
            if isinstance(message, str) and message.strip():
                return message.strip()
            if isinstance(reason, str) and reason.strip():
                return reason.strip()
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()

    return "Upstream provider returned an unknown error"


def _build_upstream_headers(settings: AppSettings, request_id: str) -> dict[str, str]:
    """
    Build headers sent to upstream provider.

    Args:
        settings: Proxy runtime settings.
        request_id: Request identifier for tracing.

    Returns:
        Header dictionary for upstream call.
    """
    return {
        "Authorization": f"Bearer {settings.upstream_api_key}",
        "Content-Type": "application/json",
        "X-Proxy-Request-Id": request_id,
    }


def create_app() -> FastAPI:
    """
    Create FastAPI application instance.

    Returns:
        Configured FastAPI app.
    """
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        """Load settings during startup and keep them in app state."""
        try:
            application.state.settings = load_settings()
        except ValueError as error:
            logger.error(f"Configuration error: {error}")
            raise RuntimeError(f"Invalid configuration: {error}") from error
        yield

    app = FastAPI(title="Deploy Proxy", version="1.0.0", lifespan=lifespan)

    async def verify_api_key(
        request: Request,
        auth_header: str | None = Security(api_key_header),
    ) -> None:
        """
        Verify proxy API key for incoming requests.

        Args:
            request: FastAPI request object.
            auth_header: Authorization header value.

        Raises:
            HTTPException: 401 if key is missing or invalid.
        """
        settings: AppSettings = request.app.state.settings
        token = _extract_bearer_token(auth_header)
        if token != settings.app_api_key:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

    @app.get("/health")
    async def health() -> dict[str, str]:
        """
        Health check endpoint.

        Returns:
            Service status payload.
        """
        return {"status": "ok"}

    @app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
    async def chat_completions(request: Request, payload: dict[str, Any]) -> Response:
        """
        Forward OpenAI-compatible chat completions to upstream provider.

        Args:
            request: FastAPI request object.
            payload: Incoming chat completions payload.

        Returns:
            JSONResponse for non-stream requests.
            StreamingResponse for stream requests.
        """
        settings: AppSettings = request.app.state.settings
        request_id = str(uuid.uuid4())
        upstream_url = f"{settings.upstream_base_url}/v1/chat/completions"
        stream_mode = bool(payload.get("stream", False))
        headers = _build_upstream_headers(settings, request_id)
        timeout = httpx.Timeout(settings.request_timeout_seconds)

        logger.info(f"Proxy request started (id={request_id}, stream={stream_mode})")

        if not stream_mode:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    upstream_response = await client.post(upstream_url, headers=headers, json=payload)
            except httpx.TimeoutException:
                return JSONResponse(
                    status_code=504,
                    content={
                        "error": "UPSTREAM_TIMEOUT",
                        "detail": "Upstream provider timed out",
                        "request_id": request_id,
                    },
                )
            except httpx.HTTPError as error:
                return JSONResponse(
                    status_code=502,
                    content={
                        "error": "UPSTREAM_NETWORK_ERROR",
                        "detail": f"Unable to reach upstream provider: {error}",
                        "request_id": request_id,
                    },
                )

            if upstream_response.status_code >= 400:
                detail = _extract_upstream_error_message(upstream_response.content)
                return JSONResponse(
                    status_code=upstream_response.status_code,
                    content={
                        "error": "UPSTREAM_ERROR",
                        "detail": detail,
                        "request_id": request_id,
                    },
                )

            try:
                response_json = upstream_response.json()
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=502,
                    content={
                        "error": "UPSTREAM_INVALID_JSON",
                        "detail": "Upstream provider returned invalid JSON",
                        "request_id": request_id,
                    },
                )

            return JSONResponse(
                status_code=upstream_response.status_code,
                content=response_json,
                headers={"X-Proxy-Request-Id": request_id},
            )

        client = httpx.AsyncClient(timeout=timeout)
        try:
            upstream_request = client.build_request("POST", upstream_url, headers=headers, json=payload)
            upstream_response = await client.send(upstream_request, stream=True)
        except httpx.TimeoutException:
            await client.aclose()
            return JSONResponse(
                status_code=504,
                content={
                    "error": "UPSTREAM_TIMEOUT",
                    "detail": "Upstream provider timed out",
                    "request_id": request_id,
                },
            )
        except httpx.HTTPError as error:
            await client.aclose()
            return JSONResponse(
                status_code=502,
                content={
                    "error": "UPSTREAM_NETWORK_ERROR",
                    "detail": f"Unable to reach upstream provider: {error}",
                    "request_id": request_id,
                },
            )

        if upstream_response.status_code >= 400:
            raw_body = await upstream_response.aread()
            await upstream_response.aclose()
            await client.aclose()
            detail = _extract_upstream_error_message(raw_body)
            return JSONResponse(
                status_code=upstream_response.status_code,
                content={
                    "error": "UPSTREAM_ERROR",
                    "detail": detail,
                    "request_id": request_id,
                },
            )

        async def stream_generator() -> AsyncGenerator[bytes, None]:
            """Yield raw SSE bytes from upstream response."""
            try:
                async for chunk in upstream_response.aiter_raw():
                    if chunk:
                        yield chunk
            finally:
                await upstream_response.aclose()
                await client.aclose()

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Proxy-Request-Id": request_id,
            },
        )

    return app


app = create_app()
