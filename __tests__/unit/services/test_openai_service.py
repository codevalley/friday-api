import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

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
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock()
    return mock_client


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter."""
    mock_limiter = AsyncMock()
    mock_limiter.wait_for_capacity = AsyncMock(
        return_value=True
    )
    mock_limiter.record_usage = AsyncMock()
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


@pytest.mark.asyncio
async def test_init_with_valid_config(test_config):
    """Test initialization with valid configuration."""
    service = OpenAIService(test_config)
    assert service.config == test_config
    assert service.client is not None


@pytest.mark.asyncio
async def test_init_without_api_key():
    """Test initialization without API key."""
    config = RoboConfig(api_key="", model_name="test_model")
    with pytest.raises(RoboConfigError) as exc_info:
        OpenAIService(config)
    assert "OpenAI API key is required" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_process_text_success(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test successful text processing."""
    with patch(
        "services.OpenAIService.AsyncOpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)

        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(content="Test response")
            )
        ]
        mock_response.model = "test_model"
        mock_response.usage = MagicMock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        )
        mock_response.created = datetime.now(
            UTC
        ).timestamp()

        mock_openai_client.chat.completions.create.return_value = (
            mock_response
        )

        result = await service.process_text("Test input")

        assert result.content == "Test response"
        assert result.model_name == "test_model"
        assert result.tokens_used == 30
        assert isinstance(result.created_at, datetime)


@pytest.mark.asyncio
async def test_process_text_rate_limit_error(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test rate limit error handling."""
    mock_rate_limiter.wait_for_capacity.return_value = False

    with patch(
        "services.OpenAIService.AsyncOpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)

        with pytest.raises(RoboRateLimitError) as exc_info:
            await service.process_text("Test input")
        assert "Failed to acquire capacity" in str(
            exc_info.value
        )


@pytest.mark.asyncio
async def test_process_text_api_error(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test API error handling."""
    error = Exception("API error")
    mock_openai_client.chat.completions.create.side_effect = (
        error
    )

    with patch(
        "services.OpenAIService.AsyncOpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)

        with pytest.raises(RoboAPIError) as exc_info:
            await service.process_text("Test input")
        assert "OpenAI API error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_health_check_success(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test successful health check."""
    mock_response = MagicMock()
    mock_response.usage = MagicMock(total_tokens=5)
    mock_response.created = datetime.now(UTC).timestamp()
    mock_openai_client.chat.completions.create.return_value = (
        mock_response
    )

    with patch(
        "services.OpenAIService.AsyncOpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)
        result = await service.health_check()
        assert result is True


@pytest.mark.asyncio
async def test_health_check_failure(
    test_config, mock_openai_client, mock_rate_limiter
):
    """Test health check failure."""
    error = Exception("API error")
    mock_openai_client.chat.completions.create.side_effect = (
        error
    )

    with patch(
        "services.OpenAIService.AsyncOpenAI",
        return_value=mock_openai_client,
    ), patch(
        "services.OpenAIService.RateLimiter",
        return_value=mock_rate_limiter,
    ):
        service = OpenAIService(test_config)
        result = await service.health_check()
        assert result is False
