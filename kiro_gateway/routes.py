# -*- coding: utf-8 -*-

# Kiro Gateway
# https://github.com/jwadow/kiro-gateway
# Copyright (C) 2025 Jwadow
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
FastAPI routes for Kiro Gateway.

Contains all API endpoints:
- / and /health: Health check
- /v1/models: Models list
- /v1/chat/completions: Chat completions
"""

import asyncio
import json
import secrets
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Security
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import APIKeyHeader
from loguru import logger

from kiro_gateway.config import (
    PROXY_API_KEY,
    AVAILABLE_MODELS,
    APP_VERSION,
)
from kiro_gateway.models import (
    OpenAIModel,
    ModelList,
    ChatCompletionRequest,
)
from kiro_gateway.auth import KiroAuthManager, AuthType
from kiro_gateway.cache import ModelInfoCache
from kiro_gateway.converters import build_kiro_payload
from kiro_gateway.streaming import stream_kiro_to_openai, collect_stream_response, stream_with_first_token_retry
from kiro_gateway.http_client import KiroHttpClient
from kiro_gateway.utils import get_kiro_headers, generate_conversation_id
from kiro_gateway.anthropic_models import (
    AnthropicCountTokensRequest,
    AnthropicCreateMessageBatchRequest,
    AnthropicCreateMessageRequest,
)
from kiro_gateway.anthropic_converters import (
    anthropic_count_tokens_to_openai_messages_and_tools,
    anthropic_request_to_openai_chat_completion_request,
    openai_chat_completion_to_anthropic_message,
)
from kiro_gateway.anthropic_streaming import stream_openai_sse_to_anthropic_sse
from kiro_gateway.tokenizer import estimate_request_tokens

# Import debug_logger
try:
    from kiro_gateway.debug_logger import debug_logger
except ImportError:
    debug_logger = None


# --- Security scheme ---
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
anthropic_api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def validate_api_key(api_key: str) -> bool:
    return bool(api_key) and secrets.compare_digest(api_key, PROXY_API_KEY)


async def verify_api_key(auth_header: str = Security(api_key_header)) -> bool:
    """
    Verify API key in Authorization header.
    
    Expects format: "Bearer {PROXY_API_KEY}"
    
    Args:
        auth_header: Authorization header value
    
    Returns:
        True if key is valid
    
    Raises:
        HTTPException: 401 if key is invalid or missing
    """
    if not auth_header or auth_header != f"Bearer {PROXY_API_KEY}":
        logger.warning("Access attempt with invalid API key.")
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    return True


async def verify_any_api_key(
    auth_header: str = Security(api_key_header),
    x_api_key: str = Security(anthropic_api_key_header),
) -> bool:
    if auth_header:
        return await verify_api_key(auth_header)
    if x_api_key and validate_api_key(x_api_key):
        return True
    logger.warning("Access attempt with missing or invalid API key.")
    raise HTTPException(status_code=401, detail="Invalid or missing API Key")


# --- Router ---
router = APIRouter()


@router.get("/")
async def root():
    """
    Health check endpoint.
    
    Returns:
        Status and application version
    """
    return {
        "status": "ok",
        "message": "Kiro Gateway is running",
        "version": APP_VERSION
    }


@router.get("/health")
async def health():
    """
    Detailed health check.
    
    Returns:
        Status, timestamp and version
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": APP_VERSION
    }


