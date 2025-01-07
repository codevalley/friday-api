"""Unit tests for OpenAIService."""

import json
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
)
from openai.types import CompletionUsage

from domain.exceptions import (
    RoboAPIError,
    RoboConfigError,
    RoboRateLimitError,
)
from domain.robo import RoboConfig
from services.OpenAIService import (
    OpenAIService,
    ENRICH_NOTE_FUNCTION,
)


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    mock = Mock()
    mock.chat.completions.create = MagicMock()
    return mock


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter."""
    mock = Mock()
    mock.wait_for_capacity.return_value = True
    return mock


@pytest.fixture
def test_config():
    """Create test configuration."""
    return RoboConfig(
        api_key="test-key",
        model_name="test-model",
        temperature=0.7,
        max_tokens=150,
    )


def test_init_missing_api_key():
    """Test initialization with missing API key."""
    config = RoboConfig(api_key="", model_name="test-model")
    with pytest.raises(RoboConfigError) as exc_info:
        OpenAIService(config)
    assert "OpenAI API key is required" in str(
        exc_info.value
    )


def test_process_text_success(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test successful text processing."""
    # Setup mock response
    mock_response = Mock(spec=ChatCompletion)
    mock_message = Mock(spec=ChatCompletionMessage)
    mock_message.content = "Processed text"
    mock_response.choices = [Mock(message=mock_message)]
    mock_response.usage = Mock(
        spec=CompletionUsage,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )
    mock_response.model = "test-model"
    mock_response.created = 1704067200  # 2024-01-01

    # Setup service
    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)
        mock_openai_client.chat.completions.create.return_value = (
            mock_response
        )

        # Test
        result = service.process_text("Test text")

        # Verify
        assert result.content == "Processed text"
        assert result.tokens_used == 30
        assert result.model_name == "test-model"
        assert isinstance(result.created_at, datetime)


def test_process_text_note_enrichment(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test note enrichment processing."""
    # Setup mock response
    mock_response = Mock(spec=ChatCompletion)
    mock_message = Mock(spec=ChatCompletionMessage)
    mock_tool_call = Mock(
        spec=ChatCompletionMessageToolCall
    )
    mock_function = Mock()
    mock_function.name = "enrich_note"
    mock_function.arguments = json.dumps(
        {
            "title": "Test Note",
            "formatted": "- Point 1\n- Point 2",
        }
    )
    mock_tool_call.function = mock_function
    mock_message.tool_calls = [mock_tool_call]
    mock_response.choices = [Mock(message=mock_message)]
    mock_response.usage = Mock(
        spec=CompletionUsage,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )
    mock_response.model = "test-model"
    mock_response.created = 1704067200  # 2024-01-01

    # Setup service
    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)
        mock_openai_client.chat.completions.create.return_value = (
            mock_response
        )

        # Test
        result = service.process_text(
            "Raw note content",
            context={"type": "note_enrichment"},
        )

        # Verify
        assert result.content == "- Point 1\n- Point 2"
        assert result.metadata["title"] == "Test Note"
        assert result.tokens_used == 30
        assert result.model_name == "test-model"
        assert isinstance(result.created_at, datetime)

        # Verify function calling
        call_args = (
            mock_openai_client.chat.completions.create.call_args
        )
        assert "tools" in call_args.kwargs
        assert call_args.kwargs["tools"] == [
            {
                "type": "function",
                "function": ENRICH_NOTE_FUNCTION,
            }
        ]
        assert call_args.kwargs["tool_choice"] == {
            "type": "function",
            "function": {"name": "enrich_note"},
        }


def test_process_text_rate_limit_error(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test handling of rate limit errors."""
    # Setup rate limiter to deny capacity
    mock_rate_limiter.wait_for_capacity.return_value = False

    # Setup service
    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)

        # Test
        with pytest.raises(RoboRateLimitError) as exc_info:
            service.process_text("Test text")

        assert "capacity" in str(exc_info.value)


def test_process_text_api_error(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test handling of API errors."""
    # Setup mock to raise error
    mock_openai_client.chat.completions.create.side_effect = Exception(
        "API Error"
    )

    # Setup service
    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)

        # Test
        with pytest.raises(RoboAPIError) as exc_info:
            service.process_text("Test text")

        assert "API error" in str(exc_info.value)


def test_health_check_success(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test successful health check."""
    # Setup mock response
    mock_response = Mock(spec=ChatCompletion)
    mock_message = Mock(spec=ChatCompletionMessage)
    mock_message.content = "OK"
    mock_response.choices = [Mock(message=mock_message)]
    mock_response.usage = Mock(
        spec=CompletionUsage,
        prompt_tokens=1,
        completion_tokens=1,
        total_tokens=2,
    )
    mock_response.model = "test-model"
    mock_response.created = 1704067200

    # Setup service
    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)
        mock_openai_client.chat.completions.create.return_value = (
            mock_response
        )

        # Test
        assert service.health_check() is True


def test_health_check_failure(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test failed health check."""
    # Setup mock to raise error
    mock_openai_client.chat.completions.create.side_effect = Exception(
        "API Error"
    )

    # Setup service
    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)

        # Test
        assert service.health_check() is False


def test_analyze_activity_schema_success(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test successful activity schema analysis."""
    # Setup mock response
    mock_response = Mock(spec=ChatCompletion)
    mock_message = Mock(spec=ChatCompletionMessage)
    mock_message.content = "Analyzed schema"
    mock_response.choices = [Mock(message=mock_message)]
    mock_response.usage = Mock(
        spec=CompletionUsage,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )
    mock_response.model = "test-model"
    mock_response.created = 1704067200  # 2024-01-01

    # Setup service
    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)
        mock_openai_client.chat.completions.create.return_value = (
            mock_response
        )

        # Test
        result = service.analyze_activity_schema({"type": "test"})

        # Verify
        assert result.content == "Analyzed schema"
        assert result.tokens_used == 30
        assert result.model_name == "test-model"
        assert isinstance(result.created_at, datetime)


def test_analyze_activity_schema_rate_limit_error(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test handling of rate limit errors during activity schema analysis."""
    # Setup rate limiter to deny capacity
    mock_rate_limiter.wait_for_capacity.return_value = False

    # Setup service
    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)

        # Test
        with pytest.raises(RoboRateLimitError) as exc_info:
            service.analyze_activity_schema({"type": "test"})

        assert "capacity" in str(exc_info.value)


def test_analyze_activity_schema_api_error(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test handling of API errors during activity schema analysis."""
    # Setup mock to raise error
    mock_openai_client.chat.completions.create.side_effect = Exception(
        "API Error"
    )

    # Setup service
    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)

        # Test
        with pytest.raises(RoboAPIError) as exc_info:
            service.analyze_activity_schema({"type": "test"})

        assert "API error" in str(exc_info.value)
