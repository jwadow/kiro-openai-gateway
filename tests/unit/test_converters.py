# -*- coding: utf-8 -*-

"""
Unit tests for OpenAI <-> Kiro converters.
Tests message format conversion logic and payload building.
"""

import pytest

from unittest.mock import patch

from kiro_gateway.converters import (
    extract_text_content,
    merge_adjacent_messages,
    build_kiro_history,
    build_kiro_payload,
    process_tools_with_long_descriptions,
    inject_thinking_tags,
    _extract_tool_results,
    _extract_tool_uses,
    _build_user_input_context,
    _sanitize_json_schema
)
from kiro_gateway.models import ChatMessage, ChatCompletionRequest, Tool, ToolFunction


class TestExtractTextContent:
    """Tests for extract_text_content function."""
    
    def test_extracts_from_string(self):
        """
        What it does: Verifies text extraction from a string.
        Purpose: Ensure string is returned as-is.
        """
        print("Setup: Simple string...")
        content = "Hello, World!"
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected 'Hello, World!', Got '{result}'")
        assert result == "Hello, World!"
    
    def test_extracts_from_none(self):
        """
        What it does: Verifies None handling.
        Purpose: Ensure None returns empty string.
        """
        print("Setup: None...")
        
        print("Action: Extracting text...")
        result = extract_text_content(None)
        
        print(f"Comparing result: Expected '', Got '{result}'")
        assert result == ""
    
    def test_extracts_from_list_with_text_type(self):
        """
        What it does: Verifies extraction from list with type=text.
        Purpose: Ensure OpenAI multimodal format is handled.
        """
        print("Setup: List with type=text...")
        content = [
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": " World"}
        ]
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected 'Hello World', Got '{result}'")
        assert result == "Hello World"
    
    def test_extracts_from_list_with_text_key(self):
        """
        What it does: Verifies extraction from list with text key.
        Purpose: Ensure alternative format is handled.
        """
        print("Setup: List with text key...")
        content = [{"text": "Hello"}, {"text": " World"}]
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected 'Hello World', Got '{result}'")
        assert result == "Hello World"
    
    def test_extracts_from_list_with_strings(self):
        """
        What it does: Verifies extraction from list of strings.
        Purpose: Ensure string list is concatenated.
        """
        print("Setup: List of strings...")
        content = ["Hello", " ", "World"]
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected 'Hello World', Got '{result}'")
        assert result == "Hello World"
    
    def test_extracts_from_mixed_list(self):
        """
        What it does: Verifies extraction from mixed list.
        Purpose: Ensure different formats in one list are handled.
        """
        print("Setup: Mixed list...")
        content = [
            {"type": "text", "text": "Part1"},
            "Part2",
            {"text": "Part3"}
        ]
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected 'Part1Part2Part3', Got '{result}'")
        assert result == "Part1Part2Part3"
    
    def test_converts_other_types_to_string(self):
        """
        What it does: Verifies conversion of other types to string.
        Purpose: Ensure numbers and other types are converted.
        """
        print("Setup: Number...")
        content = 42
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected '42', Got '{result}'")
        assert result == "42"
    
    def test_handles_empty_list(self):
        """
        What it does: Verifies empty list handling.
        Purpose: Ensure empty list returns empty string.
        """
        print("Setup: Empty list...")
        content = []
        
        print("Action: Extracting text...")
        result = extract_text_content(content)
        
        print(f"Comparing result: Expected '', Got '{result}'")
        assert result == ""


