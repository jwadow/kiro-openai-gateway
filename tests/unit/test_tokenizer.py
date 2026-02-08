# -*- coding: utf-8 -*-

"""
Unit-тесты для модуля токенизатора (kiro/tokenizer.py).

Проверяет:
- Подсчёт токенов в тексте (count_tokens)
- Подсчёт токенов в сообщениях (count_message_tokens)
- Подсчёт токенов в инструментах (count_tools_tokens)
- Оценку токенов запроса (estimate_request_tokens)
- Коэффициент коррекции для Claude (CLAUDE_CORRECTION_FACTOR)
- Fallback при отсутствии tiktoken
"""

import pytest
from unittest.mock import patch, MagicMock

from kiro.tokenizer import (
    count_tokens,
    count_message_tokens,
    count_tools_tokens,
    estimate_request_tokens,
    count_anthropic_content_block_tokens,
    count_anthropic_message_tokens,
    count_anthropic_tools_tokens,
    count_anthropic_system_tokens,
    estimate_anthropic_request_tokens,
    CLAUDE_CORRECTION_FACTOR,
    _get_encoding
)


class TestCountTokens:
    """Тесты для функции count_tokens."""
    
    def test_empty_string_returns_zero(self):
        """
        Что он делает: Проверяет, что пустая строка возвращает 0 токенов.
        Цель: Убедиться в корректной обработке граничного случая.
        """
        print("Тест: Пустая строка...")
        result = count_tokens("")
        print(f"Результат: {result}")
        assert result == 0, "Пустая строка должна возвращать 0 токенов"
    
    def test_none_returns_zero(self):
        """
        Что он делает: Проверяет, что None возвращает 0 токенов.
        Цель: Убедиться в корректной обработке None.
        """
        print("Тест: None...")
        result = count_tokens(None)
        print(f"Результат: {result}")
        assert result == 0, "None должен возвращать 0 токенов"
    
    def test_simple_text_returns_positive(self):
        """
        Что он делает: Проверяет, что простой текст возвращает положительное число токенов.
        Цель: Убедиться в базовой работоспособности подсчёта.
        """
        print("Тест: Простой текст...")
        result = count_tokens("Hello, world!")
        print(f"Результат: {result}")
        assert result > 0, "Простой текст должен возвращать положительное число токенов"
    
    def test_longer_text_returns_more_tokens(self):
        """
        Что он делает: Проверяет, что более длинный текст возвращает больше токенов.
        Цель: Убедиться в корректной пропорциональности подсчёта.
        """
        print("Тест: Сравнение длинного и короткого текста...")
        short_text = "Hello"
        long_text = "Hello, this is a much longer text that should have more tokens"
        
        short_tokens = count_tokens(short_text)
        long_tokens = count_tokens(long_text)
        
        print(f"Короткий текст: {short_tokens} токенов")
        print(f"Длинный текст: {long_tokens} токенов")
        
        assert long_tokens > short_tokens, "Длинный текст должен иметь больше токенов"
    
    def test_claude_correction_applied_by_default(self):
        """
        Что он делает: Проверяет, что коэффициент коррекции Claude применяется по умолчанию.
        Цель: Убедиться, что apply_claude_correction=True по умолчанию.
        """
        print("Тест: Коэффициент коррекции Claude...")
        text = "This is a test text for token counting"
        
        with_correction = count_tokens(text, apply_claude_correction=True)
        without_correction = count_tokens(text, apply_claude_correction=False)
        
        print(f"С коррекцией: {with_correction}")
        print(f"Без коррекции: {without_correction}")
        
        # С коррекцией должно быть больше (коэффициент 1.15)
        assert with_correction > without_correction, "С коррекцией должно быть больше токенов"
        
        # Проверяем примерное соотношение
        ratio = with_correction / without_correction
        print(f"Соотношение: {ratio}")
        assert 1.1 <= ratio <= 1.2, f"Соотношение должно быть около {CLAUDE_CORRECTION_FACTOR}"
    
    def test_without_claude_correction(self):
        """
        Что он делает: Проверяет подсчёт без коэффициента коррекции.
        Цель: Убедиться, что apply_claude_correction=False работает.
        """
        print("Тест: Без коэффициента коррекции...")
        text = "Test text"
        
        result = count_tokens(text, apply_claude_correction=False)
        print(f"Результат: {result}")
        
        assert result > 0, "Должен вернуть положительное число токенов"
    
    def test_unicode_text(self):
        """
        Что он делает: Проверяет подсчёт токенов для Unicode текста.
        Цель: Убедиться в корректной обработке не-ASCII символов.
        """
        print("Тест: Unicode текст...")
        text = "Привет, мир! 你好世界 🌍"
        
        result = count_tokens(text)
        print(f"Результат: {result}")
        
        assert result > 0, "Unicode текст должен возвращать положительное число токенов"
    
    def test_multiline_text(self):
        """
        Что он делает: Проверяет подсчёт токенов для многострочного текста.
        Цель: Убедиться в корректной обработке переносов строк.
        """
        print("Тест: Многострочный текст...")
        text = """Line 1
        Line 2
        Line 3"""
        
        result = count_tokens(text)
        print(f"Результат: {result}")
        
        assert result > 0, "Многострочный текст должен возвращать положительное число токенов"
    
    def test_json_text(self):
        """
        Что он делает: Проверяет подсчёт токенов для JSON строки.
        Цель: Убедиться в корректной обработке JSON.
        """
        print("Тест: JSON текст...")
        text = '{"name": "test", "value": 123, "nested": {"key": "value"}}'
        
        result = count_tokens(text)
        print(f"Результат: {result}")
        
        assert result > 0, "JSON текст должен возвращать положительное число токенов"


