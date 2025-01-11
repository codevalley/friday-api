"""OpenAI implementation of RoboService."""

import logging
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
import json

from openai import OpenAI

from domain.exceptions import (
    RoboAPIError,
    RoboConfigError,
    RoboRateLimitError,
    RoboValidationError,
)
from domain.robo import (
    RoboService,
    RoboConfig,
    RoboProcessingResult,
)
from services.RateLimiter import RateLimiter
from utils.retry import with_retry

logger = logging.getLogger(__name__)


# OpenAI function definitions
ENRICH_NOTE_FUNCTION = {
    "name": "enrich_note",
    "description": (
        "Enrich a raw note by formatting content and extracting title"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Extracted title under 50 characters",
            },
            "formatted": {
                "type": "string",
                "description": "Well-formatted markdown content",
            },
        },
        "required": ["title", "formatted"],
    },
}

ANALYZE_SCHEMA_FUNCTION = {
    "name": "analyze_schema",
    "description": "Analyze JSON schema and suggest rendering strategy",
    "parameters": {
        "type": "object",
        "properties": {
            "render_type": {
                "type": "string",
                "description": "Suggested rendering type",
                "enum": [
                    "form",
                    "table",
                    "timeline",
                    "cards",
                ],
            },
            "layout": {
                "type": "object",
                "properties": {
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "fields": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                },
                            },
                        },
                    },
                    "suggestions": {
                        "type": "object",
                        "properties": {
                            "column_count": {
                                "type": "integer"
                            },
                            "responsive_breakpoints": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
            },
            "field_groups": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "fields": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "description": {"type": "string"},
                    },
                },
            },
        },
        "required": ["render_type", "layout"],
    },
}


class OpenAIService(RoboService):
    """OpenAI implementation of RoboService."""

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
            requests_per_minute=60,  # Default to 60 RPM
            tokens_per_minute=90000,  # Default to 90K TPM
            max_wait_seconds=60,  # Default to 60s max wait
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
    def process_text(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboProcessingResult:
        """Process text using OpenAI's API.

        The processing type is determined by the context:
        - context["type"] == "note_enrichment": Format note and extract title
        - No context: Default text processing

        Args:
            text: Text to process
            context: Optional context for processing

        Returns:
            RoboProcessingResult: Processing result

        Raises:
            RoboAPIError: If API call fails
            RoboRateLimitError: If rate limit is exceeded
            RoboConfigError: If configuration is invalid
        """
        try:
            # Estimate token usage (rough estimate: 4 chars ≈ 1 token)
            estimated_tokens = (
                len(text) // 4
            ) + 100  # Buffer for response

            # Wait for rate limit capacity
            if not self.rate_limiter.wait_for_capacity(
                estimated_tokens
            ):
                raise RoboRateLimitError(
                    "Failed to acquire capacity after retries"
                )

            # Choose processing type based on context
            if (
                context
                and context.get("type") == "note_enrichment"
            ):
                return self._enrich_note(text)

            # Default text processing
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant.",
                    },
                    {"role": "user", "content": text},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens or 150,
            )

            # Record actual token usage
            self.rate_limiter.record_usage(
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

    def _enrich_note(
        self, content: str
    ) -> RoboProcessingResult:
        """Internal method to enrich notes using function calling.

        Args:
            content: Raw note content to enrich

        Returns:
            RoboProcessingResult with enriched content and metadata

        Raises:
            RoboAPIError: If API call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": self.config.note_enrichment_prompt,
                    },
                    {"role": "user", "content": content},
                ],
                tools=[
                    {
                        "type": "function",
                        "function": ENRICH_NOTE_FUNCTION,
                    }
                ],
                tool_choice={
                    "type": "function",
                    "function": {"name": "enrich_note"},
                },
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            # Extract function call results
            if not response.choices:
                raise RoboAPIError(
                    "No choices in OpenAI response"
                )

            if not response.choices[0].message.tool_calls:
                raise RoboAPIError(
                    "No tool calls in OpenAI response"
                )

            tool_call = response.choices[
                0
            ].message.tool_calls[0]

            # Log the raw arguments for debugging
            logger.debug(
                f"Raw function arguments: {tool_call.function.arguments}"
            )

            try:
                result = json.loads(
                    tool_call.function.arguments
                )
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse function arguments: {str(e)}"
                )
                logger.error(
                    f"Raw arguments: {tool_call.function.arguments}"
                )
                raise RoboAPIError(
                    f"Invalid JSON in OpenAI response: {str(e)}"
                )

            # Validate required fields
            if (
                "formatted" not in result
                or "title" not in result
            ):
                raise RoboAPIError(
                    f"Missing required fields in response: {result}"
                )

            return RoboProcessingResult(
                content=result["formatted"],
                metadata={
                    "title": result["title"],
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
            if isinstance(e, RoboAPIError):
                raise
            logger.error(f"Error in _enrich_note: {str(e)}")
            raise RoboAPIError(
                f"Failed to enrich note: {str(e)}"
            )

    def extract_entities(
        self, text: str, entity_types: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities using OpenAI's API.

        Args:
            text: Text to analyze
            entity_types: Types of entities to extract

        Returns:
            Dict mapping entity types to lists of found entities

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError(
            "Entity extraction not yet implemented"
        )

    def validate_content(
        self, content: str, validation_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate content using OpenAI's API.

        Args:
            content: Content to validate
            validation_rules: Rules to validate against

        Returns:
            Dict with validation results

        Raises:
            NotImplementedError: This feature is not yet implemented
        """
        raise NotImplementedError(
            "Content validation not yet implemented"
        )

    def health_check(self) -> bool:
        """Check if the service is healthy.

        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "Respond with 'OK'",
                    }
                ],
                max_tokens=1,
            )
            return (
                response.choices[0].message.content.strip()
                == "OK"
            )
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

    def analyze_activity_schema(
        self, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze schema using OpenAI."""
        try:
            # Estimate token usage
            estimated_tokens = (
                len(json.dumps(schema)) // 4
            ) + 100  # Buffer for response

            # Wait for rate limit capacity
            if not self.rate_limiter.wait_for_capacity(
                estimated_tokens
            ):
                raise RoboRateLimitError(
                    "Failed to acquire capacity after retries"
                )

            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": self.config.schema_analysis_prompt,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Analyze this schema, suggest how to render it: "
                            f"{json.dumps(schema)}"
                        ),
                    },
                ],
                tools=[
                    {
                        "type": "function",
                        "function": ANALYZE_SCHEMA_FUNCTION,
                    }
                ],
                tool_choice={
                    "type": "function",
                    "function": {"name": "analyze_schema"},
                },
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            # Record token usage
            self.rate_limiter.record_usage(
                datetime.fromtimestamp(
                    response.created, UTC
                ),
                response.usage.total_tokens,
            )

            # Extract and validate response
            tool_call = response.choices[
                0
            ].message.tool_calls[0]
            result = json.loads(
                tool_call.function.arguments
            )

            return result

        except Exception as e:
            logger.error(
                f"Error analyzing schema: {str(e)}"
            )
            if isinstance(e, RoboRateLimitError):
                raise
            raise RoboAPIError(
                f"Failed to analyze schema: {str(e)}"
            )
