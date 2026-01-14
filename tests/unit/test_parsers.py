# -*- coding: utf-8 -*-

"""
Unit-тесты для AwsEventStreamParser и вспомогательных функций парсинга.
Проверяет логику парсинга AWS SSE потока от Kiro API.
"""

from kiro.parsers import (
    AwsEventStreamParser,
    find_matching_brace,
    parse_bracket_tool_calls,
    deduplicate_tool_calls,
)


class TestFindMatchingBrace:
    """Тесты функции find_matching_brace."""

    def test_simple_json_object(self):
        """
        Что он делает: Проверяет поиск закрывающей скобки для простого JSON.
        Цель: Убедиться, что базовый случай работает.
        """
        print("Настройка: Простой JSON объект...")
        text = '{"key": "value"}'

        print("Действие: Поиск закрывающей скобки...")
        result = find_matching_brace(text, 0)

        print(f"Сравниваем результат: Ожидалось 15, Получено {result}")
        assert result == 15

    def test_nested_json_object(self):
        """
        Что он делает: Проверяет поиск для вложенного JSON.
        Цель: Убедиться, что вложенность обрабатывается корректно.
        """
        print("Настройка: Вложенный JSON объект...")
        text = '{"outer": {"inner": "value"}}'

        print("Действие: Поиск закрывающей скобки...")
        result = find_matching_brace(text, 0)

        # Длина строки 29, индекс последнего символа 28
        print(f"Сравниваем результат: Ожидалось 28, Получено {result}")
        assert result == 28

    def test_json_with_braces_in_string(self):
        """
        Что он делает: Проверяет игнорирование скобок внутри строк.
        Цель: Убедиться, что скобки в строках не влияют на подсчёт.
        """
        print("Настройка: JSON со скобками в строке...")
        text = '{"text": "Hello {world}"}'

        print("Действие: Поиск закрывающей скобки...")
        result = find_matching_brace(text, 0)

        print(f"Сравниваем результат: Ожидалось 24, Получено {result}")
        assert result == 24

    def test_json_with_escaped_quotes(self):
        """
        Что он делает: Проверяет обработку экранированных кавычек.
        Цель: Убедиться, что escape-последовательности не ломают парсинг.
        """
        print("Настройка: JSON с экранированными кавычками...")
        text = '{"text": "Say \\"hello\\""}'

        print("Действие: Поиск закрывающей скобки...")
        result = find_matching_brace(text, 0)

        # Длина строки 25, индекс последнего символа 24
        print(f"Сравниваем результат: Ожидалось 24, Получено {result}")
        assert result == 24

    def test_incomplete_json(self):
        """
        Что он делает: Проверяет обработку незавершённого JSON.
        Цель: Убедиться, что возвращается -1 для неполного JSON.
        """
        print("Настройка: Незавершённый JSON...")
        text = '{"key": "value"'

        print("Действие: Поиск закрывающей скобки...")
        result = find_matching_brace(text, 0)

        print(f"Сравниваем результат: Ожидалось -1, Получено {result}")
        assert result == -1

    def test_invalid_start_position(self):
        """
        Что он делает: Проверяет обработку невалидной стартовой позиции.
        Цель: Убедиться, что возвращается -1 если start_pos не на '{'.
        """
        print("Настройка: Текст без скобки на start_pos...")
        text = 'hello {"key": "value"}'

        print("Действие: Поиск с позиции 0 (не скобка)...")
        result = find_matching_brace(text, 0)

        print(f"Сравниваем результат: Ожидалось -1, Получено {result}")
        assert result == -1

    def test_start_position_out_of_bounds(self):
        """
        Что он делает: Проверяет обработку позиции за пределами текста.
        Цель: Убедиться, что возвращается -1 для невалидной позиции.
        """
        print("Настройка: Короткий текст...")
        text = '{"a":1}'

        print("Действие: Поиск с позиции 100...")
        result = find_matching_brace(text, 100)

        print(f"Сравниваем результат: Ожидалось -1, Получено {result}")
        assert result == -1