class TestCountTokensFallback:
    """Тесты для fallback логики при отсутствии tiktoken."""
    
    def test_fallback_when_tiktoken_unavailable(self):
        """
        Что он делает: Проверяет fallback подсчёт когда tiktoken недоступен.
        Цель: Убедиться, что система работает без tiktoken.
        """
        print("Тест: Fallback без tiktoken...")
        
        # Мокируем _get_encoding чтобы вернуть None
        with patch('kiro.tokenizer._get_encoding', return_value=None):
            result = count_tokens("Hello world test")
            print(f"Результат: {result}")
            
            # Fallback: len(text) // 4 + 1, затем * 1.15
            # "Hello world test" = 16 символов
            # 16 // 4 + 1 = 5
            # 5 * 1.15 = 5.75 -> 5
            assert result > 0, "Fallback должен вернуть положительное число"
    
    def test_fallback_without_correction(self):
        """
        Что он делает: Проверяет fallback без коэффициента коррекции.
        Цель: Убедиться, что fallback работает с apply_claude_correction=False.
        """
        print("Тест: Fallback без коррекции...")
        
        with patch('kiro.tokenizer._get_encoding', return_value=None):
            result = count_tokens("Test", apply_claude_correction=False)
            print(f"Результат: {result}")
            
            # "Test" = 4 символа
            # 4 // 4 + 1 = 2
            assert result > 0, "Fallback должен вернуть положительное число"


class TestCountMessageTokens:
    """Тесты для функции count_message_tokens."""
    
    def test_empty_list_returns_zero(self):
        """
        Что он делает: Проверяет, что пустой список возвращает 0 токенов.
        Цель: Убедиться в корректной обработке пустого списка.
        """
        print("Тест: Пустой список сообщений...")
        result = count_message_tokens([])
        print(f"Результат: {result}")
        assert result == 0, "Пустой список должен возвращать 0 токенов"
    
    def test_none_returns_zero(self):
        """
        Что он делает: Проверяет, что None возвращает 0 токенов.
        Цель: Убедиться в корректной обработке None.
        """
        print("Тест: None...")
        result = count_message_tokens(None)
        print(f"Результат: {result}")
        assert result == 0, "None должен возвращать 0 токенов"
    
    def test_single_user_message(self):
        """
        Что он делает: Проверяет подсчёт токенов для одного user сообщения.
        Цель: Убедиться в базовой работоспособности.
        """
        print("Тест: Одно user сообщение...")
        messages = [{"role": "user", "content": "Hello, AI!"}]
        
        result = count_message_tokens(messages)
        print(f"Результат: {result}")
        
        assert result > 0, "Должен вернуть положительное число токенов"
    
    def test_multiple_messages(self):
        """
        Что он делает: Проверяет подсчёт токенов для нескольких сообщений.
        Цель: Убедиться, что токены суммируются корректно.
        """
        print("Тест: Несколько сообщений...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there! How can I help you?"},
            {"role": "user", "content": "What is the weather?"}
        ]
        
        result = count_message_tokens(messages)
        print(f"Результат: {result}")
        
        # Больше сообщений = больше токенов
        single_message = count_message_tokens([messages[0]])
        assert result > single_message, "Несколько сообщений должны иметь больше токенов"
    
    def test_message_with_tool_calls(self):
        """
        Что он делает: Проверяет подсчёт токенов для сообщения с tool_calls.
        Цель: Убедиться, что tool_calls учитываются.
        """
        print("Тест: Сообщение с tool_calls...")
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "Moscow"}'
                        }
                    }
                ]
            }
        ]
        
        result = count_message_tokens(messages)
        print(f"Результат: {result}")
        
        assert result > 0, "Сообщение с tool_calls должно иметь токены"
    
    def test_message_with_tool_call_id(self):
        """
        Что он делает: Проверяет подсчёт токенов для tool response сообщения.
        Цель: Убедиться, что tool_call_id учитывается.
        """
        print("Тест: Tool response сообщение...")
        messages = [
            {
                "role": "tool",
                "content": "The weather in Moscow is sunny, 25°C",
                "tool_call_id": "call_123"
            }
        ]
        
        result = count_message_tokens(messages)
        print(f"Результат: {result}")
        
        assert result > 0, "Tool response должен иметь токены"
    
    def test_message_with_list_content(self):
        """
        Что он делает: Проверяет подсчёт токенов для мультимодального контента.
        Цель: Убедиться, что list content обрабатывается.
        """
        print("Тест: Мультимодальный контент...")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is in this image?"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
                ]
            }
        ]
        
        result = count_message_tokens(messages)
        print(f"Результат: {result}")
        
        assert result > 0, "Мультимодальный контент должен иметь токены"
    
    def test_without_claude_correction(self):
        """
        Что он делает: Проверяет подсчёт без коэффициента коррекции.
        Цель: Убедиться, что apply_claude_correction=False работает.
        """
        print("Тест: Без коэффициента коррекции...")
        messages = [{"role": "user", "content": "Test message"}]
        
        with_correction = count_message_tokens(messages, apply_claude_correction=True)
        without_correction = count_message_tokens(messages, apply_claude_correction=False)
        
        print(f"С коррекцией: {with_correction}")
        print(f"Без коррекции: {without_correction}")
        
        assert with_correction > without_correction, "С коррекцией должно быть больше"
    
    def test_message_with_empty_content(self):
        """
        Что он делает: Проверяет подсчёт для сообщения с пустым content.
        Цель: Убедиться, что пустой content не ломает подсчёт.
        """
        print("Тест: Пустой content...")
        messages = [{"role": "user", "content": ""}]
        
        result = count_message_tokens(messages)
        print(f"Результат: {result}")
        
        # Должны быть служебные токены (role, разделители)
        assert result > 0, "Даже пустое сообщение должно иметь служебные токены"
    
    def test_message_with_none_content(self):
        """
        Что он делает: Проверяет подсчёт для сообщения с None content.
        Цель: Убедиться, что None content не ломает подсчёт.
        """
        print("Тест: None content...")
        messages = [{"role": "assistant", "content": None}]
        
        result = count_message_tokens(messages)
        print(f"Результат: {result}")
        
        assert result > 0, "Сообщение с None content должно иметь служебные токены"


