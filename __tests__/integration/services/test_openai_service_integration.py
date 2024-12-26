import asyncio
import pytest
from datetime import datetime
import os

from domain.robo import RoboConfig
from domain.exceptions import (
    RoboRateLimitError,
    RoboConfigError,
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

    async def test_process_text_success(
        self, openai_service
    ):
        """Test successful text processing with real API."""
        result = await openai_service.process_text(
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

    async def test_extract_entities_success(
        self, openai_service
    ):
        """Test successful entity extraction with real API."""
        text = (
            "I have a meeting in New York tomorrow at 2pm"
        )
        entity_types = ["dates", "locations", "times"]

        result = await openai_service.extract_entities(
            text, entity_types
        )

        assert isinstance(result, dict)
        assert "locations" in result
        assert any(
            "new york" in loc["text"].lower()
            for loc in result["locations"]
        )
        assert "dates" in result
        assert "times" in result
        assert any(
            "2pm" in time["text"].lower()
            for time in result["times"]
        )

    async def test_validate_content_success(
        self, openai_service
    ):
        """Test successful content validation with real API."""
        content = "This is a test message containing important information."
        rules = [
            "Must contain at least 5 words",
            "Must contain the word 'test'",
            "Must not contain profanity",
        ]

        result = await openai_service.validate_content(
            content, rules
        )
        assert result is True

    async def test_validate_content_failure(
        self, openai_service
    ):
        """Test content validation failure with real API."""
        content = "test"  # Too short
        rules = [
            "Must contain at least 5 words",
            "Must contain the word 'test'",
            "Must not contain profanity",
        ]

        result = await openai_service.validate_content(
            content, rules
        )
        assert result is False

    async def test_health_check(self, openai_service):
        """Test health check with real API."""
        result = await openai_service.health_check()
        assert result is True

    async def test_invalid_api_key(self):
        """Test behavior with invalid API key."""
        config = RoboConfig(
            api_key="invalid-key",
            model_name="gpt-3.5-turbo",
            max_tokens=150,
            temperature=0.7,
            timeout_seconds=30,
        )
        service = OpenAIService(config)

        with pytest.raises(RoboConfigError) as exc_info:
            await service.process_text("Test content")
        assert (
            "invalid api key" in str(exc_info.value).lower()
        )

    @pytest.mark.skip(
        reason="Only run manually to avoid rate limits"
    )
    async def test_rate_limit_handling(
        self, openai_service
    ):
        """Test handling of rate limits with real API.

        This test is skipped by default to avoid hitting rate limits.
        Run manually with: pytest -v -m integration --no-skip
        """
        # Make multiple rapid requests to trigger rate limit
        tasks = []
        for _ in range(
            100
        ):  # Adjust based on your rate limits
            tasks.append(
                openai_service.process_text("Test content")
            )

        with pytest.raises(RoboRateLimitError):
            await asyncio.gather(*tasks)