class TestParseBracketToolCalls:
    """Тесты функции parse_bracket_tool_calls."""

    def test_parses_single_tool_call(self):
        """
        Что он делает: Проверяет парсинг одного tool call.
        Цель: Убедиться, что bracket-style tool call извлекается корректно.
        """
        print("Настройка: Текст с одним tool call...")
        text = '[Called get_weather with args: {"location": "Moscow"}]'

        print("Действие: Парсинг tool calls...")
        result = parse_bracket_tool_calls(text)

        print(f"Результат: {result}")
        assert len(result) == 1
        assert result[0]["function"]["name"] == "get_weather"
        assert '"location"' in result[0]["function"]["arguments"]

    def test_parses_multiple_tool_calls(self):
        """
        Что он делает: Проверяет парсинг нескольких tool calls.
        Цель: Убедиться, что все tool calls извлекаются.
        """
        print("Настройка: Текст с несколькими tool calls...")
        text = """
        [Called get_weather with args: {"location": "Moscow"}]
        Some text in between
        [Called get_time with args: {"timezone": "UTC"}]
        """

        print("Действие: Парсинг tool calls...")
        result = parse_bracket_tool_calls(text)

        print(f"Результат: {result}")
        assert len(result) == 2
        assert result[0]["function"]["name"] == "get_weather"
        assert result[1]["function"]["name"] == "get_time"

    def test_returns_empty_for_no_tool_calls(self):
        """
        Что он делает: Проверяет возврат пустого списка без tool calls.
        Цель: Убедиться, что обычный текст не парсится как tool call.
        """
        print("Настройка: Обычный текст без tool calls...")
        text = "This is just regular text without any tool calls."

        print("Действие: Парсинг tool calls...")
        result = parse_bracket_tool_calls(text)

        print(f"Сравниваем результат: Ожидалось [], Получено {result}")
        assert result == []

    def test_returns_empty_for_empty_string(self):
        """
        Что он делает: Проверяет обработку пустой строки.
        Цель: Убедиться, что пустая строка не вызывает ошибок.
        """
        print("Настройка: Пустая строка...")

        print("Действие: Парсинг tool calls...")
        result = parse_bracket_tool_calls("")

        print(f"Сравниваем результат: Ожидалось [], Получено {result}")
        assert result == []

    def test_returns_empty_for_none(self):
        """
        Что он делает: Проверяет обработку None.
        Цель: Убедиться, что None не вызывает ошибок.
        """
        print("Настройка: None...")

        print("Действие: Парсинг tool calls...")
        result = parse_bracket_tool_calls(None)

        print(f"Сравниваем результат: Ожидалось [], Получено {result}")
        assert result == []

    def test_handles_nested_json_in_args(self):
        """
        Что он делает: Проверяет парсинг вложенного JSON в аргументах.
        Цель: Убедиться, что сложные аргументы парсятся корректно.
        """
        print("Настройка: Tool call с вложенным JSON...")
        text = (
            '[Called complex_func with args: {"data": {"nested": {"deep": "value"}}}]'
        )

        print("Действие: Парсинг tool calls...")
        result = parse_bracket_tool_calls(text)

        print(f"Результат: {result}")
        assert len(result) == 1
        assert result[0]["function"]["name"] == "complex_func"
        assert "nested" in result[0]["function"]["arguments"]

    def test_generates_unique_ids(self):
        """
        Что он делает: Проверяет генерацию уникальных ID для tool calls.
        Цель: Убедиться, что каждый tool call имеет уникальный ID.
        """
        print("Настройка: Два одинаковых tool calls...")
        text = """
        [Called func with args: {"a": 1}]
        [Called func with args: {"a": 1}]
        """

        print("Действие: Парсинг tool calls...")
        result = parse_bracket_tool_calls(text)

        print(f"IDs: {[r['id'] for r in result]}")
        assert len(result) == 2
        assert result[0]["id"] != result[1]["id"]