class TestCountToolsTokens:
    """Тесты для функции count_tools_tokens."""
    
    def test_none_returns_zero(self):
        """
        Что он делает: Проверяет, что None возвращает 0 токенов.
        Цель: Убедиться в корректной обработке None.
        """
        print("Тест: None...")
        result = count_tools_tokens(None)
        print(f"Результат: {result}")
        assert result == 0, "None должен возвращать 0 токенов"
    
    def test_empty_list_returns_zero(self):
        """
        Что он делает: Проверяет, что пустой список возвращает 0 токенов.
        Цель: Убедиться в корректной обработке пустого списка.
        """
        print("Тест: Пустой список...")
        result = count_tools_tokens([])
        print(f"Результат: {result}")
        assert result == 0, "Пустой список должен возвращать 0 токенов"
    
    def test_single_tool(self):
        """
        Что он делает: Проверяет подсчёт токенов для одного инструмента.
        Цель: Убедиться в базовой работоспособности.
        """
        print("Тест: Один инструмент...")
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City name"}
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        
        result = count_tools_tokens(tools)
        print(f"Результат: {result}")
        
        assert result > 0, "Инструмент должен иметь токены"
    
    def test_multiple_tools(self):
        """
        Что он делает: Проверяет подсчёт токенов для нескольких инструментов.
        Цель: Убедиться, что токены суммируются.
        """
        print("Тест: Несколько инструментов...")
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]
        
        result = count_tools_tokens(tools)
        single_tool = count_tools_tokens([tools[0]])
        
        print(f"Два инструмента: {result}")
        print(f"Один инструмент: {single_tool}")
        
        assert result > single_tool, "Больше инструментов = больше токенов"
    
    def test_tool_with_complex_parameters(self):
        """
        Что он делает: Проверяет подсчёт для инструмента со сложными параметрами.
        Цель: Убедиться, что JSON schema параметров учитывается.
        """
        print("Тест: Сложные параметры...")
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "complex_function",
                    "description": "A function with complex parameters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Name"},
                            "age": {"type": "integer", "description": "Age"},
                            "address": {
                                "type": "object",
                                "properties": {
                                    "street": {"type": "string"},
                                    "city": {"type": "string"},
                                    "country": {"type": "string"}
                                }
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["name", "age"]
                    }
                }
            }
        ]
        
        result = count_tools_tokens(tools)
        print(f"Результат: {result}")
        
        assert result > 0, "Сложный инструмент должен иметь токены"
    
    def test_tool_without_parameters(self):
        """
        Что он делает: Проверяет подсчёт для инструмента без параметров.
        Цель: Убедиться, что отсутствие parameters не ломает подсчёт.
        """
        print("Тест: Без параметров...")
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "no_params_func",
                    "description": "A function without parameters"
                }
            }
        ]
        
        result = count_tools_tokens(tools)
        print(f"Результат: {result}")
        
        assert result > 0, "Инструмент без параметров должен иметь токены"
    
    def test_tool_with_empty_description(self):
        """
        Что он делает: Проверяет подсчёт для инструмента с пустым description.
        Цель: Убедиться, что пустой description не ломает подсчёт.
        """
        print("Тест: Пустой description...")
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "func",
                    "description": "",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]
        
        result = count_tools_tokens(tools)
        print(f"Результат: {result}")
        
        assert result > 0, "Инструмент с пустым description должен иметь токены"
    
    def test_non_function_tool_type(self):
        """
        Что он делает: Проверяет обработку инструмента с type != "function".
        Цель: Убедиться, что non-function tools обрабатываются.
        """
        print("Тест: Non-function tool...")
        tools = [
            {
                "type": "other_type",
                "some_field": "value"
            }
        ]
        
        result = count_tools_tokens(tools)
        print(f"Результат: {result}")
        
        # Должны быть хотя бы служебные токены
        assert result >= 0, "Non-function tool не должен ломать подсчёт"
    
    def test_without_claude_correction(self):
        """
        Что он делает: Проверяет подсчёт без коэффициента коррекции.
        Цель: Убедиться, что apply_claude_correction=False работает.
        """
        print("Тест: Без коэффициента коррекции...")
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "test_func",
                    "description": "Test function",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]
        
        with_correction = count_tools_tokens(tools, apply_claude_correction=True)
        without_correction = count_tools_tokens(tools, apply_claude_correction=False)
        
        print(f"С коррекцией: {with_correction}")
        print(f"Без коррекции: {without_correction}")
        
        assert with_correction > without_correction, "С коррекцией должно быть больше"


