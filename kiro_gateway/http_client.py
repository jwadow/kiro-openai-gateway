# -*- coding: utf-8 -*-

# Kiro OpenAI Gateway
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
HTTP клиент для Kiro API с поддержкой retry логики.

Обрабатывает:
- 403: автоматический refresh токена и повтор
- 429: exponential backoff
- 5xx: exponential backoff
- Таймауты: exponential backoff
"""

import asyncio
from typing import Optional

import httpx
from fastapi import HTTPException
from loguru import logger

from kiro_gateway.config import MAX_RETRIES, BASE_RETRY_DELAY, FIRST_TOKEN_TIMEOUT, FIRST_TOKEN_MAX_RETRIES, STREAMING_READ_TIMEOUT
from kiro_gateway.auth import KiroAuthManager
from kiro_gateway.utils import get_kiro_headers


class KiroHttpClient:
    """
    HTTP клиент для Kiro API с поддержкой retry логики.
    
    Автоматически обрабатывает ошибки и повторяет запросы:
    - 403: обновляет токен и повторяет
    - 429: ждёт с exponential backoff
    - 5xx: ждёт с exponential backoff
    - Таймауты: ждёт с exponential backoff
    Attributes:
        auth_manager: Менеджер аутентификации для получения токенов
        client: HTTP клиент httpx
    
    Example:
        >>> client = KiroHttpClient(auth_manager)
        >>> response = await client.request_with_retry(
        ...     "POST",
        ...     "https://api.example.com/endpoint",
        ...     {"data": "value"},
        ...     stream=True
        ... )
    """
    
    def __init__(self, auth_manager: KiroAuthManager):
        """
        Инициализирует HTTP клиент.
        
        Args:
            auth_manager: Менеджер аутентификации
        """
        self.auth_manager = auth_manager
        self.client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self, timeout: float = 300, stream: bool = False) -> httpx.AsyncClient:
        """
        Возвращает или создаёт HTTP клиент.
        
        Args:
            timeout: Таймаут для запросов (секунды)
            stream: Если True, использует отдельный read timeout для streaming
        
        Returns:
            Активный HTTP клиент
        """
        if self.client is None or self.client.is_closed:
            if stream:
                # For streaming: use short connect timeout but long read timeout
                # This allows quick retry on connection issues while giving
                # the model plenty of time to generate responses between chunks
                timeout_config = httpx.Timeout(
                    connect=timeout,  # Connection timeout (FIRST_TOKEN_TIMEOUT)
                    read=STREAMING_READ_TIMEOUT,  # Read timeout for chunks (5 min default)
                    write=30.0,  # Write timeout
                    pool=30.0  # Pool timeout
                )
            else:
                timeout_config = timeout
            self.client = httpx.AsyncClient(timeout=timeout_config, follow_redirects=True)
        return self.client
    
    async def close(self) -> None:
        """Закрывает HTTP клиент."""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
    
    async def request_with_retry(
        self,
        method: str,
        url: str,
        json_data: dict,
        stream: bool = False,
        first_token_timeout: float = None
    ) -> httpx.Response:
        """
        Выполняет HTTP запрос с retry логикой.
        
        Автоматически обрабатывает различные типы ошибок:
        - 403: обновляет токен через auth_manager.force_refresh() и повторяет
        - 429: ждёт с exponential backoff (1s, 2s, 4s)
        - 5xx: ждёт с exponential backoff
        - Таймауты: ждёт с exponential backoff (для streaming - retry при first token timeout)
        
        Args:
            method: HTTP метод (GET, POST, etc.)
            url: URL запроса
            json_data: Тело запроса (JSON)
            stream: Использовать streaming (по умолчанию False)
            first_token_timeout: Таймаут ожидания первого ответа для streaming (секунды).
                                 Если None, используется FIRST_TOKEN_TIMEOUT из config.
        
        Returns:
            httpx.Response с успешным ответом
        
        Raises:
            HTTPException: При неудаче после всех попыток (502)
        """
        # Для streaming используем first_token_timeout, для обычных запросов - 300 секунд
        if stream:
            timeout = first_token_timeout if first_token_timeout is not None else FIRST_TOKEN_TIMEOUT
            max_retries = FIRST_TOKEN_MAX_RETRIES
        else:
            timeout = 300
            max_retries = MAX_RETRIES
        
        client = await self._get_client(timeout, stream=stream)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Получаем актуальный токен
                token = await self.auth_manager.get_access_token()
                headers = get_kiro_headers(self.auth_manager, token)
                
                if stream:
                    req = client.build_request(method, url, json=json_data, headers=headers)
                    response = await client.send(req, stream=True)
                else:
                    response = await client.request(method, url, json=json_data, headers=headers)
                
                # Проверяем статус
                if response.status_code == 200:
                    return response
                
                # 403 - токен истёк, обновляем и повторяем
                if response.status_code == 403:
                    logger.warning(f"Received 403, refreshing token (attempt {attempt + 1}/{MAX_RETRIES})")
                    await self.auth_manager.force_refresh()
                    continue
                
                # 429 - rate limit, ждём и повторяем
                if response.status_code == 429:
                    delay = BASE_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Received 429, waiting {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    await asyncio.sleep(delay)
                    continue
                
                # 5xx - серверная ошибка, ждём и повторяем
                if 500 <= response.status_code < 600:
                    delay = BASE_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Received {response.status_code}, waiting {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    await asyncio.sleep(delay)
                    continue
                
                # Другие ошибки - возвращаем как есть
                return response
                
            except httpx.TimeoutException as e:
                last_error = e
                if stream:
                    # Для streaming - это first token timeout, retry без задержки
                    logger.warning(f"First token timeout after {timeout}s (attempt {attempt + 1}/{max_retries})")
                else:
                    delay = BASE_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Timeout, waiting {delay}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                
            except httpx.RequestError as e:
                last_error = e
                delay = BASE_RETRY_DELAY * (2 ** attempt)
                logger.warning(f"Request error: {e}, waiting {delay}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
        
        # Все попытки исчерпаны
        if stream:
            raise HTTPException(
                status_code=504,
                detail=f"Model did not respond within {timeout}s after {max_retries} attempts. Please try again."
            )
        else:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to complete request after {max_retries} attempts: {last_error}"
            )
    
    async def __aenter__(self) -> "KiroHttpClient":
        """Поддержка async context manager."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Закрывает клиент при выходе из контекста."""
        await self.close()