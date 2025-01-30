"""Unit tests for OpenAIService."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timezone
import json
from dateutil.tz import UTC

from domain.robo import (
    RoboConfig,
    RoboProcessingResult,
)
from domain.exceptions import (
    RoboRateLimitError,
    RoboAPIError,
    RoboValidationError,
)
from services.OpenAIService import (
    OpenAIService,
    PROCESS_TASK_FUNCTION,
)


@pytest.fixture
def mock_openai(mocker):
    """Mock OpenAI client."""
    # Create the function mock first
    function_mock = mocker.MagicMock()
    function_mock.name = (
        "process_task"  # Set as attribute instead of mock
    )
    function_mock.arguments = json.dumps(
        {
            "title": "Test Task",
            "formatted": "Task content",
            "priority": "high",
            "due_date": "2025-02-01",
        }
    )

    # Create the tool call mock
    tool_call_mock = mocker.MagicMock()
    tool_call_mock.function = function_mock

    # Create the message mock
    message_mock = mocker.MagicMock()
    message_mock.tool_calls = [tool_call_mock]

    # Create the choice mock
    choice_mock = mocker.MagicMock()
    choice_mock.message = message_mock

    # Create the usage mock
    usage_mock = mocker.MagicMock()
    usage_mock.prompt_tokens = 10
    usage_mock.completion_tokens = 20
    usage_mock.total_tokens = 30

    # Create the main mock
    mock = mocker.MagicMock()
    mock.chat.completions.create.return_value = (
        mocker.MagicMock(
            choices=[choice_mock],
            model="gpt-4",
            usage=usage_mock,
            created=int(datetime.now(UTC).timestamp()),
        )
    )
    return mock


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter."""
    mock = MagicMock()
    mock.try_acquire.return_value = True
    mock.wait_for_capacity.return_value = True
    return mock


@pytest.fixture
def robo_config():
    """Create a test RoboConfig instance."""
    return RoboConfig(
        api_key="test-key",
        model_name="gpt-4",
        max_retries=3,
        timeout_seconds=30,
        temperature=0.7,
        max_tokens=150,
        task_enrichment_prompt="Format this task",
        task_extraction_prompt="Extract tasks from this note",
    )


@pytest.fixture
def openai_service(
    robo_config, mock_openai, mock_rate_limiter
):
    """Create an OpenAIService instance with mocks."""
    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        return OpenAIService(robo_config)


@pytest.fixture
def mock_openai_response():
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message.content = "Test response"
    response.model = "gpt-4"
    response.created = int(
        datetime.now(timezone.utc).timestamp()
    )
    response.usage.prompt_tokens = 50
    response.usage.completion_tokens = 50
    response.usage.total_tokens = 100
    return response


@pytest.fixture
def mock_openai_function_response(mocker):
    """Create a mock OpenAI function response."""
    response_mock = mocker.MagicMock()

    # Create tool call mock
    tool_call_mock = mocker.MagicMock()
    tool_call_mock.function.name = "extract_tasks"
    tool_call_mock.function.arguments = (
        '{"tasks": [{"content": "Test task"}]}'
    )

    # Set up response structure
    response_mock.choices = [mocker.MagicMock()]
    response_mock.choices[0].message.tool_calls = [
        tool_call_mock
    ]

    return response_mock


