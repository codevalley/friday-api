import logging
from datetime import datetime, UTC

from openai import AsyncOpenAI

from domain.exceptions import (
    RoboAPIError,
    RoboConfigError,
    RoboRateLimitError,
    RoboValidationError,
)
from domain.robo import (
    RoboConfig,
    RoboProcessingResult,
)
from services.RateLimiter import RateLimiter
from utils.retry import with_retry

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI's API."""

    def __init__(self, config: RoboConfig):
        """Initialize the OpenAI service.

        Args:
            config: Configuration for the service
        """
        if not config.api_key:
            raise RoboConfigError(
                "OpenAI API key is required"
            )

        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            timeout=config.timeout_seconds,
        )
        self.rate_limiter = RateLimiter(
            requests_per_minute=60,  # Default OpenAI RPM limit
            tokens_per_minute=90_000,  # Default OpenAI TPM limit
        )

    @with_retry(
        max_retries=3,
        retry_on=(RoboAPIError,),
        exclude_on=(
            RoboConfigError,
            RoboValidationError,
            RoboRateLimitError,
        ),
    )
    async def process_text(
        self, content: str
    ) -> RoboProcessingResult:
        """Process text content using OpenAI's API."""
        try:
            # Estimate token usage (rough estimate: 4 chars ≈ 1 token)
            estimated_tokens = (
                len(content) // 4
            ) + 100  # Buffer for response

            # Wait for rate limit capacity
            if not await self.rate_limiter.wait_for_capacity(
                estimated_tokens
            ):
                raise RoboRateLimitError(
                    "Failed to acquire capacity after retries"
                )

            # Make the API call
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant.",
                    },
                    {"role": "user", "content": content},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens or 150,
            )

            # Record actual token usage
            await self.rate_limiter.record_usage(
                datetime.fromtimestamp(
                    response.created, UTC
                ),
                response.usage.total_tokens,
            )

            return RoboProcessingResult(
                content=response.choices[0].message.content,
                metadata={
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                },
                tokens_used=response.usage.total_tokens,
                model_name=response.model,
                created_at=datetime.fromtimestamp(
                    response.created, UTC
                ),
            )

        except Exception as e:
            logger.error(
                f"Error processing text with OpenAI: {str(e)}"
            )
            if isinstance(e, RoboRateLimitError):
                raise
            if "rate limit" in str(e).lower():
                raise RoboRateLimitError(
                    "OpenAI rate limit exceeded"
                )
            elif "invalid api key" in str(e).lower():
                raise RoboConfigError(
                    "Invalid OpenAI API key"
                )
            elif "billing" in str(e).lower():
                raise RoboConfigError(
                    "OpenAI billing issue"
                )
            else:
                raise RoboAPIError(
                    f"OpenAI API error: {str(e)}"
                )

    async def health_check(self) -> bool:
        """Check if the OpenAI service is healthy."""
        try:
            await self.process_text("test")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