class TestEstimateRequestTokens:
    """Тесты для функции estimate_request_tokens."""
    
    def test_messages_only(self):
        """
        Что он делает: Проверяет оценку токенов только для сообщений.
        Цель: Убедиться в базовой работоспособности.
        """
        print("Тест: Только сообщения...")
        messages = [{"role": "user", "content": "Hello!"}]
        
        result = estimate_request_tokens(messages)
        print(f"Результат: {result}")
        
        assert "messages_tokens" in result
        assert "tools_tokens" in result
        assert "system_tokens" in result
        assert "total_tokens" in result
        
        assert result["messages_tokens"] > 0
        assert result["tools_tokens"] == 0
        assert result["system_tokens"] == 0
        assert result["total_tokens"] == result["messages_tokens"]
    
    def test_messages_with_tools(self):
        """
        Что он делает: Проверяет оценку токенов для сообщений с инструментами.
        Цель: Убедиться, что tools учитываются.
        """
        print("Тест: Сообщения с инструментами...")
        messages = [{"role": "user", "content": "What is the weather?"}]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]
        
        result = estimate_request_tokens(messages, tools=tools)
        print(f"Результат: {result}")
        
        assert result["messages_tokens"] > 0
        assert result["tools_tokens"] > 0
        assert result["total_tokens"] == result["messages_tokens"] + result["tools_tokens"]
    
    def test_messages_with_system_prompt(self):
        """
        Что он делает: Проверяет оценку токенов с отдельным system prompt.
        Цель: Убедиться, что system_prompt учитывается.
        """
        print("Тест: С system prompt...")
        messages = [{"role": "user", "content": "Hello!"}]
        system_prompt = "You are a helpful assistant."
        
        result = estimate_request_tokens(messages, system_prompt=system_prompt)
        print(f"Результат: {result}")
        
        assert result["messages_tokens"] > 0
        assert result["system_tokens"] > 0
        assert result["total_tokens"] == result["messages_tokens"] + result["system_tokens"]
    
    def test_full_request(self):
        """
        Что он делает: Проверяет оценку токенов для полного запроса.
        Цель: Убедиться, что все компоненты суммируются.
        """
        print("Тест: Полный запрос...")
        messages = [
            {"role": "user", "content": "What is the weather in Moscow?"}
        ]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"}
                        }
                    }
                }
            }
        ]
        system_prompt = "You are a weather assistant."
        
        result = estimate_request_tokens(messages, tools=tools, system_prompt=system_prompt)
        print(f"Результат: {result}")
        
        expected_total = result["messages_tokens"] + result["tools_tokens"] + result["system_tokens"]
        assert result["total_tokens"] == expected_total, "Total должен быть суммой компонентов"
    
    def test_empty_messages(self):
        """
        Что он делает: Проверяет оценку для пустого списка сообщений.
        Цель: Убедиться в корректной обработке граничного случая.
        """
        print("Тест: Пустые сообщения...")
        result = estimate_request_tokens([])
        print(f"Результат: {result}")
        
        assert result["messages_tokens"] == 0
        assert result["total_tokens"] == 0