class TestDeduplicateToolCalls:
    """Тесты функции deduplicate_tool_calls."""

    def test_removes_duplicates(self):
        """
        Что он делает: Проверяет удаление дубликатов.
        Цель: Убедиться, что одинаковые tool calls удаляются.
        """
        print("Настройка: Список с дубликатами...")
        tool_calls = [
            {"id": "1", "function": {"name": "func", "arguments": '{"a": 1}'}},
            {"id": "2", "function": {"name": "func", "arguments": '{"a": 1}'}},
            {"id": "3", "function": {"name": "other", "arguments": '{"b": 2}'}},
        ]

        print("Действие: Дедупликация...")
        result = deduplicate_tool_calls(tool_calls)

        print(f"Сравниваем длину: Ожидалось 2, Получено {len(result)}")
        assert len(result) == 2

    def test_preserves_first_occurrence(self):
        """
        Что он делает: Проверяет сохранение первого вхождения.
        Цель: Убедиться, что сохраняется первый tool call из дубликатов.
        """
        print("Настройка: Список с дубликатами...")
        tool_calls = [
            {"id": "first", "function": {"name": "func", "arguments": '{"a": 1}'}},
            {"id": "second", "function": {"name": "func", "arguments": '{"a": 1}'}},
        ]

        print("Действие: Дедупликация...")
        result = deduplicate_tool_calls(tool_calls)

        print(f"Сравниваем ID: Ожидалось 'first', Получено '{result[0]['id']}'")
        assert result[0]["id"] == "first"

    def test_handles_empty_list(self):
        """
        Что он делает: Проверяет обработку пустого списка.
        Цель: Убедиться, что пустой список не вызывает ошибок.
        """
        print("Настройка: Пустой список...")

        print("Действие: Дедупликация...")
        result = deduplicate_tool_calls([])

        print(f"Сравниваем результат: Ожидалось [], Получено {result}")
        assert result == []

    def test_deduplicates_by_id_keeps_one_with_arguments(self):
        """
        Что он делает: Проверяет дедупликацию по id с сохранением tool call с аргументами.
        Цель: Убедиться, что при дубликатах по id сохраняется тот, у которого есть аргументы.
        """
        print(
            "Настройка: Два tool calls с одинаковым id, один с аргументами, один пустой..."
        )
        tool_calls = [
            {"id": "call_123", "function": {"name": "func", "arguments": "{}"}},
            {
                "id": "call_123",
                "function": {"name": "func", "arguments": '{"location": "Moscow"}'},
            },
        ]

        print("Действие: Дедупликация...")
        result = deduplicate_tool_calls(tool_calls)

        print(f"Результат: {result}")
        print(f"Сравниваем длину: Ожидалось 1, Получено {len(result)}")
        assert len(result) == 1

        print("Проверяем, что сохранился tool call с аргументами...")
        assert "Moscow" in result[0]["function"]["arguments"]

    def test_deduplicates_by_id_prefers_longer_arguments(self):
        """
        Что он делает: Проверяет, что при дубликатах по id предпочитаются более длинные аргументы.
        Цель: Убедиться, что сохраняется tool call с более полными аргументами.
        """
        print("Настройка: Два tool calls с одинаковым id, разной длины аргументов...")
        tool_calls = [
            {
                "id": "call_abc",
                "function": {"name": "search", "arguments": '{"q": "test"}'},
            },
            {
                "id": "call_abc",
                "function": {
                    "name": "search",
                    "arguments": '{"q": "test", "limit": 10, "offset": 0}',
                },
            },
        ]

        print("Действие: Дедупликация...")
        result = deduplicate_tool_calls(tool_calls)

        print(f"Результат: {result}")
        assert len(result) == 1

        print("Проверяем, что сохранился tool call с более длинными аргументами...")
        assert "limit" in result[0]["function"]["arguments"]

    def test_deduplicates_empty_arguments_replaced_by_non_empty(self):
        """
        Что он делает: Проверяет замену пустых аргументов на непустые.
        Цель: Убедиться, что "{}" заменяется на реальные аргументы.
        """
        print(
            "Настройка: Первый tool call с пустыми аргументами, второй с реальными..."
        )
        tool_calls = [
            {"id": "call_xyz", "function": {"name": "get_weather", "arguments": "{}"}},
            {
                "id": "call_xyz",
                "function": {"name": "get_weather", "arguments": '{"city": "London"}'},
            },
        ]

        print("Действие: Дедупликация...")
        result = deduplicate_tool_calls(tool_calls)

        print(f"Результат: {result}")
        assert len(result) == 1
        assert result[0]["function"]["arguments"] == '{"city": "London"}'

    def test_handles_tool_calls_without_id(self):
        """
        Что он делает: Проверяет обработку tool calls без id.
        Цель: Убедиться, что tool calls без id дедуплицируются по name+arguments.
        """
        print("Настройка: Tool calls без id...")
        tool_calls = [
            {"id": "", "function": {"name": "func", "arguments": '{"a": 1}'}},
            {"id": "", "function": {"name": "func", "arguments": '{"a": 1}'}},
            {"id": "", "function": {"name": "func", "arguments": '{"b": 2}'}},
        ]

        print("Действие: Дедупликация...")
        result = deduplicate_tool_calls(tool_calls)

        print(f"Результат: {result}")
        # Два уникальных по name+arguments
        assert len(result) == 2

    def test_mixed_with_and_without_id(self):
        """
        Что он делает: Проверяет смешанный список с id и без.
        Цель: Убедиться, что оба типа обрабатываются корректно.
        """
        print("Настройка: Смешанный список...")
        tool_calls = [
            {"id": "call_1", "function": {"name": "func1", "arguments": '{"x": 1}'}},
            {
                "id": "call_1",
                "function": {"name": "func1", "arguments": "{}"},
            },  # Дубликат по id
            {"id": "", "function": {"name": "func2", "arguments": '{"y": 2}'}},
            {
                "id": "",
                "function": {"name": "func2", "arguments": '{"y": 2}'},
            },  # Дубликат по name+args
        ]

        print("Действие: Дедупликация...")
        result = deduplicate_tool_calls(tool_calls)

        print(f"Результат: {result}")
        # call_1 с аргументами + func2 один раз
        assert len(result) == 2

        # Проверяем, что call_1 сохранил аргументы
        call_1 = next(tc for tc in result if tc["id"] == "call_1")
        assert call_1["function"]["arguments"] == '{"x": 1}'


