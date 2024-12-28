import pytest
from datetime import datetime, UTC
from unittest.mock import MagicMock, patch
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
)
from openai.types.chat.chat_completion import Choice
from openai.types import CompletionUsage

from domain.robo import RoboConfig
from domain.exceptions import (
    RoboConfigError,
    RoboAPIError,
    RoboRateLimitError,
)
from services.OpenAIService import OpenAIService


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter."""
    mock_limiter = MagicMock()
    mock_limiter.wait_for_capacity = MagicMock(
        return_value=True
    )
    mock_limiter.record_usage = MagicMock()
    return mock_limiter


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return RoboConfig(
        api_key="test_key",
        model_name="test_model",
        max_retries=3,
        timeout_seconds=30,
        temperature=0.7,
        max_tokens=150,
    )


def test_init_with_valid_config(test_config):
    """Test initialization with valid configuration."""
    service = OpenAIService(test_config)
    assert service.config == test_config
    assert service.client is not None


def test_init_without_api_key():
    """Test initialization without API key."""
    config = RoboConfig(api_key="", model_name="test_model")
    with pytest.raises(RoboConfigError) as exc_info:
        OpenAIService(config)
    assert "OpenAI API key is required" in str(
        exc_info.value
    )


def test_process_text_success(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test successful text processing."""
    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)

        # Create a proper mock response
        mock_message = ChatCompletionMessage(
            content="Test response",
            role="assistant",
            function_call=None,
            tool_calls=None,
        )
        mock_usage = CompletionUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        )
        mock_choice = Choice(
            finish_reason="stop",
            index=0,
            message=mock_message,
            logprobs=None,
        )
        created_time = int(datetime.now(UTC).timestamp())
        mock_response = ChatCompletion(
            id="test_id",
            choices=[mock_choice],
            created=created_time,
            model="test_model",
            object="chat.completion",
            usage=mock_usage,
            system_fingerprint=None,
        )

        mock_openai_client.chat.completions.create = (
            MagicMock(return_value=mock_response)
        )

        result = service.process_text("Test input")

        assert result.content == "Test response"
        assert result.model_name == "test_model"
        assert result.tokens_used == 30
        assert isinstance(result.created_at, datetime)


def test_process_text_rate_limit_error(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test rate limit error handling."""
    mock_rate_limiter.wait_for_capacity = MagicMock(
        return_value=False
    )

    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)

        with pytest.raises(RoboRateLimitError) as exc_info:
            service.process_text("Test input")
        assert "Failed to acquire capacity" in str(
            exc_info.value
        )


def test_process_text_api_error(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test API error handling."""
    mock_openai_client.chat.completions.create = MagicMock(
        side_effect=Exception("API error")
    )

    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)

        with pytest.raises(RoboAPIError) as exc_info:
            service.process_text("Test input")
        assert "OpenAI API error" in str(exc_info.value)


def test_health_check_success(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test successful health check."""
    # Create a proper mock response
    mock_message = ChatCompletionMessage(
        content="Test",
        role="assistant",
        function_call=None,
        tool_calls=None,
    )
    mock_usage = CompletionUsage(
        prompt_tokens=2,
        completion_tokens=3,
        total_tokens=5,
    )
    mock_choice = Choice(
        finish_reason="stop",
        index=0,
        message=mock_message,
        logprobs=None,
    )
    created_time = int(datetime.now(UTC).timestamp())
    mock_response = ChatCompletion(
        id="test_id",
        choices=[mock_choice],
        created=created_time,
        model="test_model",
        object="chat.completion",
        usage=mock_usage,
        system_fingerprint=None,
    )

    mock_openai_client.chat.completions.create = MagicMock(
        return_value=mock_response
    )

    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)
        result = service.health_check()
        assert result is True


def test_health_check_failure(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test health check failure."""
    mock_openai_client.chat.completions.create = MagicMock(
        side_effect=Exception("API error")
    )

    with patch(
        "services.OpenAIService.OpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)
        result = service.health_check()
        assert result is False
