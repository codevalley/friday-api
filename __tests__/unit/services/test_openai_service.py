"""Unit tests for OpenAIService."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from domain.robo import RoboConfig, RoboResponse
from domain.exceptions import (
    RoboRateLimitError,
    RoboAPIError,
)
from services.OpenAIService import OpenAIService


@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client."""
    mock = MagicMock()
    mock.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(content="Test response"),
                finish_reason="stop",
            )
        ],
        model="gpt-3.5-turbo",
        created=1677858242,
        usage=MagicMock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        ),
    )
    return mock


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter."""
    mock = MagicMock()
    mock.try_acquire.return_value = True
    return mock


@pytest.fixture
def robo_config():
    """Create a test RoboConfig instance."""
    return RoboConfig(
        api_key="test-key",
        model_name="gpt-3.5-turbo",
        max_tokens=150,
        temperature=0.7,
        timeout_seconds=30,
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


class TestOpenAIService:
    """Test suite for OpenAIService."""

    def test_process_text_success(
        self, openai_service, mock_openai
    ):
        """Test successful text processing."""
        result = openai_service.process_text("Test content")

        assert isinstance(result, RoboResponse)
        assert result.content == "Test response"
        assert result.model_name == "gpt-3.5-turbo"
        assert result.tokens_used == 30
        assert isinstance(result.created_at, datetime)
        assert result.metadata == {
            "model": "gpt-3.5-turbo",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }

        # Verify OpenAI API was called correctly
        mock_openai.chat.completions.create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": "Test content",
                }
            ],
            max_tokens=150,
            temperature=0.7,
            timeout=30,
        )

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