class TestAwsEventStreamParserInitialization:
    """Тесты инициализации AwsEventStreamParser."""

    def test_initialization_creates_empty_state(self):
        """
        Что он делает: Проверяет начальное состояние парсера.
        Цель: Убедиться, что парсер создаётся с пустым состоянием.
        """
        print("Настройка: Создание парсера...")
        parser = AwsEventStreamParser()

        print("Проверка: Буфер пуст...")
        assert parser.buffer == ""

        print("Проверка: last_content is None...")
        assert parser.last_content is None

        print("Проверка: current_tool_call is None...")
        assert parser.current_tool_call is None

        print("Проверка: tool_calls пуст...")
        assert parser.tool_calls == []


class TestAwsEventStreamParserFeed:
    """Тесты метода feed парсера."""

    def test_parses_content_event(self, aws_event_parser):
        """
        Что он делает: Проверяет парсинг события с контентом.
        Цель: Убедиться, что текстовый контент извлекается.
        """
        print("Настройка: Chunk с контентом...")
        chunk = b'{"content":"Hello World"}'

        print("Действие: Парсинг chunk...")
        events = aws_event_parser.feed(chunk)

        print(f"Результат: {events}")
        assert len(events) == 1
        assert events[0]["type"] == "content"
        assert events[0]["data"] == "Hello World"

    def test_parses_multiple_content_events(self, aws_event_parser):
        """
        Что он делает: Проверяет парсинг нескольких событий контента.
        Цель: Убедиться, что все события извлекаются.
        """
        print("Настройка: Chunk с несколькими событиями...")
        chunk = b'{"content":"First"}{"content":"Second"}'

        print("Действие: Парсинг chunk...")
        events = aws_event_parser.feed(chunk)

        print(f"Результат: {events}")
        assert len(events) == 2
        assert events[0]["data"] == "First"
        assert events[1]["data"] == "Second"

    def test_deduplicates_repeated_content(self, aws_event_parser):
        """
        Что он делает: Проверяет дедупликацию повторяющегося контента.
        Цель: Убедиться, что одинаковый контент не дублируется.
        """
        print("Настройка: Chunks с повторяющимся контентом...")

        print("Действие: Парсинг первого chunk...")
        events1 = aws_event_parser.feed(b'{"content":"Same"}')

        print("Действие: Парсинг второго chunk с тем же контентом...")
        events2 = aws_event_parser.feed(b'{"content":"Same"}')

        print(f"Первый результат: {events1}")
        print(f"Второй результат: {events2}")
        assert len(events1) == 1
        assert len(events2) == 0  # Дубликат отфильтрован

    def test_parses_usage_event(self, aws_event_parser):
        """
        Что он делает: Проверяет парсинг события usage.
        Цель: Убедиться, что информация о credits извлекается.
        """
        print("Настройка: Chunk с usage...")
        chunk = b'{"usage":1.5}'

        print("Действие: Парсинг chunk...")
        events = aws_event_parser.feed(chunk)

        print(f"Результат: {events}")
        assert len(events) == 1
        assert events[0]["type"] == "usage"
        assert events[0]["data"] == 1.5

    def test_parses_context_usage_event(self, aws_event_parser):
        """
        Что он делает: Проверяет парсинг события context_usage.
        Цель: Убедиться, что процент использования контекста извлекается.
        """
        print("Настройка: Chunk с context usage...")
        chunk = b'{"contextUsagePercentage":25.5}'

        print("Действие: Парсинг chunk...")
        events = aws_event_parser.feed(chunk)

        print(f"Результат: {events}")
        assert len(events) == 1
        assert events[0]["type"] == "context_usage"
        assert events[0]["data"] == 25.5

    def test_handles_incomplete_json(self, aws_event_parser):
        """
        Что он делает: Проверяет обработку неполного JSON.
        Цель: Убедиться, что неполный JSON буферизуется.
        """
        print("Настройка: Неполный chunk...")
        chunk = b'{"content":"Hel'

        print("Действие: Парсинг неполного chunk...")
        events = aws_event_parser.feed(chunk)

        print(f"Результат: {events}")
        assert len(events) == 0  # Ничего не распарсено

        print("Проверка: Данные в буфере...")
        assert "content" in aws_event_parser.buffer

    def test_completes_json_across_chunks(self, aws_event_parser):
        """
        Что он делает: Проверяет сборку JSON из нескольких chunks.
        Цель: Убедиться, что JSON собирается из частей.
        """
        print("Настройка: Первая часть JSON...")
        events1 = aws_event_parser.feed(b'{"content":"Hel')

        print("Действие: Вторая часть JSON...")
        events2 = aws_event_parser.feed(b'lo World"}')

        print(f"Первый результат: {events1}")
        print(f"Второй результат: {events2}")
        assert len(events1) == 0
        assert len(events2) == 1
        assert events2[0]["data"] == "Hello World"

    def test_decodes_escape_sequences(self, aws_event_parser):
        """
        Что он делает: Проверяет декодирование escape-последовательностей.
        Цель: Убедиться, что \\n преобразуется в реальный перенос строки.
        """
        print("Настройка: Chunk с escape-последовательностью...")
        # Используем правильный формат escape-последовательности
        chunk = b'{"content":"Line1\\nLine2"}'

        print("Действие: Парсинг chunk...")
        events = aws_event_parser.feed(chunk)

        print(f"Результат: {events}")
        assert len(events) == 1
        assert "\n" in events[0]["data"]

    def test_handles_invalid_bytes(self, aws_event_parser):
        """
        Что он делает: Проверяет обработку невалидных байтов.
        Цель: Убедиться, что невалидные данные не ломают парсер.
        """
        print("Настройка: Невалидные байты...")
        chunk = b'\xff\xfe{"content":"test"}'

        print("Действие: Парсинг chunk...")
        events = aws_event_parser.feed(chunk)

        print(f"Результат: {events}")
        # Парсер должен продолжить работу
        assert len(events) == 1


