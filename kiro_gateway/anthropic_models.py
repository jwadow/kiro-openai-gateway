# -*- coding: utf-8 -*-

# Kiro OpenAI Gateway
# https://github.com/jwadow/kiro-openai-gateway
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

"""Pydantic models for an Anthropic (Claude) compatible API surface."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class AnthropicTool(BaseModel):
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class AnthropicToolChoice(BaseModel):
    type: str
    name: Optional[str] = None

    model_config = {"extra": "allow"}


class AnthropicThinkingParam(BaseModel):
    type: str
    budget_tokens: Optional[int] = None

    model_config = {"extra": "allow"}


class AnthropicMessageParam(BaseModel):
    role: str
    content: Optional[Union[str, List[Any], Any]] = None

    model_config = {"extra": "allow"}


class AnthropicCreateMessageRequest(BaseModel):
    model: str
    max_tokens: int
    messages: List[AnthropicMessageParam] = Field(min_length=1)

    stream: bool = False
    system: Optional[Union[str, List[Any], Any]] = None

    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stop_sequences: Optional[List[str]] = None

    tools: Optional[List[AnthropicTool]] = None
    tool_choice: Optional[Union[str, Dict[str, Any], AnthropicToolChoice]] = None

    thinking: Optional[Union[Dict[str, Any], AnthropicThinkingParam]] = None

    model_config = {"extra": "allow"}


class AnthropicCountTokensRequest(BaseModel):
    model: str
    messages: List[AnthropicMessageParam] = Field(min_length=1)

    system: Optional[Union[str, List[Any], Any]] = None
    tools: Optional[List[AnthropicTool]] = None

    model_config = {"extra": "allow"}


class AnthropicMessageBatchRequestItem(BaseModel):
    custom_id: str
    params: Dict[str, Any]

    model_config = {"extra": "allow"}


class AnthropicCreateMessageBatchRequest(BaseModel):
    requests: List[AnthropicMessageBatchRequestItem] = Field(min_length=1)

    model_config = {"extra": "allow"}