class TestMergeAdjacentMessages:
    """Tests for merge_adjacent_messages function."""
    
    def test_merges_adjacent_user_messages(self):
        """
        What it does: Verifies merging of adjacent user messages.
        Purpose: Ensure messages with the same role are merged.
        """
        print("Setup: Two consecutive user messages...")
        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="user", content="World")
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Comparing length: Expected 1, Got {len(result)}")
        assert len(result) == 1
        assert "Hello" in result[0].content
        assert "World" in result[0].content
    
    def test_preserves_alternating_messages(self):
        """
        What it does: Verifies preservation of alternating messages.
        Purpose: Ensure different roles are not merged.
        """
        print("Setup: Alternating messages...")
        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi"),
            ChatMessage(role="user", content="How are you?")
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Comparing length: Expected 3, Got {len(result)}")
        assert len(result) == 3
    
    def test_handles_empty_list(self):
        """
        What it does: Verifies empty list handling.
        Purpose: Ensure empty list doesn't cause errors.
        """
        print("Setup: Empty list...")
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages([])
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []
    
    def test_handles_single_message(self):
        """
        What it does: Verifies single message handling.
        Purpose: Ensure single message is returned as-is.
        """
        print("Setup: Single message...")
        messages = [ChatMessage(role="user", content="Hello")]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Comparing length: Expected 1, Got {len(result)}")
        assert len(result) == 1
        assert result[0].content == "Hello"
    
    def test_merges_multiple_adjacent_groups(self):
        """
        What it does: Verifies merging of multiple groups.
        Purpose: Ensure multiple groups of adjacent messages are merged.
        """
        print("Setup: Multiple groups of adjacent messages...")
        messages = [
            ChatMessage(role="user", content="A"),
            ChatMessage(role="user", content="B"),
            ChatMessage(role="assistant", content="C"),
            ChatMessage(role="assistant", content="D"),
            ChatMessage(role="user", content="E")
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Comparing length: Expected 3, Got {len(result)}")
        assert len(result) == 3
        assert result[0].role == "user"
        assert result[1].role == "assistant"
        assert result[2].role == "user"
    
    def test_converts_tool_message_to_user_with_tool_result(self):
        """
        What it does: Verifies conversion of tool message to user message with tool_result.
        Purpose: Ensure role="tool" is converted to user message with tool_results content.
        """
        print("Setup: Tool message...")
        messages = [
            ChatMessage(role="tool", content="Tool result text", tool_call_id="call_123")
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        print(f"Comparing length: Expected 1, Got {len(result)}")
        assert len(result) == 1
        assert result[0].role == "user"
        
        print("Checking content contains tool_result...")
        assert isinstance(result[0].content, list)
        assert len(result[0].content) == 1
        assert result[0].content[0]["type"] == "tool_result"
        assert result[0].content[0]["tool_use_id"] == "call_123"
        assert result[0].content[0]["content"] == "Tool result text"
    
    def test_converts_multiple_tool_messages_to_single_user_message(self):
        """
        What it does: Verifies merging of multiple tool messages into single user message.
        Purpose: Ensure multiple tool results are merged into one user message.
        """
        print("Setup: Multiple consecutive tool messages...")
        messages = [
            ChatMessage(role="tool", content="Result 1", tool_call_id="call_1"),
            ChatMessage(role="tool", content="Result 2", tool_call_id="call_2"),
            ChatMessage(role="tool", content="Result 3", tool_call_id="call_3")
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        print(f"Comparing length: Expected 1, Got {len(result)}")
        assert len(result) == 1
        assert result[0].role == "user"
        
        print("Checking content contains all tool_results...")
        assert isinstance(result[0].content, list)
        assert len(result[0].content) == 3
        
        tool_use_ids = [item["tool_use_id"] for item in result[0].content]
        assert "call_1" in tool_use_ids
        assert "call_2" in tool_use_ids
        assert "call_3" in tool_use_ids
    
    def test_tool_message_followed_by_user_message(self):
        """
        What it does: Verifies tool message before user message.
        Purpose: Ensure tool results and user message are merged.
        """
        print("Setup: Tool message + user message...")
        messages = [
            ChatMessage(role="tool", content="Tool result", tool_call_id="call_1"),
            ChatMessage(role="user", content="Continue please")
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        print(f"Comparing length: Expected 1, Got {len(result)}")
        # Tool message is converted to user, then merged with user
        assert len(result) == 1
        assert result[0].role == "user"
    
    def test_assistant_tool_user_sequence(self):
        """
        What it does: Verifies assistant -> tool -> user sequence.
        Purpose: Ensure tool message is correctly inserted between assistant and user.
        """
        print("Setup: assistant -> tool -> user...")
        messages = [
            ChatMessage(role="assistant", content="I'll call a tool"),
            ChatMessage(role="tool", content="Tool output", tool_call_id="call_abc"),
            ChatMessage(role="user", content="Thanks!")
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        # assistant stays, tool+user are merged into one user
        assert len(result) == 2
        assert result[0].role == "assistant"
        assert result[1].role == "user"
    
    def test_tool_message_with_empty_content(self):
        """
        What it does: Verifies tool message with empty content.
        Purpose: Ensure empty result is replaced with "(empty result)".
        """
        print("Setup: Tool message with empty content...")
        messages = [
            ChatMessage(role="tool", content="", tool_call_id="call_empty")
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert result[0].content[0]["content"] == "(empty result)"
    
    def test_tool_message_with_none_tool_call_id(self):
        """
        What it does: Verifies tool message without tool_call_id.
        Purpose: Ensure missing tool_call_id is replaced with empty string.
        """
        print("Setup: Tool message without tool_call_id...")
        messages = [
            ChatMessage(role="tool", content="Result", tool_call_id=None)
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert result[0].content[0]["tool_use_id"] == ""
    
    def test_merges_list_contents_correctly(self):
        """
        What it does: Verifies merging of list contents.
        Purpose: Ensure lists are merged correctly.
        """
        print("Setup: Two user messages with list content...")
        messages = [
            ChatMessage(role="user", content=[{"type": "text", "text": "Part 1"}]),
            ChatMessage(role="user", content=[{"type": "text", "text": "Part 2"}])
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert isinstance(result[0].content, list)
        assert len(result[0].content) == 2
    
    def test_merges_adjacent_assistant_tool_calls(self):
        """
        What it does: Verifies merging of tool_calls when merging adjacent assistant messages.
        Purpose: Ensure tool_calls from all assistant messages are preserved when merging.
        
        This is a critical test for a bug where Codex CLI sends multiple assistant
        messages in a row, each with its own tool_call. Without this fix, the second
        tool_call was lost, causing a 400 error from Kiro API (toolResult without toolUse).
        """
        print("Setup: Two assistant messages with different tool_calls...")
        messages = [
            ChatMessage(
                role="assistant",
                content=None,
                tool_calls=[{
                    "id": "tooluse_first",
                    "type": "function",
                    "function": {
                        "name": "shell",
                        "arguments": '{"command": ["ls", "-la"]}'
                    }
                }]
            ),
            ChatMessage(
                role="assistant",
                content=None,
                tool_calls=[{
                    "id": "tooluse_second",
                    "type": "function",
                    "function": {
                        "name": "shell",
                        "arguments": '{"command": ["pwd"]}'
                    }
                }]
            )
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        print(f"Comparing length: Expected 1, Got {len(result)}")
        assert len(result) == 1
        assert result[0].role == "assistant"
        
        print("Checking that both tool_calls are preserved...")
        assert result[0].tool_calls is not None
        print(f"Comparing tool_calls count: Expected 2, Got {len(result[0].tool_calls)}")
        assert len(result[0].tool_calls) == 2
        
        tool_ids = [tc["id"] for tc in result[0].tool_calls]
        print(f"Tool IDs: {tool_ids}")
        assert "tooluse_first" in tool_ids
        assert "tooluse_second" in tool_ids
    
    def test_merges_three_adjacent_assistant_tool_calls(self):
        """
        What it does: Verifies merging of tool_calls from three assistant messages.
        Purpose: Ensure all tool_calls are preserved when merging more than two messages.
        """
        print("Setup: Three assistant messages with tool_calls...")
        messages = [
            ChatMessage(
                role="assistant",
                content="",
                tool_calls=[{"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}]
            ),
            ChatMessage(
                role="assistant",
                content="",
                tool_calls=[{"id": "call_2", "type": "function", "function": {"name": "tool2", "arguments": "{}"}}]
            ),
            ChatMessage(
                role="assistant",
                content="",
                tool_calls=[{"id": "call_3", "type": "function", "function": {"name": "tool3", "arguments": "{}"}}]
            )
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert len(result[0].tool_calls) == 3
        
        tool_ids = [tc["id"] for tc in result[0].tool_calls]
        print(f"Comparing tool IDs: Expected ['call_1', 'call_2', 'call_3'], Got {tool_ids}")
        assert tool_ids == ["call_1", "call_2", "call_3"]
    
    def test_merges_assistant_with_and_without_tool_calls(self):
        """
        What it does: Verifies merging of assistant with and without tool_calls.
        Purpose: Ensure tool_calls are correctly initialized when merging.
        """
        print("Setup: Assistant without tool_calls + assistant with tool_calls...")
        messages = [
            ChatMessage(role="assistant", content="Thinking...", tool_calls=None),
            ChatMessage(
                role="assistant",
                content="",
                tool_calls=[{"id": "call_1", "type": "function", "function": {"name": "tool1", "arguments": "{}"}}]
            )
        ]
        
        print("Action: Merging messages...")
        result = merge_adjacent_messages(messages)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert result[0].tool_calls is not None
        print(f"Comparing tool_calls count: Expected 1, Got {len(result[0].tool_calls)}")
        assert len(result[0].tool_calls) == 1
        assert result[0].tool_calls[0]["id"] == "call_1"


class TestBuildKiroHistory:
    """Tests for build_kiro_history function."""
    
    def test_builds_user_message(self):
        """
        What it does: Verifies building of user message.
        Purpose: Ensure user message is converted to userInputMessage.
        """
        print("Setup: User message...")
        messages = [ChatMessage(role="user", content="Hello")]
        
        print("Action: Building history...")
        result = build_kiro_history(messages, "claude-sonnet-4")
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert "userInputMessage" in result[0]
        assert result[0]["userInputMessage"]["content"] == "Hello"
        assert result[0]["userInputMessage"]["modelId"] == "claude-sonnet-4"
    
    def test_builds_assistant_message(self):
        """
        What it does: Verifies building of assistant message.
        Purpose: Ensure assistant message is converted to assistantResponseMessage.
        """
        print("Setup: Assistant message...")
        messages = [ChatMessage(role="assistant", content="Hi there")]
        
        print("Action: Building history...")
        result = build_kiro_history(messages, "claude-sonnet-4")
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert "assistantResponseMessage" in result[0]
        assert result[0]["assistantResponseMessage"]["content"] == "Hi there"
    
    def test_ignores_system_messages(self):
        """
        What it does: Verifies ignoring of system messages.
        Purpose: Ensure system messages are not added to history.
        """
        print("Setup: System message...")
        messages = [ChatMessage(role="system", content="You are helpful")]
        
        print("Action: Building history...")
        result = build_kiro_history(messages, "claude-sonnet-4")
        
        print(f"Comparing length: Expected 0, Got {len(result)}")
        assert len(result) == 0
    
    def test_builds_conversation_history(self):
        """
        What it does: Verifies building of full conversation history.
        Purpose: Ensure user/assistant alternation is preserved.
        """
        print("Setup: Full conversation history...")
        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi"),
            ChatMessage(role="user", content="How are you?")
        ]
        
        print("Action: Building history...")
        result = build_kiro_history(messages, "claude-sonnet-4")
        
        print(f"Result: {result}")
        assert len(result) == 3
        assert "userInputMessage" in result[0]
        assert "assistantResponseMessage" in result[1]
        assert "userInputMessage" in result[2]
    
    def test_handles_empty_list(self):
        """
        What it does: Verifies empty list handling.
        Purpose: Ensure empty list returns empty history.
        """
        print("Setup: Empty list...")
        
        print("Action: Building history...")
        result = build_kiro_history([], "claude-sonnet-4")
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []


class TestExtractToolResults:
    """Tests for _extract_tool_results function."""
    
    def test_extracts_tool_results_from_list(self):
        """
        What it does: Verifies extraction of tool results from list.
        Purpose: Ensure tool_result elements are extracted.
        """
        print("Setup: List with tool_result...")
        content = [
            {"type": "tool_result", "tool_use_id": "call_123", "content": "Result text"}
        ]
        
        print("Action: Extracting tool results...")
        result = _extract_tool_results(content)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert result[0]["toolUseId"] == "call_123"
        assert result[0]["status"] == "success"
    
    def test_returns_empty_for_string_content(self):
        """
        What it does: Verifies empty list return for string.
        Purpose: Ensure string doesn't contain tool results.
        """
        print("Setup: String...")
        content = "Just a string"
        
        print("Action: Extracting tool results...")
        result = _extract_tool_results(content)
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []
    
    def test_returns_empty_for_list_without_tool_results(self):
        """
        What it does: Verifies empty list return without tool_result.
        Purpose: Ensure regular elements are not extracted.
        """
        print("Setup: List without tool_result...")
        content = [{"type": "text", "text": "Hello"}]
        
        print("Action: Extracting tool results...")
        result = _extract_tool_results(content)
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []


class TestExtractToolUses:
    """Tests for _extract_tool_uses function."""
    
    def test_extracts_from_tool_calls_field(self):
        """
        What it does: Verifies extraction from tool_calls field.
        Purpose: Ensure OpenAI tool_calls format is handled.
        """
        print("Setup: Message with tool_calls...")
        msg = ChatMessage(
            role="assistant",
            content="",
            tool_calls=[{
                "id": "call_123",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"location": "Moscow"}'
                }
            }]
        )
        
        print("Action: Extracting tool uses...")
        result = _extract_tool_uses(msg)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert result[0]["name"] == "get_weather"
        assert result[0]["toolUseId"] == "call_123"
    
    def test_extracts_from_content_list(self):
        """
        What it does: Verifies extraction from content list.
        Purpose: Ensure tool_use in content is handled.
        """
        print("Setup: Message with tool_use in content...")
        msg = ChatMessage(
            role="assistant",
            content=[{
                "type": "tool_use",
                "id": "call_456",
                "name": "search",
                "input": {"query": "test"}
            }]
        )
        
        print("Action: Extracting tool uses...")
        result = _extract_tool_uses(msg)
        
        print(f"Result: {result}")
        assert len(result) == 1
        assert result[0]["name"] == "search"
        assert result[0]["toolUseId"] == "call_456"
    
    def test_returns_empty_for_no_tool_uses(self):
        """
        What it does: Verifies empty list return without tool uses.
        Purpose: Ensure regular message doesn't contain tool uses.
        """
        print("Setup: Regular message...")
        msg = ChatMessage(role="assistant", content="Hello")
        
        print("Action: Extracting tool uses...")
        result = _extract_tool_uses(msg)
        
        print(f"Comparing result: Expected [], Got {result}")
        assert result == []


class TestProcessToolsWithLongDescriptions:
    """Tests for process_tools_with_long_descriptions function."""
    
    def test_returns_none_and_empty_string_for_none_tools(self):
        """
        What it does: Verifies handling of None instead of tools list.
        Purpose: Ensure None returns (None, "").
        """
        print("Setup: None instead of tools...")
        
        print("Action: Processing tools...")
        processed, doc = process_tools_with_long_descriptions(None)
        
        print(f"Comparing result: Expected (None, ''), Got ({processed}, '{doc}')")
        assert processed is None
        assert doc == ""
    
    def test_returns_none_and_empty_string_for_empty_list(self):
        """
        What it does: Verifies handling of empty tools list.
        Purpose: Ensure empty list returns (None, "").
        """
        print("Setup: Empty tools list...")
        
        print("Action: Processing tools...")
        processed, doc = process_tools_with_long_descriptions([])
        
        print(f"Comparing result: Expected (None, ''), Got ({processed}, '{doc}')")
        assert processed is None
        assert doc == ""
    
    def test_short_description_unchanged(self):
        """
        What it does: Verifies short descriptions are unchanged.
        Purpose: Ensure tools with short descriptions remain as-is.
        """
        print("Setup: Tool with short description...")
        tools = [Tool(
            type="function",
            function=ToolFunction(
                name="get_weather",
                description="Get weather for a location",
                parameters={"type": "object", "properties": {}}
            )
        )]
        
        print("Action: Processing tools...")
        with patch('kiro_gateway.converters.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print(f"Comparing description: Expected 'Get weather for a location', Got '{processed[0].function.description}'")
        assert len(processed) == 1
        assert processed[0].function.description == "Get weather for a location"
        assert doc == ""
    
    def test_long_description_moved_to_system_prompt(self):
        """
        What it does: Verifies moving long description to system prompt.
        Purpose: Ensure long descriptions are moved correctly.
        """
        print("Setup: Tool with very long description...")
        long_description = "A" * 15000  # 15000 chars - exceeds limit
        tools = [Tool(
            type="function",
            function=ToolFunction(
                name="bash",
                description=long_description,
                parameters={"type": "object", "properties": {"command": {"type": "string"}}}
            )
        )]
        
        print("Action: Processing tools with limit 10000...")
        with patch('kiro_gateway.converters.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print(f"Checking reference in description...")
        assert len(processed) == 1
        assert "[Full documentation in system prompt under '## Tool: bash']" in processed[0].function.description
        
        print(f"Checking documentation in system prompt...")
        assert "## Tool: bash" in doc
        assert long_description in doc
        assert "# Tool Documentation" in doc
    
    def test_mixed_short_and_long_descriptions(self):
        """
        What it does: Verifies handling of mixed tools list.
        Purpose: Ensure short ones stay, long ones are moved.
        """
        print("Setup: Two tools - short and long...")
        short_desc = "Short description"
        long_desc = "B" * 15000
        tools = [
            Tool(
                type="function",
                function=ToolFunction(
                    name="short_tool",
                    description=short_desc,
                    parameters={}
                )
            ),
            Tool(
                type="function",
                function=ToolFunction(
                    name="long_tool",
                    description=long_desc,
                    parameters={}
                )
            )
        ]
        
        print("Action: Processing tools...")
        with patch('kiro_gateway.converters.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print(f"Checking tools count: Expected 2, Got {len(processed)}")
        assert len(processed) == 2
        
        print(f"Checking short tool...")
        assert processed[0].function.description == short_desc
        
        print(f"Checking long tool...")
        assert "[Full documentation in system prompt" in processed[1].function.description
        assert "## Tool: long_tool" in doc
        assert long_desc in doc
    
    def test_preserves_tool_parameters(self):
        """
        What it does: Verifies parameters preservation when moving description.
        Purpose: Ensure parameters are not lost.
        """
        print("Setup: Tool with parameters and long description...")
        params = {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
        tools = [Tool(
            type="function",
            function=ToolFunction(
                name="weather",
                description="C" * 15000,
                parameters=params
            )
        )]
        
        print("Action: Processing tools...")
        with patch('kiro_gateway.converters.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print(f"Checking parameters preservation...")
        assert processed[0].function.parameters == params
    
    def test_disabled_when_limit_is_zero(self):
        """
        What it does: Verifies function is disabled when limit is 0.
        Purpose: Ensure tools are unchanged when TOOL_DESCRIPTION_MAX_LENGTH=0.
        """
        print("Setup: Tool with long description and limit 0...")
        long_desc = "D" * 15000
        tools = [Tool(
            type="function",
            function=ToolFunction(
                name="test_tool",
                description=long_desc,
                parameters={}
            )
        )]
        
        print("Action: Processing tools with limit 0...")
        with patch('kiro_gateway.converters.TOOL_DESCRIPTION_MAX_LENGTH', 0):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print(f"Checking that description is unchanged...")
        assert processed[0].function.description == long_desc
        assert doc == ""
    
    def test_non_function_tools_unchanged(self):
        """
        What it does: Verifies non-function tools are unchanged.
        Purpose: Ensure only function tools are processed.
        """
        print("Setup: Tool with type != function...")
        # Create tool with different type (though OpenAI only supports function)
        tools = [Tool(
            type="other_type",
            function=ToolFunction(
                name="test",
                description="E" * 15000,
                parameters={}
            )
        )]
        
        print("Action: Processing tools...")
        with patch('kiro_gateway.converters.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print(f"Checking that tool is unchanged...")
        assert len(processed) == 1
        assert processed[0].type == "other_type"
        assert doc == ""
    
    def test_multiple_long_descriptions_all_moved(self):
        """
        What it does: Verifies moving of multiple long descriptions.
        Purpose: Ensure all long descriptions are moved.
        """
        print("Setup: Three tools with long descriptions...")
        tools = [
            Tool(type="function", function=ToolFunction(name="tool1", description="F" * 15000, parameters={})),
            Tool(type="function", function=ToolFunction(name="tool2", description="G" * 15000, parameters={})),
            Tool(type="function", function=ToolFunction(name="tool3", description="H" * 15000, parameters={}))
        ]
        
        print("Action: Processing tools...")
        with patch('kiro_gateway.converters.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print(f"Checking all three tools...")
        assert len(processed) == 3
        for i, tool in enumerate(processed):
            assert "[Full documentation in system prompt" in tool.function.description
        
        print(f"Checking documentation contains all three sections...")
        assert "## Tool: tool1" in doc
        assert "## Tool: tool2" in doc
        assert "## Tool: tool3" in doc
    
    def test_empty_description_unchanged(self):
        """
        What it does: Verifies handling of empty description.
        Purpose: Ensure empty description doesn't cause errors.
        """
        print("Setup: Tool with empty description...")
        tools = [Tool(
            type="function",
            function=ToolFunction(
                name="empty_desc_tool",
                description="",
                parameters={}
            )
        )]
        
        print("Action: Processing tools...")
        with patch('kiro_gateway.converters.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print(f"Checking that empty description remains empty...")
        assert processed[0].function.description == ""
        assert doc == ""
    
    def test_none_description_unchanged(self):
        """
        What it does: Verifies handling of None description.
        Purpose: Ensure None description doesn't cause errors.
        """
        print("Setup: Tool with None description...")
        tools = [Tool(
            type="function",
            function=ToolFunction(
                name="none_desc_tool",
                description=None,
                parameters={}
            )
        )]
        
        print("Action: Processing tools...")
        with patch('kiro_gateway.converters.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            processed, doc = process_tools_with_long_descriptions(tools)
        
        print(f"Checking that None description is handled correctly...")
        # None should remain None or become empty string
        assert processed[0].function.description is None or processed[0].function.description == ""
        assert doc == ""


class TestSanitizeJsonSchema:
    """
    Tests for _sanitize_json_schema function.
    
    This function cleans JSON Schema from fields that Kiro API doesn't accept:
    - Empty required arrays []
    - additionalProperties
    """
    
    def test_returns_empty_dict_for_none(self):
        """
        What it does: Verifies handling of None.
        Purpose: Ensure None returns empty dict.
        """
        print("Setup: None schema...")
        
        print("Action: Sanitizing schema...")
        result = _sanitize_json_schema(None)
        
        print(f"Comparing result: Expected {{}}, Got {result}")
        assert result == {}
    
    def test_returns_empty_dict_for_empty_dict(self):
        """
        What it does: Verifies handling of empty dict.
        Purpose: Ensure empty dict is returned as-is.
        """
        print("Setup: Empty dict...")
        
        print("Action: Sanitizing schema...")
        result = _sanitize_json_schema({})
        
        print(f"Comparing result: Expected {{}}, Got {result}")
        assert result == {}
    
    def test_removes_empty_required_array(self):
        """
        What it does: Verifies removal of empty required array.
        Purpose: Ensure required: [] is removed from schema.
        
        This is a critical test for a Cline bug where tools with required: []
        caused a 400 "Improperly formed request" error from Kiro API.
        """
        print("Setup: Schema with empty required...")
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        print("Action: Sanitizing schema...")
        result = _sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking that required is removed...")
        assert "required" not in result
        assert result["type"] == "object"
        assert result["properties"] == {}
    
    def test_preserves_non_empty_required_array(self):
        """
        What it does: Verifies preservation of non-empty required array.
        Purpose: Ensure required with elements is preserved.
        """
        print("Setup: Schema with non-empty required...")
        schema = {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
        
        print("Action: Sanitizing schema...")
        result = _sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking that required is preserved...")
        assert "required" in result
        assert result["required"] == ["location"]
    
    def test_removes_additional_properties(self):
        """
        What it does: Verifies removal of additionalProperties.
        Purpose: Ensure additionalProperties is removed from schema.
        
        Kiro API doesn't support additionalProperties in JSON Schema.
        """
        print("Setup: Schema with additionalProperties...")
        schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
        
        print("Action: Sanitizing schema...")
        result = _sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking that additionalProperties is removed...")
        assert "additionalProperties" not in result
        assert result["type"] == "object"
    
    def test_removes_both_empty_required_and_additional_properties(self):
        """
        What it does: Verifies removal of both problematic fields.
        Purpose: Ensure both fields are removed simultaneously.
        
        This is a real scenario from Cline where tools had both fields.
        """
        print("Setup: Schema with both problematic fields...")
        schema = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        }
        
        print("Action: Sanitizing schema...")
        result = _sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking that both fields are removed...")
        assert "required" not in result
        assert "additionalProperties" not in result
        assert result == {"type": "object", "properties": {}}
    
    def test_recursively_sanitizes_nested_properties(self):
        """
        What it does: Verifies recursive sanitization of nested properties.
        Purpose: Ensure nested schemas are also sanitized.
        """
        print("Setup: Schema with nested properties...")
        schema = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                }
            }
        }
        
        print("Action: Sanitizing schema...")
        result = _sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking nested object...")
        nested = result["properties"]["nested"]
        assert "required" not in nested
        assert "additionalProperties" not in nested
    
    def test_recursively_sanitizes_dict_values(self):
        """
        What it does: Verifies recursive sanitization of dict values.
        Purpose: Ensure any nested dicts are sanitized.
        """
        print("Setup: Schema with nested dict...")
        schema = {
            "type": "object",
            "items": {
                "type": "string",
                "additionalProperties": True
            }
        }
        
        print("Action: Sanitizing schema...")
        result = _sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking nested items...")
        assert "additionalProperties" not in result["items"]
        assert result["items"]["type"] == "string"
    
    def test_sanitizes_items_in_lists(self):
        """
        What it does: Verifies sanitization of items in lists (anyOf, oneOf).
        Purpose: Ensure list elements are also sanitized.
        """
        print("Setup: Schema with anyOf...")
        schema = {
            "anyOf": [
                {"type": "string", "additionalProperties": False},
                {"type": "number", "required": []}
            ]
        }
        
        print("Action: Sanitizing schema...")
        result = _sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking anyOf elements...")
        assert "additionalProperties" not in result["anyOf"][0]
        assert "required" not in result["anyOf"][1]
    
    def test_preserves_non_dict_list_items(self):
        """
        What it does: Verifies preservation of non-dict list items.
        Purpose: Ensure strings and other types in lists are preserved.
        """
        print("Setup: Schema with enum...")
        schema = {
            "type": "string",
            "enum": ["value1", "value2", "value3"]
        }
        
        print("Action: Sanitizing schema...")
        result = _sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking enum is preserved...")
        assert result["enum"] == ["value1", "value2", "value3"]
    
    def test_complex_real_world_schema(self):
        """
        What it does: Verifies sanitization of real complex schema from Cline.
        Purpose: Ensure real schemas are handled correctly.
        """
        print("Setup: Real schema from Cline...")
        schema = {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask"
                },
                "options": {
                    "type": "string",
                    "description": "Array of options"
                }
            },
            "required": ["question", "options"],
            "additionalProperties": False
        }
        
        print("Action: Sanitizing schema...")
        result = _sanitize_json_schema(schema)
        
        print(f"Result: {result}")
        print("Checking result...")
        assert "additionalProperties" not in result
        assert result["required"] == ["question", "options"]  # Non-empty required is preserved
        assert result["properties"]["question"]["type"] == "string"


class TestBuildUserInputContext:
    """Tests for _build_user_input_context function."""
    
    def test_builds_tools_context(self):
        """
        What it does: Verifies building of context with tools.
        Purpose: Ensure tools are converted to toolSpecification.
        """
        print("Setup: Request with tools...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4",
            messages=[ChatMessage(role="user", content="Hello")],
            tools=[Tool(
                type="function",
                function=ToolFunction(
                    name="get_weather",
                    description="Get weather",
                    parameters={"type": "object", "properties": {}}
                )
            )]
        )
        current_msg = ChatMessage(role="user", content="Hello")
        
        print("Action: Building context...")
        result = _build_user_input_context(request, current_msg)
        
        print(f"Result: {result}")
        assert "tools" in result
        assert len(result["tools"]) == 1
        assert result["tools"][0]["toolSpecification"]["name"] == "get_weather"
    
    def test_returns_empty_for_no_tools(self):
        """
        What it does: Verifies return of empty context without tools.
        Purpose: Ensure request without tools returns empty context.
        """
        print("Setup: Request without tools...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4",
            messages=[ChatMessage(role="user", content="Hello")]
        )
        current_msg = ChatMessage(role="user", content="Hello")
        
        print("Action: Building context...")
        result = _build_user_input_context(request, current_msg)
        
        print(f"Comparing result: Expected {{}}, Got {result}")
        assert result == {}
    
    def test_empty_description_replaced_with_placeholder(self):
        """
        What it does: Verifies replacement of empty description with placeholder.
        Purpose: Ensure empty description is replaced with "Tool: {name}".
        
        This is a critical test for a Cline bug where tool focus_chain had
        empty description "", which caused a 400 error from Kiro API.
        """
        print("Setup: Tool with empty description...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4",
            messages=[ChatMessage(role="user", content="Hello")],
            tools=[Tool(
                type="function",
                function=ToolFunction(
                    name="focus_chain",
                    description="",
                    parameters={"type": "object", "properties": {}}
                )
            )]
        )
        current_msg = ChatMessage(role="user", content="Hello")
        
        print("Action: Building context...")
        result = _build_user_input_context(request, current_msg)
        
        print(f"Result: {result}")
        print("Checking that description is replaced with placeholder...")
        tool_spec = result["tools"][0]["toolSpecification"]
        assert tool_spec["description"] == "Tool: focus_chain"
    
    def test_whitespace_only_description_replaced_with_placeholder(self):
        """
        What it does: Verifies replacement of whitespace-only description with placeholder.
        Purpose: Ensure description with only whitespace is replaced.
        """
        print("Setup: Tool with whitespace-only description...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4",
            messages=[ChatMessage(role="user", content="Hello")],
            tools=[Tool(
                type="function",
                function=ToolFunction(
                    name="whitespace_tool",
                    description="   ",
                    parameters={}
                )
            )]
        )
        current_msg = ChatMessage(role="user", content="Hello")
        
        print("Action: Building context...")
        result = _build_user_input_context(request, current_msg)
        
        print(f"Result: {result}")
        print("Checking that description is replaced with placeholder...")
        tool_spec = result["tools"][0]["toolSpecification"]
        assert tool_spec["description"] == "Tool: whitespace_tool"
    
    def test_none_description_replaced_with_placeholder(self):
        """
        What it does: Verifies replacement of None description with placeholder.
        Purpose: Ensure None description is replaced with "Tool: {name}".
        """
        print("Setup: Tool with None description...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4",
            messages=[ChatMessage(role="user", content="Hello")],
            tools=[Tool(
                type="function",
                function=ToolFunction(
                    name="none_desc_tool",
                    description=None,
                    parameters={}
                )
            )]
        )
        current_msg = ChatMessage(role="user", content="Hello")
        
        print("Action: Building context...")
        result = _build_user_input_context(request, current_msg)
        
        print(f"Result: {result}")
        print("Checking that description is replaced with placeholder...")
        tool_spec = result["tools"][0]["toolSpecification"]
        assert tool_spec["description"] == "Tool: none_desc_tool"
    
    def test_non_empty_description_preserved(self):
        """
        What it does: Verifies preservation of non-empty description.
        Purpose: Ensure normal description is not changed.
        """
        print("Setup: Tool with normal description...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4",
            messages=[ChatMessage(role="user", content="Hello")],
            tools=[Tool(
                type="function",
                function=ToolFunction(
                    name="get_weather",
                    description="Get weather for a location",
                    parameters={}
                )
            )]
        )
        current_msg = ChatMessage(role="user", content="Hello")
        
        print("Action: Building context...")
        result = _build_user_input_context(request, current_msg)
        
        print(f"Result: {result}")
        print("Checking that description is preserved...")
        tool_spec = result["tools"][0]["toolSpecification"]
        assert tool_spec["description"] == "Get weather for a location"
    
    def test_sanitizes_tool_parameters(self):
        """
        What it does: Verifies sanitization of parameters from problematic fields.
        Purpose: Ensure _sanitize_json_schema is applied to parameters.
        """
        print("Setup: Tool with problematic parameters...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4",
            messages=[ChatMessage(role="user", content="Hello")],
            tools=[Tool(
                type="function",
                function=ToolFunction(
                    name="test_tool",
                    description="Test tool",
                    parameters={
                        "type": "object",
                        "properties": {},
                        "required": [],
                        "additionalProperties": False
                    }
                )
            )]
        )
        current_msg = ChatMessage(role="user", content="Hello")
        
        print("Action: Building context...")
        result = _build_user_input_context(request, current_msg)
        
        print(f"Result: {result}")
        print("Checking that parameters are sanitized...")
        input_schema = result["tools"][0]["toolSpecification"]["inputSchema"]["json"]
        assert "required" not in input_schema
        assert "additionalProperties" not in input_schema
    
    def test_mixed_tools_with_empty_and_normal_descriptions(self):
        """
        What it does: Verifies handling of mixed tools list.
        Purpose: Ensure empty descriptions are replaced while normal ones are preserved.
        
        This is a real scenario from Cline where most tools have
        normal descriptions, but focus_chain has an empty one.
        """
        print("Setup: Mixed list of tools...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4",
            messages=[ChatMessage(role="user", content="Hello")],
            tools=[
                Tool(
                    type="function",
                    function=ToolFunction(
                        name="read_file",
                        description="Read contents of a file",
                        parameters={}
                    )
                ),
                Tool(
                    type="function",
                    function=ToolFunction(
                        name="focus_chain",
                        description="",
                        parameters={}
                    )
                ),
                Tool(
                    type="function",
                    function=ToolFunction(
                        name="write_file",
                        description="Write content to a file",
                        parameters={}
                    )
                )
            ]
        )
        current_msg = ChatMessage(role="user", content="Hello")
        
        print("Action: Building context...")
        result = _build_user_input_context(request, current_msg)
        
        print(f"Result: {result}")
        print("Checking descriptions...")
        tools = result["tools"]
        assert tools[0]["toolSpecification"]["description"] == "Read contents of a file"
        assert tools[1]["toolSpecification"]["description"] == "Tool: focus_chain"
        assert tools[2]["toolSpecification"]["description"] == "Write content to a file"


class TestInjectThinkingTags:
    """
    Tests for inject_thinking_tags function.
    
    This function injects thinking mode tags into content when FAKE_REASONING_ENABLED is True.
    The tags instruct the model to include its reasoning process in the response.
    """
    
    def test_returns_original_content_when_disabled(self):
        """
        What it does: Verifies that content is returned unchanged when fake reasoning is disabled.
        Purpose: Ensure no modification occurs when FAKE_REASONING_ENABLED=False.
        """
        print("Setup: Content with fake reasoning disabled...")
        content = "Hello, world!"
        
        print("Action: Inject thinking tags with FAKE_REASONING_ENABLED=False...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', False):
            result = inject_thinking_tags(content)
        
        print(f"Comparing result: Expected 'Hello, world!', Got '{result}'")
        assert result == "Hello, world!"
    
    def test_injects_tags_when_enabled(self):
        """
        What it does: Verifies that thinking tags are injected when enabled.
        Purpose: Ensure tags are prepended to content when FAKE_REASONING_ENABLED=True.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "What is 2+2?"
        
        print("Action: Inject thinking tags with FAKE_REASONING_ENABLED=True...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print(f"Result: {result[:200]}...")
        print("Checking that thinking_mode tag is present...")
        assert "<thinking_mode>enabled</thinking_mode>" in result
        
        print("Checking that max_thinking_length tag is present...")
        assert "<max_thinking_length>4000</max_thinking_length>" in result
        
        print("Checking that original content is preserved at the end...")
        assert result.endswith("What is 2+2?")
    
    def test_injects_thinking_instruction_tag(self):
        """
        What it does: Verifies that thinking_instruction tag is injected.
        Purpose: Ensure the quality improvement prompt is included.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Analyze this code"
        
        print("Action: Inject thinking tags...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 8000):
                result = inject_thinking_tags(content)
        
        print(f"Result length: {len(result)} chars")
        print("Checking that thinking_instruction tag is present...")
        assert "<thinking_instruction>" in result
        assert "</thinking_instruction>" in result
    
    def test_thinking_instruction_contains_english_directive(self):
        """
        What it does: Verifies that thinking instruction includes English language directive.
        Purpose: Ensure model is instructed to think in English for better reasoning quality.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Test"
        
        print("Action: Inject thinking tags...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking for English directive...")
        assert "Think in English" in result
    
    def test_thinking_instruction_contains_systematic_approach(self):
        """
        What it does: Verifies that thinking instruction includes systematic approach guidance.
        Purpose: Ensure model is instructed to think systematically.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Test"
        
        print("Action: Inject thinking tags...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking for systematic approach keywords...")
        assert "thorough" in result.lower() or "systematic" in result.lower()
    
    def test_thinking_instruction_contains_understanding_step(self):
        """
        What it does: Verifies that thinking instruction includes understanding step.
        Purpose: Ensure model is instructed to understand the problem first.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Test"
        
        print("Action: Inject thinking tags...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking for understanding step...")
        assert "understand" in result.lower()
    
    def test_thinking_instruction_contains_alternatives_consideration(self):
        """
        What it does: Verifies that thinking instruction includes alternatives consideration.
        Purpose: Ensure model is instructed to consider multiple approaches.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Test"
        
        print("Action: Inject thinking tags...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking for alternatives consideration...")
        assert "multiple" in result.lower() or "alternative" in result.lower() or "approaches" in result.lower()
    
    def test_thinking_instruction_contains_edge_cases(self):
        """
        What it does: Verifies that thinking instruction includes edge cases consideration.
        Purpose: Ensure model is instructed to think about edge cases and potential issues.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Test"
        
        print("Action: Inject thinking tags...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking for edge cases consideration...")
        assert "edge case" in result.lower() or "what could go wrong" in result.lower()
    
    def test_thinking_instruction_contains_verification_step(self):
        """
        What it does: Verifies that thinking instruction includes verification step.
        Purpose: Ensure model is instructed to verify reasoning before concluding.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Test"
        
        print("Action: Inject thinking tags...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking for verification step...")
        assert "verify" in result.lower()
    
    def test_thinking_instruction_contains_assumptions_challenge(self):
        """
        What it does: Verifies that thinking instruction includes assumptions challenge.
        Purpose: Ensure model is instructed to challenge initial assumptions.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Test"
        
        print("Action: Inject thinking tags...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking for assumptions challenge...")
        assert "assumption" in result.lower() or "challenge" in result.lower()
    
    def test_thinking_instruction_contains_quality_over_speed(self):
        """
        What it does: Verifies that thinking instruction emphasizes quality over speed.
        Purpose: Ensure model is instructed to prioritize quality of thought.
        """
        print("Setup: Content with fake reasoning enabled...")
        content = "Test"
        
        print("Action: Inject thinking tags...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking for quality over speed emphasis...")
        assert "quality" in result.lower()
    
    def test_uses_configured_max_tokens(self):
        """
        What it does: Verifies that FAKE_REASONING_MAX_TOKENS config value is used.
        Purpose: Ensure the configured max tokens value is injected into the tag.
        """
        print("Setup: Content with custom max tokens...")
        content = "Test"
        
        print("Action: Inject thinking tags with FAKE_REASONING_MAX_TOKENS=16000...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 16000):
                result = inject_thinking_tags(content)
        
        print(f"Result: {result[:300]}...")
        print("Checking that max_thinking_length uses configured value...")
        assert "<max_thinking_length>16000</max_thinking_length>" in result
    
    def test_preserves_empty_content(self):
        """
        What it does: Verifies that empty content is handled correctly.
        Purpose: Ensure empty string doesn't cause issues.
        """
        print("Setup: Empty content with fake reasoning enabled...")
        content = ""
        
        print("Action: Inject thinking tags...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print(f"Result length: {len(result)} chars")
        print("Checking that tags are present even with empty content...")
        assert "<thinking_mode>enabled</thinking_mode>" in result
        assert "<thinking_instruction>" in result
    
    def test_preserves_multiline_content(self):
        """
        What it does: Verifies that multiline content is preserved correctly.
        Purpose: Ensure newlines in original content are not corrupted.
        """
        print("Setup: Multiline content...")
        content = "Line 1\nLine 2\nLine 3"
        
        print("Action: Inject thinking tags...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking that multiline content is preserved...")
        assert "Line 1\nLine 2\nLine 3" in result
    
    def test_preserves_special_characters(self):
        """
        What it does: Verifies that special characters in content are preserved.
        Purpose: Ensure XML-like content in user message doesn't break injection.
        """
        print("Setup: Content with special characters...")
        content = "Check this <code>example</code> and {json: 'value'}"
        
        print("Action: Inject thinking tags...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking that special characters are preserved...")
        assert "<code>example</code>" in result
        assert "{json: 'value'}" in result
    
    def test_tag_order_is_correct(self):
        """
        What it does: Verifies that tags are in the correct order.
        Purpose: Ensure thinking_mode comes first, then max_thinking_length, then instruction, then content.
        """
        print("Setup: Content...")
        content = "USER_CONTENT_HERE"
        
        print("Action: Inject thinking tags...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = inject_thinking_tags(content)
        
        print("Checking tag order...")
        thinking_mode_pos = result.find("<thinking_mode>")
        max_length_pos = result.find("<max_thinking_length>")
        instruction_pos = result.find("<thinking_instruction>")
        content_pos = result.find("USER_CONTENT_HERE")
        
        print(f"Positions: thinking_mode={thinking_mode_pos}, max_length={max_length_pos}, instruction={instruction_pos}, content={content_pos}")
        
        assert thinking_mode_pos < max_length_pos, "thinking_mode should come before max_thinking_length"
        assert max_length_pos < instruction_pos, "max_thinking_length should come before thinking_instruction"
        assert instruction_pos < content_pos, "thinking_instruction should come before user content"


class TestBuildKiroPayloadToolCallsIntegration:
    """
    Integration tests for build_kiro_payload with tool_calls.
    Tests full flow from OpenAI format to Kiro format.
    """
    
    def test_multiple_assistant_tool_calls_with_results(self):
        """
        What it does: Verifies full scenario with multiple assistant tool_calls and their results.
        Purpose: Ensure all toolUses and toolResults are correctly linked in Kiro payload.
        
        This is an integration test for a Codex CLI bug where multiple assistant
        messages with tool_calls were sent in a row, followed by tool results. Without
        the fix, the second toolUse was lost, causing a 400 error from Kiro API.
        """
        print("Setup: Full scenario with two tool_calls and their results...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4-5",
            messages=[
                ChatMessage(role="user", content="Run two commands"),
                # First assistant with tool_call
                ChatMessage(
                    role="assistant",
                    content=None,
                    tool_calls=[{
                        "id": "tooluse_first",
                        "type": "function",
                        "function": {
                            "name": "shell",
                            "arguments": '{"command": ["ls"]}'
                        }
                    }]
                ),
                # Second assistant with tool_call (consecutive!)
                ChatMessage(
                    role="assistant",
                    content=None,
                    tool_calls=[{
                        "id": "tooluse_second",
                        "type": "function",
                        "function": {
                            "name": "shell",
                            "arguments": '{"command": ["pwd"]}'
                        }
                    }]
                ),
                # Results of both tool_calls
                ChatMessage(role="tool", content="file1.txt\nfile2.txt", tool_call_id="tooluse_first"),
                ChatMessage(role="tool", content="/home/user", tool_call_id="tooluse_second")
            ]
        )
        
        print("Action: Building Kiro payload...")
        result = build_kiro_payload(request, "conv-123", "arn:aws:test")
        
        print(f"Result: {result}")
        
        # Check history
        history = result["conversationState"].get("history", [])
        print(f"History: {history}")
        
        # Should have userInputMessage and assistantResponseMessage in history
        assert len(history) >= 2, f"Expected at least 2 elements in history, got {len(history)}"
        
        # Find assistantResponseMessage
        assistant_msgs = [h for h in history if "assistantResponseMessage" in h]
        print(f"Assistant messages in history: {assistant_msgs}")
        assert len(assistant_msgs) >= 1, "Should have at least one assistantResponseMessage"
        
        # Check that assistantResponseMessage has both toolUses
        assistant_msg = assistant_msgs[0]["assistantResponseMessage"]
        tool_uses = assistant_msg.get("toolUses", [])
        print(f"ToolUses in assistant: {tool_uses}")
        print(f"Comparing toolUses count: Expected 2, Got {len(tool_uses)}")
        assert len(tool_uses) == 2, f"Should have 2 toolUses, got {len(tool_uses)}"
        
        tool_use_ids = [tu["toolUseId"] for tu in tool_uses]
        print(f"ToolUse IDs: {tool_use_ids}")
        assert "tooluse_first" in tool_use_ids
        assert "tooluse_second" in tool_use_ids
        
        # Check currentMessage contains toolResults
        current_msg = result["conversationState"]["currentMessage"]["userInputMessage"]
        context = current_msg.get("userInputMessageContext", {})
        tool_results = context.get("toolResults", [])
        print(f"ToolResults in currentMessage: {tool_results}")
        print(f"Comparing toolResults count: Expected 2, Got {len(tool_results)}")
        assert len(tool_results) == 2, f"Should have 2 toolResults, got {len(tool_results)}"
        
        tool_result_ids = [tr["toolUseId"] for tr in tool_results]
        print(f"ToolResult IDs: {tool_result_ids}")
        assert "tooluse_first" in tool_result_ids
        assert "tooluse_second" in tool_result_ids


class TestBuildKiroPayload:
    """Tests for build_kiro_payload function."""
    
    def test_builds_simple_payload(self):
        """
        What it does: Verifies building of simple payload.
        Purpose: Ensure basic request is converted correctly.
        """
        print("Setup: Simple request...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4-5",
            messages=[ChatMessage(role="user", content="Hello")]
        )
        
        print("Action: Building payload...")
        result = build_kiro_payload(request, "conv-123", "arn:aws:test")
        
        print(f"Result: {result}")
        assert "conversationState" in result
        assert result["conversationState"]["conversationId"] == "conv-123"
        assert "currentMessage" in result["conversationState"]
        assert result["profileArn"] == "arn:aws:test"
    
    def test_includes_system_prompt_in_first_message(self):
        """
        What it does: Verifies adding system prompt to first message.
        Purpose: Ensure system prompt is merged with user message.
        """
        print("Setup: Request with system prompt...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4-5",
            messages=[
                ChatMessage(role="system", content="You are helpful"),
                ChatMessage(role="user", content="Hello")
            ]
        )
        
        print("Action: Building payload...")
        result = build_kiro_payload(request, "conv-123", "")
        
        print(f"Result: {result}")
        current_content = result["conversationState"]["currentMessage"]["userInputMessage"]["content"]
        assert "You are helpful" in current_content
        assert "Hello" in current_content
    
    def test_builds_history_for_multi_turn(self):
        """
        What it does: Verifies building history for multi-turn.
        Purpose: Ensure previous messages go into history.
        """
        print("Setup: Multi-turn request...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4-5",
            messages=[
                ChatMessage(role="user", content="Hello"),
                ChatMessage(role="assistant", content="Hi"),
                ChatMessage(role="user", content="How are you?")
            ]
        )
        
        print("Action: Building payload...")
        result = build_kiro_payload(request, "conv-123", "")
        
        print(f"Result: {result}")
        assert "history" in result["conversationState"]
        assert len(result["conversationState"]["history"]) == 2
    
    def test_handles_assistant_as_last_message(self):
        """
        What it does: Verifies handling of assistant as last message.
        Purpose: Ensure "Continue" message is created.
        """
        print("Setup: Request with assistant at the end...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4-5",
            messages=[
                ChatMessage(role="user", content="Hello"),
                ChatMessage(role="assistant", content="Hi there")
            ]
        )
        
        print("Action: Building payload...")
        result = build_kiro_payload(request, "conv-123", "")
        
        print(f"Result: {result}")
        current_content = result["conversationState"]["currentMessage"]["userInputMessage"]["content"]
        assert current_content == "Continue"
    
    def test_raises_for_empty_messages(self):
        """
        What it does: Verifies exception raising for empty messages.
        Purpose: Ensure empty request raises ValueError.
        """
        print("Setup: Request with only system message...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4-5",
            messages=[ChatMessage(role="system", content="You are helpful")]
        )
        
        print("Action: Attempting to build payload...")
        with pytest.raises(ValueError) as exc_info:
            build_kiro_payload(request, "conv-123", "")
        
        print(f"Exception: {exc_info.value}")
        assert "No messages to send" in str(exc_info.value)
    
    def test_uses_continue_for_empty_content(self):
        """
        What it does: Verifies using "Continue" for empty content.
        Purpose: Ensure empty message is replaced with "Continue".
        
        Note: We mock FAKE_REASONING_ENABLED=False so the test doesn't depend
        on environment configuration (if fake reasoning is enabled in .env).
        """
        print("Setup: Request with empty content...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4-5",
            messages=[ChatMessage(role="user", content="")]
        )

        print("Action: Building payload (with fake reasoning disabled)...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', False):
            result = build_kiro_payload(request, "conv-123", "")

        print(f"Result: {result}")
        current_content = result["conversationState"]["currentMessage"]["userInputMessage"]["content"]
        assert current_content == "Continue"
    
    def test_maps_model_id_correctly(self):
        """
        What it does: Verifies mapping of external model ID to internal.
        Purpose: Ensure MODEL_MAPPING is applied.
        """
        print("Setup: Request with external model ID...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4-5",
            messages=[ChatMessage(role="user", content="Hello")]
        )
        
        print("Action: Building payload...")
        result = build_kiro_payload(request, "conv-123", "")
        
        print(f"Result: {result}")
        model_id = result["conversationState"]["currentMessage"]["userInputMessage"]["modelId"]
        # claude-sonnet-4-5 should map to CLAUDE_SONNET_4_5_20250929_V1_0
        assert model_id == "CLAUDE_SONNET_4_5_20250929_V1_0"
    
    def test_long_tool_description_added_to_system_prompt(self):
        """
        What it does: Verifies integration of long tool descriptions into payload.
        Purpose: Ensure long descriptions are added to system prompt in payload.
        """
        print("Setup: Request with tool with long description...")
        long_desc = "X" * 15000
        request = ChatCompletionRequest(
            model="claude-sonnet-4-5",
            messages=[
                ChatMessage(role="system", content="You are helpful"),
                ChatMessage(role="user", content="Hello")
            ],
            tools=[Tool(
                type="function",
                function=ToolFunction(
                    name="long_tool",
                    description=long_desc,
                    parameters={}
                )
            )]
        )
        
        print("Action: Building payload...")
        with patch('kiro_gateway.converters.TOOL_DESCRIPTION_MAX_LENGTH', 10000):
            result = build_kiro_payload(request, "conv-123", "")
        
        print(f"Checking that system prompt contains tool documentation...")
        current_content = result["conversationState"]["currentMessage"]["userInputMessage"]["content"]
        assert "You are helpful" in current_content
        assert "## Tool: long_tool" in current_content
        assert long_desc in current_content
        
        print(f"Checking that tool in context has reference description...")
        tools_context = result["conversationState"]["currentMessage"]["userInputMessage"]["userInputMessageContext"]["tools"]
        assert "[Full documentation in system prompt" in tools_context[0]["toolSpecification"]["description"]
    
    def test_skips_thinking_tags_when_tool_results_present(self):
        """
        What it does: Verifies thinking tags are NOT injected when toolResults are present.
        Purpose: Fix GitHub issue #20 - OpenCode compaction returns 400 error.
        
        When the last message contains tool results:
        - Kiro API rejects requests with thinking tags + toolResults combination
        - This causes "Improperly formed request" 400 error
        - Fix: skip thinking tag injection when toolResults are in current message
        """
        print("Setup: Request where last message is a tool result...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4-5",
            messages=[
                ChatMessage(role="user", content="Run a command"),
                ChatMessage(
                    role="assistant",
                    content="I'll run the command",
                    tool_calls=[{
                        "id": "tool_1",
                        "type": "function",
                        "function": {"name": "bash", "arguments": "{}"}
                    }]
                ),
                ChatMessage(role="tool", content="Command output here", tool_call_id="tool_1"),
            ]
        )
        
        print("Action: Building payload with FAKE_REASONING_ENABLED=True...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = build_kiro_payload(request, "conv-123", "")
        
        current_msg = result["conversationState"]["currentMessage"]["userInputMessage"]
        content = current_msg["content"]
        context = current_msg.get("userInputMessageContext", {})
        
        print(f"Content: {repr(content[:100] if len(content) > 100 else content)}")
        print(f"Has toolResults: {'toolResults' in context}")
        
        assert "toolResults" in context, "toolResults should be present"
        assert "<thinking_mode>" not in content, "thinking tags should NOT be injected when toolResults present"
        assert content == "Continue", "Content should be 'Continue' (no thinking tags)"
    
    def test_injects_thinking_tags_when_no_tool_results(self):
        """
        What it does: Verifies thinking tags ARE injected for normal user messages.
        Purpose: Ensure fix for issue #20 doesn't break normal thinking tag injection.
        """
        print("Setup: Normal user message without tool results...")
        request = ChatCompletionRequest(
            model="claude-sonnet-4-5",
            messages=[ChatMessage(role="user", content="Hello")]
        )
        
        print("Action: Building payload with FAKE_REASONING_ENABLED=True...")
        with patch('kiro_gateway.converters.FAKE_REASONING_ENABLED', True):
            with patch('kiro_gateway.converters.FAKE_REASONING_MAX_TOKENS', 4000):
                result = build_kiro_payload(request, "conv-123", "")
        
        current_msg = result["conversationState"]["currentMessage"]["userInputMessage"]
        content = current_msg["content"]
        context = current_msg.get("userInputMessageContext", {})
        
        print(f"Content starts with thinking tags: {'<thinking_mode>' in content}")
        print(f"Has toolResults: {'toolResults' in context}")
        
        assert "toolResults" not in context, "toolResults should NOT be present"
        assert "<thinking_mode>" in content, "thinking tags SHOULD be injected for normal messages"
        assert "Hello" in content, "Original content should be preserved"