class TestAwsEventStreamParserToolCalls:
    """Тесты парсинга tool calls."""

    def test_parses_tool_start_event(self, aws_event_parser):
        """
        Что он делает: Проверяет парсинг начала tool call.
        Цель: Убедиться, что tool_start создаёт current_tool_call.
        """
        print("Настройка: Chunk с началом tool call...")
        chunk = b'{"name":"get_weather","toolUseId":"call_123"}'

        print("Действие: Парсинг chunk...")
        events = aws_event_parser.feed(chunk)

        print(f"Результат: {events}")
        print(f"current_tool_call: {aws_event_parser.current_tool_call}")

        # tool_start не возвращает событие, но создаёт current_tool_call
        assert aws_event_parser.current_tool_call is not None
        assert aws_event_parser.current_tool_call["function"]["name"] == "get_weather"

    def test_parses_tool_input_event(self, aws_event_parser):
        """
        Что он делает: Проверяет парсинг input для tool call.
        Цель: Убедиться, что input добавляется к current_tool_call.
        """
        print("Настройка: Начало tool call...")
        aws_event_parser.feed(b'{"name":"func","toolUseId":"call_1"}')

        print("Действие: Парсинг input...")
        aws_event_parser.feed(b'{"input":"{\\"key\\": \\"value\\"}"}')

        print(f"current_tool_call: {aws_event_parser.current_tool_call}")
        assert (
            '{"key": "value"}'
            in aws_event_parser.current_tool_call["function"]["arguments"]
        )

    def test_parses_tool_stop_event(self, aws_event_parser):
        """
        Что он делает: Проверяет завершение tool call.
        Цель: Убедиться, что tool call добавляется в список.
        """
        print("Настройка: Полный tool call...")
        aws_event_parser.feed(b'{"name":"func","toolUseId":"call_1"}')
        aws_event_parser.feed(b'{"input":"{}"}')

        print("Действие: Парсинг stop...")
        aws_event_parser.feed(b'{"stop":true}')

        print(f"tool_calls: {aws_event_parser.tool_calls}")
        assert len(aws_event_parser.tool_calls) == 1
        assert aws_event_parser.current_tool_call is None

    def test_get_tool_calls_returns_all(self, aws_event_parser):
        """
        Что он делает: Проверяет получение всех tool calls.
        Цель: Убедиться, что get_tool_calls возвращает завершённые calls.
        """
        print("Настройка: Несколько tool calls...")
        aws_event_parser.feed(b'{"name":"func1","toolUseId":"call_1"}')
        aws_event_parser.feed(b'{"stop":true}')
        aws_event_parser.feed(b'{"name":"func2","toolUseId":"call_2"}')
        aws_event_parser.feed(b'{"stop":true}')

        print("Действие: Получение tool calls...")
        tool_calls = aws_event_parser.get_tool_calls()

        print(f"Результат: {tool_calls}")
        assert len(tool_calls) == 2

    def test_get_tool_calls_finalizes_current(self, aws_event_parser):
        """
        Что он делает: Проверяет завершение незавершённого tool call.
        Цель: Убедиться, что get_tool_calls завершает current_tool_call.
        """
        print("Настройка: Незавершённый tool call...")
        aws_event_parser.feed(b'{"name":"func","toolUseId":"call_1"}')

        print("Действие: Получение tool calls...")
        tool_calls = aws_event_parser.get_tool_calls()

        print(f"Результат: {tool_calls}")
        assert len(tool_calls) == 1
        assert aws_event_parser.current_tool_call is None


