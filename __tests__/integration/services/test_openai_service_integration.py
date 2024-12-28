import pytest
from datetime import datetime
import os
from openai import AuthenticationError, APIError

from domain.robo import RoboConfig
from domain.exceptions import (
    RoboRateLimitError,
    RoboAPIError,
)
from services.OpenAIService import OpenAIService

pytestmark = pytest.mark.integration


@pytest.fixture
def robo_config():
    """Create a RoboConfig instance with real API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip(
            "OPENAI_API_KEY environment variable not set"
        )

    return RoboConfig(
        api_key=api_key,
        model_name="gpt-3.5-turbo",  # Using cheaper model for tests
        max_tokens=150,
        temperature=0.7,
        timeout_seconds=30,
    )


@pytest.fixture
def openai_service(robo_config):
    """Create an OpenAIService instance with real configuration."""
    return OpenAIService(robo_config)


class TestOpenAIServiceIntegration:
    """Integration test suite for OpenAIService."""

    def test_process_text_success(self, openai_service):
        """Test successful text processing with real API."""
        result = openai_service.process_text(
            "What is the capital of France?"
        )

        assert "Paris" in result.content.lower()
        assert result.model_name == "gpt-3.5-turbo"
        assert result.tokens_used > 0
        assert isinstance(result.created_at, datetime)
        assert "usage" in result.metadata
        assert result.metadata["usage"]["prompt_tokens"] > 0
        assert (
            result.metadata["usage"]["completion_tokens"]
            > 0
        )

    def test_health_check(self, openai_service):
        """Test health check with real API."""
        result = openai_service.health_check()
        assert result is True

    def test_invalid_api_key(self):
        """Test behavior with invalid API key."""
        config = RoboConfig(
            api_key="invalid-key",
            model_name="gpt-3.5-turbo",
            max_tokens=150,
            temperature=0.7,
            timeout_seconds=30,
        )
        service = OpenAIService(config)

        with pytest.raises(
            (AuthenticationError, APIError, RoboAPIError)
        ) as exc_info:
            service.process_text("Test content")
        error_msg = str(exc_info.value).lower()
        assert any(
            msg in error_msg
            for msg in [
                "invalid api key",
                "invalid_api_key",
                "incorrect api key",
                "authentication",
                "401",
            ]
        )

    @pytest.mark.skip(
        reason="Only run manually to avoid rate limits"
    )
    def test_rate_limit_handling(self, openai_service):
        """Test handling of rate limits with real API.

        This test is skipped by default to avoid hitting rate limits.
        Run manually with: pytest -v -m integration --no-skip
        """
        # Make multiple rapid requests to trigger rate limit
        with pytest.raises(RoboRateLimitError):
            for _ in range(
                100
            ):  # Adjust based on your rate limits
                openai_service.process_text("Test content")