@router.get("/v1/models", dependencies=[Depends(verify_any_api_key)])
async def get_models(request: Request):
    """
    Return list of available models.
    
    Uses static model list with ability to update from API.
    Caches results to reduce API load.
    
    Args:
        request: FastAPI Request for accessing app.state
    
    Returns:
        ModelList with available models
    """
    logger.info("Request to /v1/models")

    if request.headers.get("anthropic-version"):
        models = []
        for model_id in AVAILABLE_MODELS:
            models.append(
                {
                    "id": model_id,
                    "type": "model",
                    "display_name": model_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        first_id = models[0]["id"] if models else None
        last_id = models[-1]["id"] if models else None
        return {
            "data": models,
            "first_id": first_id,
            "last_id": last_id,
            "has_more": False,
        }
    
    auth_manager: KiroAuthManager = request.app.state.auth_manager
    model_cache: ModelInfoCache = request.app.state.model_cache
    
    # Try to get models from API if cache is empty or stale
    if model_cache.is_empty() or model_cache.is_stale():
        try:
            token = await auth_manager.get_access_token()
            headers = get_kiro_headers(auth_manager, token)
            
            # Build params - profileArn is only needed for Kiro Desktop auth
            # AWS SSO OIDC (Builder ID) users don't need profileArn and it causes 403 if sent
            params = {"origin": "AI_EDITOR"}
            if auth_manager.auth_type == AuthType.KIRO_DESKTOP and auth_manager.profile_arn:
                params["profileArn"] = auth_manager.profile_arn
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{auth_manager.q_host}/ListAvailableModels",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    models_list = data.get("models", [])
                    await model_cache.update(models_list)
                    logger.info(f"Received {len(models_list)} models from API")
        except Exception as e:
            logger.warning(f"Failed to fetch models from API: {e}")
    
    # Return static model list
    openai_models = [
        OpenAIModel(
            id=model_id,
            owned_by="anthropic",
            description="Claude model via Kiro API"
        )
        for model_id in AVAILABLE_MODELS
    ]
    
    return ModelList(data=openai_models)


@router.get("/v1/models/{model_id}", dependencies=[Depends(verify_any_api_key)])
async def get_model_by_id(request: Request, model_id: str):
    if not request.headers.get("anthropic-version"):
        raise HTTPException(status_code=404, detail="Not Found")
    return {
        "id": model_id,
        "type": "model",
        "display_name": model_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _anthropic_error(message: str, error_type: str = "api_error") -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"type": "error", "error": {"type": error_type, "message": message}},
    )


async def _select_auth_manager(request: Request) -> KiroAuthManager:
    account_manager = getattr(request.app.state, "account_manager", None)
    if account_manager and account_manager.account_count > 0:
        auth_manager = await account_manager.get_next_account()
        if auth_manager:
            return auth_manager
    return request.app.state.auth_manager


@router.post("/v1/messages", dependencies=[Depends(verify_any_api_key)])
async def anthropic_messages(request: Request, request_data: AnthropicCreateMessageRequest):
    openai_request = anthropic_request_to_openai_chat_completion_request(request_data)

    auth_manager = await _select_auth_manager(request)
    model_cache: ModelInfoCache = request.app.state.model_cache

    conversation_id = generate_conversation_id()
    profile_arn_for_payload = ""
    if auth_manager.auth_type == AuthType.KIRO_DESKTOP and auth_manager.profile_arn:
        profile_arn_for_payload = auth_manager.profile_arn

    try:
        kiro_payload = build_kiro_payload(openai_request, conversation_id, profile_arn_for_payload)
    except ValueError as e:
        return _anthropic_error(str(e), error_type="invalid_request_error")

    http_client = KiroHttpClient(auth_manager)
    url = f"{auth_manager.api_host}/generateAssistantResponse"

    response = await http_client.request_with_retry("POST", url, kiro_payload, stream=True)

    if response.status_code != 200:
        try:
            error_text = (await response.aread()).decode("utf-8", errors="replace")
        except Exception:
            error_text = "Unknown error"
        try:
            await response.aclose()
        except Exception:
            pass
        await http_client.close()
        return _anthropic_error(error_text, error_type="api_error")

    messages_for_tokenizer = [m.model_dump() for m in openai_request.messages]
    tools_for_tokenizer = [t.model_dump() for t in openai_request.tools] if openai_request.tools else None

    if request_data.stream:

        async def openai_stream() -> AsyncGenerator[str, None]:
            try:
                async for chunk in stream_kiro_to_openai(
                    http_client.client,
                    response,
                    openai_request.model,
                    model_cache,
                    auth_manager,
                    request_messages=messages_for_tokenizer,
                    request_tools=tools_for_tokenizer,
                ):
                    yield chunk
            finally:
                await http_client.close()

        async def anthropic_stream() -> AsyncGenerator[str, None]:
            async for out in stream_openai_sse_to_anthropic_sse(openai_stream(), model=openai_request.model):
                yield out

        return StreamingResponse(anthropic_stream(), media_type="text/event-stream")

    openai_response = await collect_stream_response(
        http_client.client,
        response,
        openai_request.model,
        model_cache,
        auth_manager,
        request_messages=messages_for_tokenizer,
        request_tools=tools_for_tokenizer,
    )
    await http_client.close()
    return JSONResponse(content=openai_chat_completion_to_anthropic_message(openai_response))


@router.post("/v1/messages/count_tokens", dependencies=[Depends(verify_any_api_key)])
async def anthropic_count_tokens(request: Request, request_data: AnthropicCountTokensRequest):
    messages_payload, tools_payload, _ = anthropic_count_tokens_to_openai_messages_and_tools(request_data)
    token_detail = estimate_request_tokens(messages_payload, tools=tools_payload)
    return {"input_tokens": token_detail["total_tokens"]}


_anthropic_batches: dict[str, dict] = {}
_anthropic_batch_results: dict[str, list[dict]] = {}
_anthropic_batch_tasks: dict[str, asyncio.Task] = {}


async def _run_anthropic_batch(app, batch_id: str) -> None:
    batch = _anthropic_batches.get(batch_id)
    if not batch:
        return

    requests_list = list(batch.get("requests") or [])
    counts = batch["request_counts"]
    counts["processing"] = len(requests_list)

    for item in requests_list:
        if batch.get("processing_status") == "canceled":
            break

        custom_id = item.get("custom_id")
        params = item.get("params") or {}
        try:
            msg_req = AnthropicCreateMessageRequest(**{**params, "stream": False})
            openai_req = anthropic_request_to_openai_chat_completion_request(msg_req)

            auth_manager = app.state.auth_manager
            model_cache = app.state.model_cache
            conversation_id = generate_conversation_id()
            profile_arn_for_payload = ""
            if auth_manager.auth_type == AuthType.KIRO_DESKTOP and auth_manager.profile_arn:
                profile_arn_for_payload = auth_manager.profile_arn

            kiro_payload = build_kiro_payload(openai_req, conversation_id, profile_arn_for_payload)

            http_client = KiroHttpClient(auth_manager)
            url = f"{auth_manager.api_host}/generateAssistantResponse"
            response = await http_client.request_with_retry("POST", url, kiro_payload, stream=True)

            messages_for_tokenizer = [m.model_dump() for m in openai_req.messages]
            tools_for_tokenizer = [t.model_dump() for t in openai_req.tools] if openai_req.tools else None
            openai_response = await collect_stream_response(
                http_client.client,
                response,
                openai_req.model,
                model_cache,
                auth_manager,
                request_messages=messages_for_tokenizer,
                request_tools=tools_for_tokenizer,
            )
            await http_client.close()

            _anthropic_batch_results[batch_id].append(
                {
                    "custom_id": custom_id,
                    "result": {
                        "type": "succeeded",
                        "message": openai_chat_completion_to_anthropic_message(openai_response),
                    },
                }
            )
            counts["succeeded"] += 1
        except Exception as e:
            _anthropic_batch_results[batch_id].append(
                {
                    "custom_id": custom_id,
                    "result": {
                        "type": "errored",
                        "error": {"type": "internal_error", "message": str(e)},
                    },
                }
            )
            counts["errored"] += 1
        finally:
            counts["processing"] = max(0, counts["processing"] - 1)

    if batch.get("processing_status") != "canceled":
        batch["processing_status"] = "ended"


@router.post("/v1/messages/batches", dependencies=[Depends(verify_any_api_key)])
async def create_message_batch(request: Request, request_data: AnthropicCreateMessageBatchRequest):
    batch_id = f"msgbatch_{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc).isoformat()
    _anthropic_batch_results[batch_id] = []

    base_url = str(request.base_url).rstrip("/")
    results_url = f"{base_url}/v1/messages/batches/{batch_id}/results"

    batch = {
        "id": batch_id,
        "type": "message_batch",
        "created_at": now,
        "processing_status": "in_progress",
        "request_counts": {
            "processing": 0,
            "succeeded": 0,
            "errored": 0,
            "canceled": 0,
            "expired": 0,
        },
        "results_url": results_url,
        "requests": [r.model_dump() for r in request_data.requests],
    }
    _anthropic_batches[batch_id] = batch

    _anthropic_batch_tasks[batch_id] = asyncio.create_task(_run_anthropic_batch(request.app, batch_id))

    return {k: v for k, v in batch.items() if k != "requests"}


@router.get("/v1/messages/batches", dependencies=[Depends(verify_any_api_key)])
async def list_message_batches(request: Request):
    data = [{k: v for k, v in b.items() if k != "requests"} for b in _anthropic_batches.values()]
    return {"data": data, "has_more": False, "first_id": data[0]["id"] if data else None, "last_id": data[-1]["id"] if data else None}


@router.get("/v1/messages/batches/{batch_id}", dependencies=[Depends(verify_any_api_key)])
async def retrieve_message_batch(request: Request, batch_id: str):
    batch = _anthropic_batches.get(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Not Found")
    return {k: v for k, v in batch.items() if k != "requests"}


@router.post("/v1/messages/batches/{batch_id}/cancel", dependencies=[Depends(verify_any_api_key)])
async def cancel_message_batch(request: Request, batch_id: str):
    batch = _anthropic_batches.get(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Not Found")
    if batch.get("processing_status") in ("ended", "canceled"):
        return {k: v for k, v in batch.items() if k != "requests"}

    batch["processing_status"] = "canceled"
    batch["request_counts"]["canceled"] = len(batch.get("requests") or [])
    return {k: v for k, v in batch.items() if k != "requests"}


@router.delete("/v1/messages/batches/{batch_id}", dependencies=[Depends(verify_any_api_key)])
async def delete_message_batch(request: Request, batch_id: str):
    _anthropic_batches.pop(batch_id, None)
    _anthropic_batch_results.pop(batch_id, None)
    task = _anthropic_batch_tasks.pop(batch_id, None)
    if task:
        task.cancel()
    return {"deleted": True, "id": batch_id}


@router.get("/v1/messages/batches/{batch_id}/results", dependencies=[Depends(verify_any_api_key)])
async def get_message_batch_results(request: Request, batch_id: str):
    if batch_id not in _anthropic_batches:
        raise HTTPException(status_code=404, detail="Not Found")

    async def gen() -> AsyncGenerator[str, None]:
        yielded = 0
        while True:
            results = _anthropic_batch_results.get(batch_id, [])
            while yielded < len(results):
                yield json.dumps(results[yielded], ensure_ascii=False) + "\n"
                yielded += 1

            batch = _anthropic_batches.get(batch_id)
            if not batch or batch.get("processing_status") in ("ended", "canceled"):
                break
            await asyncio.sleep(0.05)

    return StreamingResponse(gen(), media_type="application/x-ndjson")


@router.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
async def chat_completions(request: Request, request_data: ChatCompletionRequest):
    """
    Chat completions endpoint - compatible with OpenAI API.
    
    Accepts requests in OpenAI format and translates them to Kiro API.
    Supports streaming and non-streaming modes.
    
    Args:
        request: FastAPI Request for accessing app.state
        request_data: Request in OpenAI ChatCompletionRequest format
    
    Returns:
        StreamingResponse for streaming mode
        JSONResponse for non-streaming mode
    
    Raises:
        HTTPException: On validation or API errors
    """
    logger.info(f"Request to /v1/chat/completions (model={request_data.model}, stream={request_data.stream})")
    
    auth_manager: KiroAuthManager = request.app.state.auth_manager
    model_cache: ModelInfoCache = request.app.state.model_cache
    
    # Prepare debug logs
    if debug_logger:
        debug_logger.prepare_new_request()
    
    # Log incoming request
    try:
        request_body = json.dumps(request_data.model_dump(), ensure_ascii=False, indent=2).encode('utf-8')
        if debug_logger:
            debug_logger.log_request_body(request_body)
    except Exception as e:
        logger.warning(f"Failed to log request body: {e}")
    
    # Lazy model cache population
    if model_cache.is_empty():
        logger.debug("Model cache is empty, skipping forced population")
    
    # Generate conversation ID
    conversation_id = generate_conversation_id()
    
    # Build payload for Kiro
    # profileArn is only needed for Kiro Desktop auth
    # AWS SSO OIDC (Builder ID) users don't need profileArn and it causes 403 if sent
    profile_arn_for_payload = ""
    if auth_manager.auth_type == AuthType.KIRO_DESKTOP and auth_manager.profile_arn:
        profile_arn_for_payload = auth_manager.profile_arn
    
    try:
        kiro_payload = build_kiro_payload(
            request_data,
            conversation_id,
            profile_arn_for_payload
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Log Kiro payload
    try:
        kiro_request_body = json.dumps(kiro_payload, ensure_ascii=False, indent=2).encode('utf-8')
        if debug_logger:
            debug_logger.log_kiro_request_body(kiro_request_body)
    except Exception as e:
        logger.warning(f"Failed to log Kiro request: {e}")
    
    # Create HTTP client with retry logic
    http_client = KiroHttpClient(auth_manager)
    url = f"{auth_manager.api_host}/generateAssistantResponse"
    try:
        # Make request to Kiro API (for both streaming and non-streaming modes)
        # Important: we wait for Kiro response BEFORE returning StreamingResponse,
        # so that 200 OK means Kiro accepted the request and started responding
        response = await http_client.request_with_retry(
            "POST",
            url,
            kiro_payload,
            stream=True
        )
        
        if response.status_code != 200:
            try:
                error_content = await response.aread()
            except Exception:
                error_content = b"Unknown error"
            
            await http_client.close()
            error_text = error_content.decode('utf-8', errors='replace')
            logger.error(f"Error from Kiro API: {response.status_code} - {error_text}")
            
            # Try to parse JSON response from Kiro to extract error message
            error_message = error_text
            try:
                error_json = json.loads(error_text)
                if "message" in error_json:
                    error_message = error_json["message"]
                    if "reason" in error_json:
                        error_message = f"{error_message} (reason: {error_json['reason']})"
            except (json.JSONDecodeError, KeyError):
                pass
            
            # Log access log for error (before flush, so it gets into app_logs)
            logger.warning(
                f"HTTP {response.status_code} - POST /v1/chat/completions - {error_message[:100]}"
            )
            
            # Flush debug logs on error ("errors" mode)
            if debug_logger:
                debug_logger.flush_on_error(response.status_code, error_message)
            
            # Return error in OpenAI API format
            return JSONResponse(
                status_code=response.status_code,
                content={
                    "error": {
                        "message": error_message,
                        "type": "kiro_api_error",
                        "code": response.status_code
                    }
                }
            )
        
        # Prepare data for fallback token counting
        # Convert Pydantic models to dicts for tokenizer
        messages_for_tokenizer = [msg.model_dump() for msg in request_data.messages]
        tools_for_tokenizer = [tool.model_dump() for tool in request_data.tools] if request_data.tools else None
        
        if request_data.stream:
            # Streaming mode
            async def stream_wrapper():
                streaming_error = None
                client_disconnected = False
                try:
                    async for chunk in stream_kiro_to_openai(
                        http_client.client,
                        response,
                        request_data.model,
                        model_cache,
                        auth_manager,
                        request_messages=messages_for_tokenizer,
                        request_tools=tools_for_tokenizer
                    ):
                        yield chunk
                except GeneratorExit:
                    # Client disconnected - this is normal
                    client_disconnected = True
                    logger.debug("Client disconnected during streaming (GeneratorExit in routes)")
                except Exception as e:
                    streaming_error = e
                    # Try to send [DONE] to client before finishing
                    # so client doesn't "hang" waiting for data
                    try:
                        yield "data: [DONE]\n\n"
                    except Exception:
                        pass  # Client already disconnected
                    raise
                finally:
                    await http_client.close()
                    # Log access log for streaming (success or error)
                    if streaming_error:
                        error_type = type(streaming_error).__name__
                        error_msg = str(streaming_error) if str(streaming_error) else "(empty message)"
                        logger.error(f"HTTP 500 - POST /v1/chat/completions (streaming) - [{error_type}] {error_msg[:100]}")
                    elif client_disconnected:
                        logger.info(f"HTTP 200 - POST /v1/chat/completions (streaming) - client disconnected")
                    else:
                        logger.info(f"HTTP 200 - POST /v1/chat/completions (streaming) - completed")
                    # Write debug logs AFTER streaming completes
                    if debug_logger:
                        if streaming_error:
                            debug_logger.flush_on_error(500, str(streaming_error))
                        else:
                            debug_logger.discard_buffers()
            
            return StreamingResponse(stream_wrapper(), media_type="text/event-stream")
        
        else:
            
            # Non-streaming mode - collect entire response
            openai_response = await collect_stream_response(
                http_client.client,
                response,
                request_data.model,
                model_cache,
                auth_manager,
                request_messages=messages_for_tokenizer,
                request_tools=tools_for_tokenizer
            )
            
            await http_client.close()
            
            # Log access log for non-streaming success
            logger.info(f"HTTP 200 - POST /v1/chat/completions (non-streaming) - completed")
            
            # Write debug logs after non-streaming request completes
            if debug_logger:
                debug_logger.discard_buffers()
            
            return JSONResponse(content=openai_response)
    
    except HTTPException as e:
        await http_client.close()
        # Log access log for HTTP error
        logger.warning(f"HTTP {e.status_code} - POST /v1/chat/completions - {e.detail}")
        # Flush debug logs on HTTP error ("errors" mode)
        if debug_logger:
            debug_logger.flush_on_error(e.status_code, str(e.detail))
        raise
    except Exception as e:
        await http_client.close()
        logger.error(f"Internal error: {e}", exc_info=True)
        # Log access log for internal error
        logger.error(f"HTTP 500 - POST /v1/chat/completions - {str(e)[:100]}")
        # Flush debug logs on internal error ("errors" mode)
        if debug_logger:
            debug_logger.flush_on_error(500, str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")