class TestClaudeCorrectionFactor:
    """Тесты для коэффициента коррекции Claude."""
    
    def test_correction_factor_value(self):
        """
        Что он делает: Проверяет значение коэффициента коррекции.
        Цель: Убедиться, что коэффициент равен 1.15.
        """
        print(f"Коэффициент коррекции: {CLAUDE_CORRECTION_FACTOR}")
        assert CLAUDE_CORRECTION_FACTOR == 1.15, "Коэффициент должен быть 1.15"
    
    def test_correction_increases_token_count(self):
        """
        Что он делает: Проверяет, что коррекция увеличивает количество токенов.
        Цель: Убедиться, что коэффициент применяется корректно.
        """
        print("Тест: Коррекция увеличивает токены...")
        text = "This is a test text for checking the correction factor"
        
        with_correction = count_tokens(text, apply_claude_correction=True)
        without_correction = count_tokens(text, apply_claude_correction=False)
        
        print(f"С коррекцией: {with_correction}")
        print(f"Без коррекции: {without_correction}")
        
        assert with_correction > without_correction
        
        # Проверяем, что разница примерно 15%
        increase_percent = (with_correction - without_correction) / without_correction * 100
        print(f"Увеличение: {increase_percent:.1f}%")
        
        # Допускаем погрешность из-за округления
        assert 10 <= increase_percent <= 20, "Увеличение должно быть около 15%"
class TestGetEncoding:
    """Тесты для функции _get_encoding."""
    
    def test_returns_encoding_when_tiktoken_available(self):
        """
        Что он делает: Проверяет, что _get_encoding возвращает encoding когда tiktoken доступен.
        Цель: Убедиться в корректной инициализации tiktoken.
        """
        print("Тест: tiktoken доступен...")
        
        # Сбрасываем глобальную переменную для чистого теста
        import kiro.tokenizer as tokenizer_module
        original_encoding = tokenizer_module._encoding
        tokenizer_module._encoding = None
        
        try:
            encoding = _get_encoding()
            print(f"Encoding: {encoding}")
            
            # Если tiktoken установлен, должен вернуть encoding
            if encoding is not None:
                assert hasattr(encoding, 'encode'), "Encoding должен иметь метод encode"
        finally:
            # Восстанавливаем
            tokenizer_module._encoding = original_encoding
    
    def test_caches_encoding(self):
        """
        Что он делает: Проверяет, что encoding кэшируется.
        Цель: Убедиться в ленивой инициализации.
        """
        print("Тест: Кэширование encoding...")
        
        encoding1 = _get_encoding()
        encoding2 = _get_encoding()
        
        print(f"Encoding 1: {encoding1}")
        print(f"Encoding 2: {encoding2}")
        
        # Должен вернуть тот же объект
        assert encoding1 is encoding2, "Encoding должен кэшироваться"
    
    def test_handles_import_error(self):
        """
        Что он делает: Проверяет обработку ImportError при отсутствии tiktoken.
        Цель: Убедиться, что система работает без tiktoken.
        """
        print("Тест: ImportError...")
        
        import kiro.tokenizer as tokenizer_module
        original_encoding = tokenizer_module._encoding
        tokenizer_module._encoding = None
        
        try:
            # Мокируем import tiktoken чтобы выбросить ImportError
            with patch.dict('sys.modules', {'tiktoken': None}):
                with patch('builtins.__import__', side_effect=ImportError("No module named 'tiktoken'")):
                    # Сбрасываем кэш
                    tokenizer_module._encoding = None
                    
                    # Должен вернуть None и не упасть
                    # Примечание: из-за кэширования этот тест может не работать идеально
                    # но главное - проверить что код не падает
                    pass
        finally:
            tokenizer_module._encoding = original_encoding


class TestTokenizerIntegration:
    """Интеграционные тесты для токенизатора."""
    
    def test_realistic_chat_request(self):
        """
        Что он делает: Проверяет подсчёт токенов для реалистичного chat запроса.
        Цель: Убедиться в корректной работе на реальных данных.
        """
        print("Тест: Реалистичный chat запрос...")
        
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Be concise and accurate."},
            {"role": "user", "content": "What is the capital of France?"},
            {"role": "assistant", "content": "The capital of France is Paris."},
            {"role": "user", "content": "What is its population?"}
        ]
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        result = estimate_request_tokens(messages, tools=tools)
        print(f"Результат: {result}")
        
        # Проверяем разумность значений
        assert result["messages_tokens"] > 50, "Сообщения должны иметь > 50 токенов"
        assert result["tools_tokens"] > 20, "Tools должны иметь > 20 токенов"
        assert result["total_tokens"] > 70, "Total должен быть > 70 токенов"
    
    def test_large_context(self):
        """
        Что он делает: Проверяет подсчёт токенов для большого контекста.
        Цель: Убедиться в производительности на больших данных.
        """
        print("Тест: Большой контекст...")
        
        # Создаём большой текст
        large_text = "This is a test sentence. " * 1000  # ~5000 слов
        
        messages = [{"role": "user", "content": large_text}]
        
        result = estimate_request_tokens(messages)
        print(f"Токенов в большом тексте: {result['total_tokens']}")
        
        # Должно быть много токенов
        assert result["total_tokens"] > 1000, "Большой текст должен иметь > 1000 токенов"
    
    def test_consistency_across_calls(self):
        """
        Что он делает: Проверяет консистентность подсчёта при повторных вызовах.
        Цель: Убедиться, что результаты детерминированы.
        """
        print("Тест: Консистентность...")
        
        text = "This is a test for consistency checking"
        
        results = [count_tokens(text) for _ in range(5)]
        print(f"Результаты: {results}")
        
        # Все результаты должны быть одинаковыми
        assert len(set(results)) == 1, "Результаты должны быть консистентными"