class TestAwsEventStreamParserReset:
    """Тесты метода reset."""

    def test_reset_clears_state(self, aws_event_parser):
        """
        Что он делает: Проверяет сброс состояния парсера.
        Цель: Убедиться, что reset очищает все данные.
        """
        print("Настройка: Заполнение парсера данными...")
        aws_event_parser.feed(b'{"content":"test"}')
        aws_event_parser.feed(b'{"name":"func","toolUseId":"call_1"}')

        print("Действие: Сброс парсера...")
        aws_event_parser.reset()

        print("Проверка: Все данные очищены...")
        assert aws_event_parser.buffer == ""
        assert aws_event_parser.last_content is None
        assert aws_event_parser.current_tool_call is None
        assert aws_event_parser.tool_calls == []


class TestAwsEventStreamParserFinalizeToolCall:
    """Тесты метода _finalize_tool_call для обработки разных типов input."""

    def test_finalize_with_string_arguments(self, aws_event_parser):
        """
        Что он делает: Проверяет финализацию tool call со строковыми аргументами.
        Цель: Убедиться, что строка JSON парсится и сериализуется обратно.
        """
        print("Настройка: Tool call со строковыми аргументами...")
        aws_event_parser.current_tool_call = {
            "id": "call_1",
            "type": "function",
            "function": {"name": "test_func", "arguments": '{"key": "value"}'},
        }

        print("Действие: Финализация tool call...")
        aws_event_parser._finalize_tool_call()

        print(f"Результат: {aws_event_parser.tool_calls}")
        assert len(aws_event_parser.tool_calls) == 1
        assert (
            aws_event_parser.tool_calls[0]["function"]["arguments"]
            == '{"key": "value"}'
        )

    def test_finalize_with_dict_arguments(self, aws_event_parser):
        """
        Что он делает: Проверяет финализацию tool call с dict аргументами.
        Цель: Убедиться, что dict сериализуется в JSON строку.
        """
        print("Настройка: Tool call с dict аргументами...")
        aws_event_parser.current_tool_call = {
            "id": "call_2",
            "type": "function",
            "function": {
                "name": "test_func",
                "arguments": {"location": "Moscow", "units": "celsius"},
            },
        }

        print("Действие: Финализация tool call...")
        aws_event_parser._finalize_tool_call()

        print(f"Результат: {aws_event_parser.tool_calls}")
        assert len(aws_event_parser.tool_calls) == 1

        args = aws_event_parser.tool_calls[0]["function"]["arguments"]
        print(f"Аргументы: {args}")
        assert isinstance(args, str)
        assert "Moscow" in args
        assert "celsius" in args

    def test_finalize_with_empty_string_arguments(self, aws_event_parser):
        """
        Что он делает: Проверяет финализацию tool call с пустой строкой аргументов.
        Цель: Убедиться, что пустая строка заменяется на "{}".
        """
        print("Настройка: Tool call с пустой строкой аргументов...")
        aws_event_parser.current_tool_call = {
            "id": "call_3",
            "type": "function",
            "function": {"name": "test_func", "arguments": ""},
        }

        print("Действие: Финализация tool call...")
        aws_event_parser._finalize_tool_call()

        print(f"Результат: {aws_event_parser.tool_calls}")
        assert len(aws_event_parser.tool_calls) == 1
        assert aws_event_parser.tool_calls[0]["function"]["arguments"] == "{}"

    def test_finalize_with_whitespace_only_arguments(self, aws_event_parser):
        """
        Что он делает: Проверяет финализацию tool call с пробельными аргументами.
        Цель: Убедиться, что строка из пробелов заменяется на "{}".
        """
        print("Настройка: Tool call с пробельными аргументами...")
        aws_event_parser.current_tool_call = {
            "id": "call_4",
            "type": "function",
            "function": {"name": "test_func", "arguments": "   "},
        }

        print("Действие: Финализация tool call...")
        aws_event_parser._finalize_tool_call()

        print(f"Результат: {aws_event_parser.tool_calls}")
        assert len(aws_event_parser.tool_calls) == 1
        assert aws_event_parser.tool_calls[0]["function"]["arguments"] == "{}"

    def test_finalize_with_invalid_json_arguments(self, aws_event_parser):
        """
        Что он делает: Проверяет финализацию tool call с невалидным JSON.
        Цель: Убедиться, что невалидный JSON заменяется на "{}".
        """
        print("Настройка: Tool call с невалидным JSON...")
        aws_event_parser.current_tool_call = {
            "id": "call_5",
            "type": "function",
            "function": {"name": "test_func", "arguments": "not valid json {"},
        }

        print("Действие: Финализация tool call...")
        aws_event_parser._finalize_tool_call()

        print(f"Результат: {aws_event_parser.tool_calls}")
        assert len(aws_event_parser.tool_calls) == 1
        assert aws_event_parser.tool_calls[0]["function"]["arguments"] == "{}"

    def test_finalize_with_none_current_tool_call(self, aws_event_parser):
        """
        Что он делает: Проверяет финализацию когда current_tool_call is None.
        Цель: Убедиться, что ничего не происходит при None.
        """
        print("Настройка: current_tool_call = None...")
        aws_event_parser.current_tool_call = None

        print("Действие: Финализация tool call...")
        aws_event_parser._finalize_tool_call()

        print(f"Результат: {aws_event_parser.tool_calls}")
        assert len(aws_event_parser.tool_calls) == 0

    def test_finalize_clears_current_tool_call(self, aws_event_parser):
        """
        Что он делает: Проверяет, что финализация очищает current_tool_call.
        Цель: Убедиться, что после финализации current_tool_call = None.
        """
        print("Настройка: Tool call...")
        aws_event_parser.current_tool_call = {
            "id": "call_6",
            "type": "function",
            "function": {"name": "test_func", "arguments": "{}"},
        }

        print("Действие: Финализация tool call...")
        aws_event_parser._finalize_tool_call()

        print(
            f"current_tool_call после финализации: {aws_event_parser.current_tool_call}"
        )
        assert aws_event_parser.current_tool_call is None


