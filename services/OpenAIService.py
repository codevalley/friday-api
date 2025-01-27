"""OpenAI service implementation."""

import logging
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List

from openai import OpenAI

from domain.robo import (
    RoboService,
    RoboConfig,
    RoboResponse,
)
from domain.exceptions import (
    RoboConfigError,
    RoboValidationError,
    RoboRateLimitError,
    RoboAPIError,
)
from services.RateLimiter import RateLimiter
from utils.retry import with_retry

logger = logging.getLogger(__name__)


class OpenAIService(RoboService):
    """OpenAI service implementation."""

    def __init__(self, config: RoboConfig):
        """Initialize OpenAI service.

        Args:
            config: Service configuration

        Raises:
            RoboConfigError: If configuration is invalid
        """
        if not config.api_key:
            raise RoboConfigError(
                "OpenAI API key is required"
            )

        self.config = config
        self.client = OpenAI(api_key=config.api_key)
        self.rate_limiter = RateLimiter(
            requests_per_minute=60,  # OpenAI default limit
            tokens_per_minute=90000,  # OpenAI default limit
        )

    @with_retry(
        max_retries=3,
        retry_on=(
            RoboAPIError,
            RoboRateLimitError,
        ),
        exclude_on=(
            RoboConfigError,
            RoboValidationError,
        ),
    )
    def process_text(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboResponse:
        """Process text using OpenAI's API.

        This is the default text processing method.
        For notes and tasks, use process_note and process_task respectively.

        Args:
            text: Text to process
            context: Optional context for processing

        Returns:
            RoboResponse: Processing result

        Raises:
            RoboAPIError: If API call fails
            RoboRateLimitError: If rate limit is exceeded
            RoboConfigError: If configuration is invalid
        """
        if not text:
            raise RoboValidationError(
                "Text cannot be empty"
            )

        try:
            # Estimate token usage (rough estimate: 4 chars ≈ 1 token)
            estimated_tokens = (
                len(text) // 4
            ) + self.config.max_tokens

            # Acquire rate limit capacity
            if not self.rate_limiter.try_acquire(
                estimated_tokens
            ):
                raise RoboRateLimitError(
                    "Failed to acquire capacity after retries"
                )

            # Default text processing
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "user", "content": text},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens or 150,
                timeout=self.config.timeout_seconds,
            )

            # Record actual token usage
            self.rate_limiter.record_usage(
                datetime.fromtimestamp(
                    response.created, UTC
                ),
                response.usage.total_tokens,
            )

            return RoboResponse(
                content=response.choices[0].message.content,
                metadata={
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,  # noqa: E501
                        "total_tokens": response.usage.total_tokens,
                    },
                },
                tokens_used=response.usage.total_tokens,
                model_name=response.model,
                created_at=datetime.fromtimestamp(
                    response.created, UTC
                ),
            )

        except RoboRateLimitError as e:
            # Re-raise rate limit errors directly
            raise e
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise RoboAPIError(
                f"OpenAI API error: {str(e)}"
            )

    @with_retry(
        max_retries=3,
        retry_on=(RoboAPIError,),
        exclude_on=(
            RoboConfigError,
            RoboValidationError,
        ),
    )
    def analyze_activity_schema(
        self, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate display templates for an activity based on its schema.

        This method analyzes a JSON Schema that defines an activity's
        data structure and generates templates for displaying the activity's
        title and content. The templates can use $variable_name syntax to
        reference schema variables that will be populated dynamically.

        Args:
            schema: JSON Schema defining activity data structure

        Returns:
            Dict containing:
                - title: A template for the activity title (< 50 chars)
                - formatted: A markdown template for the activity content

        Raises:
            RoboAPIError: If API call fails
            RoboValidationError: If schema is invalid
        """
        try:
            # Create prompt with schema analysis instructions
            prompt = (
                f"{self.config.activity_schema_prompt}\n\n"
                f"Schema: {schema}"
            )

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a UI/UX expert.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            # Extract templates from response
            content = response.choices[0].message.content

            # Parse response into title and formatted templates
            lines = content.strip().split("\n")
            title = ""
            formatted = ""

            for line in lines:
                if line.startswith("Title:"):
                    title = line.replace(
                        "Title:", ""
                    ).strip()
                elif line.startswith("Formatted:"):
                    formatted = line.replace(
                        "Formatted:", ""
                    ).strip()

            if not title or not formatted:
                raise RoboValidationError(
                    "Failed to extract templates from response"
                )

            return {
                "title": title,
                "formatted": formatted,
            }

        except Exception as e:
            logger.error(
                f"Error analyzing schema: {str(e)}"
            )
            raise RoboAPIError(
                f"OpenAI API error: {str(e)}"
            )

    def extract_entities(
        self, text: str, entity_types: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract specified entity types from text.

        Not implemented yet.
        """
        raise NotImplementedError

    def validate_content(
        self, content: str, validation_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate content against specified rules.

        Not implemented yet.
        """
        raise NotImplementedError

    def health_check(self) -> bool:
        """Check if the service is operational.

        Returns:
            bool: True if service is operational, False otherwise
        """
        try:
            self.process_text("OK")
            return True
        except Exception:
            return False