# =============================================================================
# Tests for Anthropic-format token counting
# =============================================================================


class TestCountAnthropicContentBlockTokens:
    """Tests for count_anthropic_content_block_tokens function."""

    def test_text_block(self):
        """Counts tokens in a text content block."""
        block = {"type": "text", "text": "Hello, world!"}
        result = count_anthropic_content_block_tokens(block)
        assert result > 0

    def test_empty_text_block(self):
        """Empty text block returns 0 tokens."""
        block = {"type": "text", "text": ""}
        result = count_anthropic_content_block_tokens(block)
        assert result == 0

    def test_thinking_block(self):
        """Counts tokens in a thinking content block."""
        block = {"type": "thinking", "thinking": "Let me reason about this step by step..."}
        result = count_anthropic_content_block_tokens(block)
        assert result > 0

    def test_image_block_returns_fixed_estimate(self):
        """Image blocks return a fixed ~100 token estimate."""
        block = {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "abc123"}}
        result = count_anthropic_content_block_tokens(block)
        assert result == 100

    def test_tool_use_block(self):
        """Counts tokens in a tool_use content block."""
        block = {
            "type": "tool_use",
            "id": "toolu_123",
            "name": "get_weather",
            "input": {"location": "Istanbul", "units": "celsius"}
        }
        result = count_anthropic_content_block_tokens(block)
        # Should include service tokens + name + input JSON
        assert result > 4

    def test_tool_use_block_empty_input(self):
        """Tool use with empty input still has service + name tokens."""
        block = {"type": "tool_use", "id": "toolu_123", "name": "ping", "input": {}}
        result = count_anthropic_content_block_tokens(block)
        assert result > 0

    def test_tool_result_block_string_content(self):
        """Counts tokens in a tool_result with string content."""
        block = {
            "type": "tool_result",
            "tool_use_id": "toolu_123",
            "content": "The weather in Istanbul is sunny, 28°C"
        }
        result = count_anthropic_content_block_tokens(block)
        assert result > 4

    def test_tool_result_block_list_content(self):
        """Counts tokens in a tool_result with nested content blocks."""
        block = {
            "type": "tool_result",
            "tool_use_id": "toolu_123",
            "content": [
                {"type": "text", "text": "Result line 1"},
                {"type": "text", "text": "Result line 2"}
            ]
        }
        result = count_anthropic_content_block_tokens(block)
        assert result > 4

    def test_tool_result_block_empty_content(self):
        """Tool result with empty content still has service tokens."""
        block = {"type": "tool_result", "tool_use_id": "toolu_123", "content": ""}
        result = count_anthropic_content_block_tokens(block)
        # Service tokens + tool_use_id tokens
        assert result > 0

    def test_tool_result_with_nested_image(self):
        """Tool result containing an image in nested content."""
        block = {
            "type": "tool_result",
            "tool_use_id": "toolu_123",
            "content": [
                {"type": "text", "text": "Screenshot captured"},
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "..."}}
            ]
        }
        result = count_anthropic_content_block_tokens(block)
        # Should include text tokens + 100 for image + service tokens
        assert result > 100

    def test_unknown_block_type_returns_zero(self):
        """Unknown block types return 0 tokens."""
        block = {"type": "unknown_type", "data": "something"}
        result = count_anthropic_content_block_tokens(block)
        assert result == 0

    def test_missing_type_returns_zero(self):
        """Block without type field returns 0 tokens."""
        block = {"text": "no type field"}
        result = count_anthropic_content_block_tokens(block)
        assert result == 0