class TestAwsEventStreamParserEdgeCases:
    """Тесты граничных случаев."""

    def test_handles_followup_prompt(self, aws_event_parser):
        """
        Что он делает: Проверяет игнорирование followupPrompt.
        Цель: Убедиться, что followupPrompt не создаёт событие.
        """
        print("Настройка: Chunk с followupPrompt...")
        chunk = b'{"content":"text","followupPrompt":"suggestion"}'

        print("Действие: Парсинг chunk...")
        events = aws_event_parser.feed(chunk)

        print(f"Результат: {events}")
        assert len(events) == 0  # followupPrompt игнорируется

    def test_handles_mixed_events(self, aws_event_parser):
        """
        Что он делает: Проверяет парсинг смешанных событий.
        Цель: Убедиться, что разные типы событий обрабатываются вместе.
        """
        print("Настройка: Chunk со смешанными событиями...")
        chunk = b'{"content":"Hello"}{"usage":1.0}{"contextUsagePercentage":50}'

        print("Действие: Парсинг chunk...")
        events = aws_event_parser.feed(chunk)

        print(f"Результат: {events}")
        assert len(events) == 3
        assert events[0]["type"] == "content"
        assert events[1]["type"] == "usage"
        assert events[2]["type"] == "context_usage"

    def test_handles_garbage_between_events(self, aws_event_parser):
        """
        Что он делает: Проверяет обработку мусора между событиями.
        Цель: Убедиться, что парсер находит JSON среди мусора.
        """
        print("Настройка: Chunk с мусором между JSON...")
        chunk = b'garbage{"content":"valid"}more garbage{"usage":1}'

        print("Действие: Парсинг chunk...")
        events = aws_event_parser.feed(chunk)

        print(f"Результат: {events}")
        assert len(events) == 2

    def test_handles_empty_chunk(self, aws_event_parser):
        """
        Что он делает: Проверяет обработку пустого chunk.
        Цель: Убедиться, что пустой chunk не вызывает ошибок.
        """
        print("Настройка: Пустой chunk...")

        print("Действие: Парсинг пустого chunk...")
        events = aws_event_parser.feed(b"")

        print(f"Сравниваем результат: Ожидалось [], Получено {events}")
        assert events == []
