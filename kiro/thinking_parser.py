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
Thinking block parser for streaming responses.

Implements a finite state machine (FSM) for reliable parsing of thinking blocks
(<thinking>, <think>, <reasoning>, etc.) that may be split across multiple
network chunks.

Key features:
- Tag detection ONLY at the start of response
- "Cautious" sending - buffers potential tag fragments to avoid splitting tags
- After closing tag - all content is treated as regular content
- Support for multiple tag formats
"""

from enum import IntEnum
from typing import Optional, List
from dataclasses import dataclass

from loguru import logger

from kiro.config import (
    FAKE_REASONING_HANDLING,
    FAKE_REASONING_OPEN_TAGS,
    FAKE_REASONING_INITIAL_BUFFER_SIZE,
)


class ParserState(IntEnum):
    """
    States of the thinking block parser FSM.

    PRE_CONTENT: Initial state, buffering to detect opening tag
    IN_THINKING: Inside thinking block, buffering until closing tag
    STREAMING: Regular streaming, no more thinking block detection
    """

    PRE_CONTENT = 0
    IN_THINKING = 1
    STREAMING = 2


@dataclass
class ThinkingParseResult:
    """
    Result of processing a content chunk through the parser.

    Attributes:
        thinking_content: Content to be sent as reasoning_content (or processed per mode)
        regular_content: Regular content to be sent as delta.content
        is_first_thinking_chunk: True if this is the first chunk of thinking content
        is_last_thinking_chunk: True if thinking block just closed
        state_changed: True if parser state changed during this feed
    """

    thinking_content: Optional[str] = None
    regular_content: Optional[str] = None
    is_first_thinking_chunk: bool = False
    is_last_thinking_chunk: bool = False
    state_changed: bool = False


class ThinkingParser:
    """
    Finite state machine parser for thinking blocks in streaming responses.

    The parser detects thinking tags ONLY at the start of the response.
    Once a thinking block is found and closed, all subsequent content
    is treated as regular content (even if it contains thinking tags).

    This implements "cautious" buffering to handle tags split across chunks:
    - In PRE_CONTENT: buffer until tag found or buffer exceeds limit
    - In IN_THINKING: buffer last MAX_TAG_LENGTH chars to avoid splitting closing tag

    Example:
        >>> parser = ThinkingParser()
        >>> result = parser.feed("<think")
        >>> result.thinking_content  # None - still buffering
        >>> result = parser.feed("ing>Hello")
        >>> result.thinking_content  # "Hello" (or None if buffering)
        >>> result = parser.feed("</thinking>World")
        >>> result.thinking_content  # remaining thinking content
        >>> result.regular_content  # "World"
    """

    def __init__(
        self,
        handling_mode: Optional[str] = None,
        open_tags: Optional[List[str]] = None,
        initial_buffer_size: int = FAKE_REASONING_INITIAL_BUFFER_SIZE,
    ):
        """
        Initialize the thinking parser.

        Args:
            handling_mode: How to handle thinking blocks. One of:
                - "as_reasoning_content": Extract to reasoning_content field
                - "remove": Remove thinking block completely
                - "pass": Pass through with original tags
                - "strip_tags": Remove tags but keep content
                If None, uses FAKE_REASONING_HANDLING from config.
            open_tags: List of opening tags to detect. If None, uses config.
            initial_buffer_size: Max chars to buffer while looking for opening tag.
        """
        self.handling_mode = handling_mode or FAKE_REASONING_HANDLING
        self.open_tags = open_tags or FAKE_REASONING_OPEN_TAGS
        self.initial_buffer_size = initial_buffer_size

        # Calculate max tag length for cautious buffering
        # We need to buffer enough to not split a closing tag
        self.max_tag_length = max(len(tag) for tag in self.open_tags) * 2

        # State
        self.state = ParserState.PRE_CONTENT
        self.initial_buffer = ""
        self.thinking_buffer = ""
        self.open_tag: Optional[str] = None
        self.close_tag: Optional[str] = None
        self.is_first_thinking_chunk = True
        self._thinking_block_found = False

    def feed(self, content: str) -> ThinkingParseResult:
        """
        Process a chunk of content through the parser.

        Args:
            content: New content from delta.content

        Returns:
            ThinkingParseResult with processed content
        """
        result = ThinkingParseResult()

        if not content:
            return result

        # Handle based on current state
        if self.state == ParserState.PRE_CONTENT:
            result = self._handle_pre_content(content)

        # If state changed to IN_THINKING, process remaining content
        if self.state == ParserState.IN_THINKING and result.state_changed:
            # Content after tag is already in thinking_buffer from _handle_pre_content
            pass
        elif self.state == ParserState.IN_THINKING and not result.state_changed:
            result = self._handle_in_thinking(content)

        # If state changed to STREAMING, regular_content is already set
        if self.state == ParserState.STREAMING and not result.state_changed:
            result.regular_content = content

        return result

    def _handle_pre_content(self, content: str) -> ThinkingParseResult:
        """
        Handle content in PRE_CONTENT state.

        Buffers content and looks for opening tag at the start.
        """
        result = ThinkingParseResult()
        self.initial_buffer += content

        # Strip leading whitespace for tag detection
        stripped = self.initial_buffer.lstrip()

        # Check if buffer starts with any of the opening tags
        for tag in self.open_tags:
            if stripped.startswith(tag):
                # Tag found! Transition to IN_THINKING
                self.state = ParserState.IN_THINKING
                self.open_tag = tag
                self.close_tag = f"</{tag[1:]}"  # <thinking> -> </thinking>
                self._thinking_block_found = True
                result.state_changed = True

                logger.debug(
                    f"Thinking tag '{tag}' detected. Transitioning to IN_THINKING."
                )

                # Content after the tag goes to thinking buffer
                content_after_tag = stripped[len(tag) :]
                self.thinking_buffer = content_after_tag
                self.initial_buffer = ""

                # Now process the thinking buffer for potential closing tag
                thinking_result = self._process_thinking_buffer()
                if thinking_result.thinking_content:
                    result.thinking_content = thinking_result.thinking_content
                    result.is_first_thinking_chunk = (
                        thinking_result.is_first_thinking_chunk
                    )
                if thinking_result.is_last_thinking_chunk:
                    result.is_last_thinking_chunk = True
                if thinking_result.regular_content:
                    result.regular_content = thinking_result.regular_content

                return result

        # Check if we might still be receiving the tag
        # (buffer is shorter than longest tag and could be a prefix)
        for tag in self.open_tags:
            if tag.startswith(stripped) and len(stripped) < len(tag):
                # Could still be receiving the tag, keep buffering
                return result

        # No tag found and buffer is either:
        # 1. Too long (exceeds initial_buffer_size)
        # 2. Doesn't match any tag prefix
        if len(
            self.initial_buffer
        ) > self.initial_buffer_size or not self._could_be_tag_prefix(stripped):
            # No thinking block, transition to STREAMING
            self.state = ParserState.STREAMING
            result.state_changed = True
            result.regular_content = self.initial_buffer
            self.initial_buffer = ""

            logger.debug("No thinking tag detected. Transitioning to STREAMING.")

        return result

    def _could_be_tag_prefix(self, text: str) -> bool:
        """Check if text could be the start of any opening tag."""
        if not text:
            return True  # Empty could be anything

        for tag in self.open_tags:
            if tag.startswith(text):
                return True
        return False

    def _handle_in_thinking(self, content: str) -> ThinkingParseResult:
        """
        Handle content in IN_THINKING state.

        Buffers content and looks for closing tag.
        Uses "cautious" sending to avoid splitting the closing tag.
        """
        self.thinking_buffer += content
        return self._process_thinking_buffer()

    def _process_thinking_buffer(self) -> ThinkingParseResult:
        """
        Process the thinking buffer, looking for closing tag.

        Implements "cautious" sending - keeps last max_tag_length chars
        in buffer to avoid splitting the closing tag across chunks.
        """
        result = ThinkingParseResult()

        if not self.close_tag:
            return result

        # Check for closing tag
        if self.close_tag in self.thinking_buffer:
            # Found closing tag!
            idx = self.thinking_buffer.find(self.close_tag)
            thinking_content = self.thinking_buffer[:idx]
            after_tag = self.thinking_buffer[idx + len(self.close_tag) :]

            # Send all thinking content
            if thinking_content:
                result.thinking_content = thinking_content
                result.is_first_thinking_chunk = self.is_first_thinking_chunk
                self.is_first_thinking_chunk = False

            result.is_last_thinking_chunk = True

            # Transition to STREAMING
            self.state = ParserState.STREAMING
            result.state_changed = True
            self.thinking_buffer = ""

            logger.debug(
                f"Closing tag '{self.close_tag}' found. Transitioning to STREAMING."
            )

            # Content after closing tag is regular content
            # Strip leading whitespace/newlines that often follow the closing tag
            if after_tag:
                stripped_after = after_tag.lstrip()
                if stripped_after:
                    result.regular_content = stripped_after

            return result

        # No closing tag yet - use "cautious" sending
        # Keep last max_tag_length chars in buffer to avoid splitting tag
        if len(self.thinking_buffer) > self.max_tag_length:
            send_part = self.thinking_buffer[: -self.max_tag_length]
            self.thinking_buffer = self.thinking_buffer[-self.max_tag_length :]

            result.thinking_content = send_part
            result.is_first_thinking_chunk = self.is_first_thinking_chunk
            self.is_first_thinking_chunk = False

        return result

    def finalize(self) -> ThinkingParseResult:
        """
        Finalize parsing when stream ends.

        Flushes any remaining buffered content.

        Returns:
            ThinkingParseResult with any remaining content
        """
        result = ThinkingParseResult()

        # Flush thinking buffer if we're still in thinking state
        if self.thinking_buffer:
            if self.state == ParserState.IN_THINKING:
                result.thinking_content = self.thinking_buffer
                result.is_first_thinking_chunk = self.is_first_thinking_chunk
                result.is_last_thinking_chunk = True
                logger.warning(
                    "Stream ended while still in thinking block. Flushing remaining content."
                )
            else:
                result.regular_content = self.thinking_buffer
            self.thinking_buffer = ""

        # Flush initial buffer if we never found a tag
        if self.initial_buffer:
            result.regular_content = (
                result.regular_content or ""
            ) + self.initial_buffer
            self.initial_buffer = ""

        return result

    def reset(self) -> None:
        """Reset parser to initial state."""
        self.state = ParserState.PRE_CONTENT
        self.initial_buffer = ""
        self.thinking_buffer = ""
        self.open_tag = None
        self.close_tag = None
        self.is_first_thinking_chunk = True
        self._thinking_block_found = False

    @property
    def found_thinking_block(self) -> bool:
        """Returns True if a thinking block was detected in this response."""
        return self._thinking_block_found

    def process_for_output(
        self,
        thinking_content: Optional[str],
        is_first: bool,
        is_last: bool,
    ) -> Optional[str]:
        """
        Process thinking content according to handling mode.

        Args:
            thinking_content: Raw thinking content
            is_first: True if this is the first thinking chunk
            is_last: True if this is the last thinking chunk

        Returns:
            Processed content string or None (for "remove" mode)
        """
        if not thinking_content:
            return None

        if self.handling_mode == "remove":
            return None

        if self.handling_mode == "pass":
            # Add tags back
            prefix = self.open_tag if is_first and self.open_tag else ""
            suffix = self.close_tag if is_last and self.close_tag else ""
            return f"{prefix}{thinking_content}{suffix}"

        if self.handling_mode == "strip_tags":
            # Return content without tags
            return thinking_content

        # "as_reasoning_content" - return as-is, caller will put in reasoning_content field
        return thinking_content