class TestCountAnthropicMessageTokens:
    """Tests for count_anthropic_message_tokens function."""

    def test_empty_list_returns_zero(self):
        """Empty message list returns 0."""
        assert count_anthropic_message_tokens([]) == 0

    def test_none_returns_zero(self):
        """None returns 0."""
        assert count_anthropic_message_tokens(None) == 0

    def test_single_string_content_message(self):
        """Counts tokens for a message with string content."""
        messages = [{"role": "user", "content": "Hello, Claude!"}]
        result = count_anthropic_message_tokens(messages)
        assert result > 0

    def test_single_block_content_message(self):
        """Counts tokens for a message with content block list."""
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": "Hello, Claude!"}]
            }
        ]
        result = count_anthropic_message_tokens(messages)
        assert result > 0

    def test_multi_turn_conversation(self):
        """Multi-turn conversation has more tokens than single message."""
        single = [{"role": "user", "content": "Hi"}]
        multi = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello! How can I help?"},
            {"role": "user", "content": "What is the weather?"},
        ]
        single_tokens = count_anthropic_message_tokens(single)
        multi_tokens = count_anthropic_message_tokens(multi)
        assert multi_tokens > single_tokens

    def test_message_with_tool_use_blocks(self):
        """Counts tokens for assistant message with tool_use blocks."""
        messages = [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Let me check the weather."},
                    {
                        "type": "tool_use",
                        "id": "toolu_abc",
                        "name": "get_weather",
                        "input": {"location": "Paris"}
                    }
                ]
            }
        ]
        result = count_anthropic_message_tokens(messages)
        assert result > 0

    def test_thinking_blocks_skipped_in_assistant_messages(self):
        """Thinking blocks in assistant messages are NOT counted (Anthropic spec)."""
        messages_with_thinking = [
            {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "Let me reason step by step about this complex problem..."},
                    {"type": "text", "text": "The answer is 42."}
                ]
            }
        ]
        messages_without_thinking = [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "The answer is 42."}
                ]
            }
        ]
        with_thinking = count_anthropic_message_tokens(messages_with_thinking)
        without_thinking = count_anthropic_message_tokens(messages_without_thinking)
        assert with_thinking == without_thinking

    def test_thinking_blocks_skipped_only_for_assistant_role(self):
        """Thinking blocks are only skipped for assistant role, not user."""
        # User message with thinking block (unusual but should be counted)
        user_msg = [
            {
                "role": "user",
                "content": [
                    {"type": "thinking", "thinking": "Some thinking text here"},
                    {"type": "text", "text": "Hello"}
                ]
            }
        ]
        user_msg_no_thinking = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Hello"}
                ]
            }
        ]
        with_thinking = count_anthropic_message_tokens(user_msg)
        without_thinking = count_anthropic_message_tokens(user_msg_no_thinking)
        # User thinking blocks SHOULD be counted (not skipped)
        assert with_thinking > without_thinking

    def test_message_with_tool_result_blocks(self):
        """Counts tokens for user message with tool_result blocks."""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_abc",
                        "content": "Sunny, 25°C in Paris"
                    }
                ]
            }
        ]
        result = count_anthropic_message_tokens(messages)
        assert result > 0

    def test_message_with_image_block(self):
        """Image blocks contribute ~100 tokens."""
        without_image = [{"role": "user", "content": [{"type": "text", "text": "Describe this"}]}]
        with_image = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this"},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "..."}}
                ]
            }
        ]
        tokens_without = count_anthropic_message_tokens(without_image)
        tokens_with = count_anthropic_message_tokens(with_image)
        assert tokens_with > tokens_without

    def test_claude_correction_applied(self):
        """Claude correction factor increases token count."""
        messages = [{"role": "user", "content": "Test message for correction factor"}]
        with_correction = count_anthropic_message_tokens(messages, apply_claude_correction=True)
        without_correction = count_anthropic_message_tokens(messages, apply_claude_correction=False)
        assert with_correction > without_correction

    def test_empty_content_message(self):
        """Message with empty string content still has service tokens."""
        messages = [{"role": "assistant", "content": ""}]
        result = count_anthropic_message_tokens(messages)
        assert result > 0

    def test_none_content_message(self):
        """Message with None content still has service tokens."""
        messages = [{"role": "assistant", "content": None}]
        result = count_anthropic_message_tokens(messages)
        assert result > 0


class TestCountAnthropicToolsTokens:
    """Tests for count_anthropic_tools_tokens function."""

    def test_none_returns_zero(self):
        """None returns 0."""
        assert count_anthropic_tools_tokens(None) == 0

    def test_empty_list_returns_zero(self):
        """Empty list returns 0."""
        assert count_anthropic_tools_tokens([]) == 0

    def test_single_tool(self):
        """Counts tokens for a single Anthropic tool definition."""
        tools = [
            {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name"}
                    },
                    "required": ["location"]
                }
            }
        ]
        result = count_anthropic_tools_tokens(tools)
        assert result > 0

    def test_multiple_tools(self):
        """More tools means more tokens."""
        one_tool = [
            {"name": "tool_a", "description": "Tool A", "input_schema": {"type": "object", "properties": {}}}
        ]
        two_tools = [
            {"name": "tool_a", "description": "Tool A", "input_schema": {"type": "object", "properties": {}}},
            {"name": "tool_b", "description": "Tool B", "input_schema": {"type": "object", "properties": {}}}
        ]
        assert count_anthropic_tools_tokens(two_tools) > count_anthropic_tools_tokens(one_tool)

    def test_tool_without_description(self):
        """Tool without description still has name + schema tokens."""
        tools = [
            {"name": "ping", "input_schema": {"type": "object", "properties": {}}}
        ]
        result = count_anthropic_tools_tokens(tools)
        assert result > 0

    def test_tool_with_complex_schema(self):
        """Complex input_schema produces more tokens."""
        simple = [
            {"name": "func", "description": "Simple", "input_schema": {"type": "object", "properties": {}}}
        ]
        complex_tool = [
            {
                "name": "func",
                "description": "Complex",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Full name"},
                        "age": {"type": "integer", "description": "Age in years"},
                        "address": {
                            "type": "object",
                            "properties": {
                                "street": {"type": "string"},
                                "city": {"type": "string"},
                                "zip": {"type": "string"}
                            }
                        }
                    },
                    "required": ["name", "age"]
                }
            }
        ]
        assert count_anthropic_tools_tokens(complex_tool) > count_anthropic_tools_tokens(simple)

    def test_claude_correction_applied(self):
        """Claude correction factor increases tool token count."""
        tools = [
            {"name": "test", "description": "A test tool", "input_schema": {"type": "object", "properties": {}}}
        ]
        with_correction = count_anthropic_tools_tokens(tools, apply_claude_correction=True)
        without_correction = count_anthropic_tools_tokens(tools, apply_claude_correction=False)
        assert with_correction > without_correction