class TestOpenAIService:
    """Test suite for OpenAIService."""

    def test_process_text_success(
        self, openai_service, mock_openai
    ):
        """Test successful text processing."""
        # Update mock for non-tool response
        mock_openai.chat.completions.create.return_value = (
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content="Test response",
                            tool_calls=None,
                        ),
                        finish_reason="stop",
                    )
                ],
                model="gpt-4",
                created=1677858242,
                usage=MagicMock(
                    prompt_tokens=10,
                    completion_tokens=20,
                    total_tokens=30,
                ),
            )
        )

        result = openai_service.process_text("Test content")

        assert isinstance(result, RoboProcessingResult)
        assert result.content == "Test response"
        assert result.model_name == "gpt-4"
        assert result.tokens_used == 30
        assert isinstance(result.created_at, datetime)
        assert result.metadata == {
            "model": "gpt-4",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }

        # Verify OpenAI API was called correctly
        call_args = (
            mock_openai.chat.completions.create.call_args[1]
        )
        assert call_args["model"] == "gpt-4"
        assert call_args["max_tokens"] == 150
        assert call_args["temperature"] == 0.7
        assert call_args["timeout"] == 30

        # Verify messages structure
        messages = call_args["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "Current datetime:" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Test content"

    def test_rate_limit_failure(
        self, robo_config, mock_openai
    ):
        """Test rate limit handling."""
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.try_acquire.return_value = False

        with patch(
            "services.OpenAIService.OpenAI",
            return_value=mock_openai,
        ), patch(
            "services.OpenAIService.RateLimiter",
            return_value=mock_rate_limiter,
        ):
            service = OpenAIService(robo_config)

            with pytest.raises(RoboRateLimitError):
                service.process_text("Test content")

            # Verify OpenAI API was not called
            mock_openai.chat.completions.create.assert_not_called()

    def test_api_error_handling(
        self, robo_config, mock_rate_limiter
    ):
        """Test API error handling."""
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.side_effect = (
            Exception("API Error")
        )

        with patch(
            "services.OpenAIService.OpenAI",
            return_value=mock_openai,
        ), patch(
            "services.OpenAIService.RateLimiter",
            return_value=mock_rate_limiter,
        ):
            service = OpenAIService(robo_config)

            with pytest.raises(RoboAPIError):
                service.process_text("Test content")

    def test_health_check_success(
        self, openai_service, mock_openai
    ):
        """Test successful health check."""
        assert openai_service.health_check() is True
        mock_openai.chat.completions.create.assert_called_once()

    def test_health_check_failure(
        self, robo_config, mock_rate_limiter
    ):
        """Test health check failure."""
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.side_effect = (
            Exception("API Error")
        )

        with patch(
            "services.OpenAIService.OpenAI",
            return_value=mock_openai,
        ), patch(
            "services.OpenAIService.RateLimiter",
            return_value=mock_rate_limiter,
        ):
            service = OpenAIService(robo_config)
            assert service.health_check() is False

    def test_estimate_tokens(self, openai_service):
        """Test token estimation logic."""
        # Test with default buffer
        assert (
            openai_service._estimate_tokens("test") == 101
        )  # 1 token + 100 buffer

        # Test with custom buffer
        assert (
            openai_service._estimate_tokens(
                "test", buffer=50
            )
            == 51
        )

        # Test with longer text
        text = "a" * 400  # Should be roughly 100 tokens
        assert (
            openai_service._estimate_tokens(text) == 200
        )  # 100 tokens + 100 buffer

        # Test with empty string
        assert (
            openai_service._estimate_tokens("") == 100
        )  # Just buffer

        # Test with very large text
        large_text = (
            "a" * 4000
        )  # Should be roughly 1000 tokens
        assert (
            openai_service._estimate_tokens(large_text)
            == 1100
        )  # 1000 tokens + 100 buffer

        # Test with special characters
        special_text = "!@#$%^&*()"
        assert (
            openai_service._estimate_tokens(special_text)
            == 102
        )  # ~2 tokens + 100 buffer

    def test_validate_tool_response(
        self, openai_service, mock_openai
    ):
        """Test response validation with various scenarios."""
        # Test valid response
        response = mock_openai.chat.completions.create()
        result = openai_service._validate_tool_response(
            response, ["title", "formatted"], "process_task"
        )
        assert result["title"] == "Test Task"
        assert result["formatted"] == "Task content"
        assert (
            result["priority"] == "high"
        )  # Verify optional fields
        assert result["due_date"] == "2025-02-01"

        # Test missing choices
        invalid_response = MagicMock(choices=[])
        with pytest.raises(RoboAPIError) as exc_info:
            openai_service._validate_tool_response(
                invalid_response, ["title"], "process_task"
            )
        assert (
            str(exc_info.value)
            == "No choices in OpenAI response"
        )

        # Test missing tool calls
        invalid_response = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(tool_calls=None)
                )
            ]
        )
        with pytest.raises(RoboAPIError) as exc_info:
            openai_service._validate_tool_response(
                invalid_response, ["title"], "process_task"
            )
        assert (
            str(exc_info.value)
            == "No tool calls in OpenAI response"
        )

        # Test invalid JSON
        invalid_response = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        tool_calls=[
                            MagicMock(
                                function=MagicMock(
                                    name="process_task",
                                    arguments="invalid json",
                                )
                            )
                        ]
                    )
                )
            ]
        )
        with pytest.raises(RoboAPIError) as exc_info:
            openai_service._validate_tool_response(
                invalid_response,
                ["title"],
                "process_task",
            )
        assert "Invalid JSON in OpenAI response" in str(
            exc_info.value
        )

        # Test wrong function name
        invalid_response = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        tool_calls=[
                            MagicMock(
                                function=MagicMock(
                                    name="wrong_function",
                                    arguments='{"title": "Test"}',
                                )
                            )
                        ]
                    )
                )
            ]
        )
        with pytest.raises(RoboAPIError) as exc_info:
            openai_service._validate_tool_response(
                invalid_response, ["title"], "process_task"
            )
        assert (
            str(exc_info.value)
            == "Invalid tool response format"
        )

    def test_process_task_success(
        self, openai_service, mock_openai
    ):
        """Test successful task processing."""
        result = openai_service.process_task(
            "Create a new feature"
        )

        assert isinstance(result, RoboProcessingResult)
        assert result.content == "Task content"
        assert result.metadata["title"] == "Test Task"
        assert result.metadata["priority"] == "high"
        assert result.metadata["due_date"] == "2025-02-01"
        assert result.model_name == "gpt-4"
        assert result.tokens_used == 30

        # Verify OpenAI API was called correctly
        mock_openai.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Format this task",
                },
                {
                    "role": "user",
                    "content": "Create a new feature",
                },
            ],
            tools=[
                {
                    "type": "function",
                    "function": PROCESS_TASK_FUNCTION,
                }
            ],
            tool_choice={
                "type": "function",
                "function": {"name": "process_task"},
            },
            temperature=0.7,
            max_tokens=150,
            timeout=30,
        )

    def test_process_task_empty_content(
        self, openai_service
    ):
        """Test validation of empty content."""
        with pytest.raises(
            RoboValidationError,
            match="Task content cannot be empty",
        ):
            openai_service.process_task("")

    def test_process_task_rate_limit(
        self, robo_config, mock_openai
    ):
        """Test rate limiting behavior."""
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.wait_for_capacity.return_value = (
            False
        )

        with patch(
            "services.OpenAIService.OpenAI",
            return_value=mock_openai,
        ), patch(
            "services.OpenAIService.RateLimiter",
            return_value=mock_rate_limiter,
        ):
            service = OpenAIService(robo_config)

            with pytest.raises(RoboRateLimitError):
                service.process_task("Test content")

            # Verify OpenAI API was not called
            mock_openai.chat.completions.create.assert_not_called()

    def test_process_task_api_error(
        self, robo_config, mock_rate_limiter
    ):
        """Test API error handling."""
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.side_effect = (
            Exception("API Error")
        )

        with patch(
            "services.OpenAIService.OpenAI",
            return_value=mock_openai,
        ), patch(
            "services.OpenAIService.RateLimiter",
            return_value=mock_rate_limiter,
        ):
            service = OpenAIService(robo_config)

            with pytest.raises(RoboAPIError):
                service.process_task("Test content")

    def test_extract_tasks_success(
        self, openai_service, mock_openai_function_response
    ):
        """Test successful task extraction."""
        with patch.object(
            openai_service.client.chat.completions,
            "create",
            return_value=mock_openai_function_response,
        ):
            result = openai_service.extract_tasks(
                "Test note content"
            )

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["content"] == "Test task"

    def test_extract_tasks_no_tasks(
        self, openai_service, mock_openai_function_response
    ):
        """Test task extraction with no tasks found."""
        mock_openai_function_response.choices[
            0
        ].message.tool_calls[
            0
        ].function.arguments = '{"tasks": []}'

        with patch.object(
            openai_service.client.chat.completions,
            "create",
            return_value=mock_openai_function_response,
        ):
            result = openai_service.extract_tasks(
                "Test note content"
            )

            assert isinstance(result, list)
            assert len(result) == 0

    def test_extract_tasks_invalid_response(
        self, openai_service, mock_openai_function_response
    ):
        """Test task extraction with invalid API response."""
        mock_openai_function_response.choices[
            0
        ].message.tool_calls[
            0
        ].function.arguments = "invalid json"

        with patch.object(
            openai_service.client.chat.completions,
            "create",
            return_value=mock_openai_function_response,
        ):
            with pytest.raises(RoboValidationError):
                openai_service.extract_tasks(
                    "Test note content"
                )

    def test_extract_tasks_missing_tasks_field(
        self, openai_service, mock_openai_function_response
    ):
        """Test task extraction with missing tasks field in response."""
        mock_openai_function_response.choices[
            0
        ].message.tool_calls[
            0
        ].function.arguments = '{"other": []}'

        with patch.object(
            openai_service.client.chat.completions,
            "create",
            return_value=mock_openai_function_response,
        ):
            with pytest.raises(RoboValidationError):
                openai_service.extract_tasks(
                    "Test note content"
                )

    def test_extract_tasks_wrong_function_name(
        self, openai_service, mock_openai_function_response
    ):
        """Test task extraction with wrong function name in response."""
        mock_openai_function_response.choices[
            0
        ].message.tool_calls[
            0
        ].function.name = "wrong_function"

        with patch.object(
            openai_service.client.chat.completions,
            "create",
            return_value=mock_openai_function_response,
        ):
            with pytest.raises(RoboValidationError):
                openai_service.extract_tasks(
                    "Test note content"
                )

    def test_extract_tasks_multiple_tasks(
        self, openai_service, mock_openai_function_response
    ):
        """Test task extraction with multiple tasks."""
        mock_openai_function_response.choices[
            0
        ].message.tool_calls[
            0
        ].function.arguments = """
        {
            "tasks": [
                {"content": "Task 1"},
                {"content": "Task 2"},
                {"content": "Task 3"}
            ]
        }
        """

        with patch.object(
            openai_service.client.chat.completions,
            "create",
            return_value=mock_openai_function_response,
        ):
            result = openai_service.extract_tasks(
                "Test note content"
            )

            assert isinstance(result, list)
            assert len(result) == 3
            assert result[0]["content"] == "Task 1"
            assert result[1]["content"] == "Task 2"
            assert result[2]["content"] == "Task 3"

    def test_get_datetime_context(self, openai_service):
        """Test datetime context generation."""
        context = openai_service._get_datetime_context()

        # Verify all required components are present
        assert "Current datetime:" in context
        assert "Day:" in context
        assert "Date:" in context
        assert "Time:" in context
        assert "UTC" in context

    def test_prepare_messages_with_system_prompt(
        self, openai_service
    ):
        """Test message preparation with system prompt."""
        messages = openai_service._prepare_messages(
            content="test content",
            system_prompt="test system prompt",
        )

        assert (
            len(messages) == 3
        )  # datetime context + system prompt + user content
        assert messages[0]["role"] == "system"
        assert "Current datetime:" in messages[0]["content"]
        assert messages[1]["role"] == "system"
        assert (
            messages[1]["content"] == "test system prompt"
        )
        assert messages[2]["role"] == "user"
        assert messages[2]["content"] == "test content"

    def test_prepare_messages_without_system_prompt(
        self, openai_service
    ):
        """Test message preparation without system prompt."""
        messages = openai_service._prepare_messages(
            content="test content"
        )

        assert (
            len(messages) == 2
        )  # datetime context + user content
        assert messages[0]["role"] == "system"
        assert "Current datetime:" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "test content"

    @patch("services.OpenAIService.datetime")
    def test_datetime_context_in_api_calls(
        self, mock_datetime, openai_service, mock_openai
    ):
        """Test that datetime context is included in API calls."""
        # Mock datetime to have a fixed value
        mock_now = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
        mock_datetime.now.return_value = mock_now

        # Test process_text
        openai_service.process_text("test content")

        # Verify datetime context was included in the API call
        actual_messages = (
            mock_openai.chat.completions.create.call_args[
                1
            ]["messages"]
        )
        assert any(
            msg["role"] == "system"
            and "2024-01-01" in msg["content"]
            for msg in actual_messages
        )