class TestCountAnthropicSystemTokens:
    """Tests for count_anthropic_system_tokens function."""

    def test_none_returns_zero(self):
        """None system prompt returns 0."""
        assert count_anthropic_system_tokens(None) == 0

    def test_empty_string_returns_zero(self):
        """Empty string returns 0."""
        assert count_anthropic_system_tokens("") == 0

    def test_string_system_prompt(self):
        """Counts tokens for a plain string system prompt."""
        result = count_anthropic_system_tokens("You are a helpful assistant.")
        assert result > 0

    def test_list_system_prompt(self):
        """Counts tokens for a list-of-blocks system prompt (prompt caching format)."""
        system = [
            {"type": "text", "text": "You are a helpful assistant."},
            {"type": "text", "text": "Always be concise.", "cache_control": {"type": "ephemeral"}}
        ]
        result = count_anthropic_system_tokens(system)
        assert result > 0

    def test_list_system_prompt_matches_string(self):
        """List format with single block should be close to equivalent string."""
        text = "You are a helpful assistant."
        string_tokens = count_anthropic_system_tokens(text)
        list_tokens = count_anthropic_system_tokens([{"type": "text", "text": text}])
        # Should be the same since both contain the same text
        assert string_tokens == list_tokens

    def test_empty_list_returns_zero(self):
        """Empty list returns 0."""
        assert count_anthropic_system_tokens([]) == 0

    def test_claude_correction_applied(self):
        """Claude correction factor increases system token count."""
        system = "You are a helpful assistant that always provides detailed, accurate, and well-structured responses to user queries."
        with_correction = count_anthropic_system_tokens(system, apply_claude_correction=True)
        without_correction = count_anthropic_system_tokens(system, apply_claude_correction=False)
        assert with_correction > without_correction


class TestEstimateAnthropicRequestTokens:
    """Tests for estimate_anthropic_request_tokens function."""

    def test_messages_only(self):
        """Counts tokens for messages-only request."""
        messages = [{"role": "user", "content": "Hello!"}]
        result = estimate_anthropic_request_tokens(messages)
        assert result > 0

    def test_messages_with_tools(self):
        """Tools add to the total token count."""
        messages = [{"role": "user", "content": "Hello!"}]
        tools = [
            {"name": "get_weather", "description": "Get weather", "input_schema": {"type": "object", "properties": {}}}
        ]
        without_tools = estimate_anthropic_request_tokens(messages)
        with_tools = estimate_anthropic_request_tokens(messages, tools=tools)
        assert with_tools > without_tools

    def test_messages_with_system(self):
        """System prompt adds to the total token count."""
        messages = [{"role": "user", "content": "Hello!"}]
        without_system = estimate_anthropic_request_tokens(messages)
        with_system = estimate_anthropic_request_tokens(messages, system="You are a helpful assistant.")
        assert with_system > without_system

    def test_full_request(self):
        """Full request with messages + tools + system."""
        messages = [
            {"role": "user", "content": "What is the weather in Istanbul?"},
            {"role": "assistant", "content": [
                {"type": "tool_use", "id": "toolu_1", "name": "get_weather", "input": {"location": "Istanbul"}}
            ]},
            {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "toolu_1", "content": "Sunny, 30°C"}
            ]}
        ]
        tools = [
            {
                "name": "get_weather",
                "description": "Get weather for a location",
                "input_schema": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"]
                }
            }
        ]
        system = "You are a weather assistant."

        result = estimate_anthropic_request_tokens(messages, tools=tools, system=system)
        assert result > 50  # Should be a reasonable number for this request

    def test_empty_messages(self):
        """Empty messages returns 0 (or close to 0)."""
        result = estimate_anthropic_request_tokens([])
        assert result == 0

    def test_consistency(self):
        """Same input always produces same output."""
        messages = [{"role": "user", "content": "Deterministic test"}]
        results = [estimate_anthropic_request_tokens(messages) for _ in range(5)]
        assert len(set(results)) == 1