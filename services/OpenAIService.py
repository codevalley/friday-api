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

PROCESS_ACTIVITY_FUNCTION = {
    "name": "process_activity",
    "description": (
        "Generate a template for displaying activity content "
        "based on its schema"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": (
                    "A template for the activity title that can reference "
                    "schema variables using $variable_name syntax"
                ),
            },
            "formatted": {
                "type": "string",
                "description": (
                    "A markdown template for the activity content that can "
                    "reference schema variables using $variable_name syntax"
                ),
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

PROCESS_TASK_FUNCTION = {
    "name": "process_task",
    "description": "Process and format task content with title extraction",
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
            "priority": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "Suggested task priority",
            },
            "due_date": {
                "type": "string",
                "description": "Suggested due date if mentioned in content (ISO format)",  # noqa : E501
            },
        },
        "required": ["title", "formatted"],
    },
}

EXTRACT_TASKS_FUNCTION = {
    "name": "extract_tasks",
    "description": "Extract tasks from the given note content",
    "parameters": {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "description": "List of tasks extracted from the note",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The task description",
                        }
                    },
                    "required": ["content"],
                },
            }
        },
        "required": ["tasks"],
    },
}


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
            requests_per_minute=60,  # Default to 60 RPM
            tokens_per_minute=90000,  # Default to 90K TPM
            max_wait_seconds=60,  # Default to 60s max wait
        )

    def _estimate_tokens(
        self, text: str, buffer: int = 100
    ) -> int:
        """Estimate token count for text.

        Args:
            text: Input text
            buffer: Additional token buffer for response

        Returns:
            Estimated token count
        """
        return (len(text) // 4) + buffer

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
            estimated_tokens = self._estimate_tokens(text)

            # Wait for rate limit capacity
            if not self.rate_limiter.try_acquire(
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

    def _validate_tool_response(
        self,
        response: Any,
        required_fields: List[str],
        expected_function: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate OpenAI tool response.

        Args:
            response: OpenAI API response
            required_fields: List of required fields
            expected_function: If provided, validate that the function name matches # noqa: E501

        Returns:
            Dict containing the parsed response

        Raises:
            RoboAPIError: If validation fails
        """
        if not response.choices:
            raise RoboAPIError(
                "No choices in OpenAI response"
            )

        if not response.choices[0].message.tool_calls:
            raise RoboAPIError(
                "No tool calls in OpenAI response"
            )

        tool_call = response.choices[0].message.tool_calls[
            0
        ]

        try:
            result = json.loads(
                tool_call.function.arguments
            )
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse function arguments: "
                f"{str(e)}"
            )
            logger.error(
                "Raw arguments: "
                f"{tool_call.function.arguments}"
            )
            raise RoboAPIError(
                "Invalid JSON in OpenAI response: "
                f"{str(e)}"
            )

        if (
            expected_function
            and tool_call.function.name != expected_function
        ):
            raise RoboAPIError(
                "Invalid tool response format"
            )

        for field in required_fields:
            if field not in result:
                raise RoboAPIError(
                    f"Missing required field '{field}' in response"
                )

        return result

    def _enrich_note(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboProcessingResult:
        """Internal method to enrich notes using function calling.

        Args:
            content: Raw note content
            context: Optional processing context

        Returns:
            RoboProcessingResult with processed note

        Raises:
            RoboAPIError: If processing fails
        """
        try:
            # Estimate token usage
            estimated_tokens = (
                len(content) // 4
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
                timeout=self.config.timeout_seconds,
            )

            # Validate and parse response
            result = self._validate_tool_response(
                response,
                required_fields=["title", "formatted"],
                expected_function="enrich_note",
            )

            # Record token usage
            self.rate_limiter.record_usage(
                datetime.fromtimestamp(
                    response.created, UTC
                ),
                response.usage.total_tokens,
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
            if isinstance(
                e, (RoboAPIError, RoboRateLimitError)
            ):
                raise
            logger.error(f"Error in _enrich_note: {str(e)}")
            raise RoboAPIError(
                f"Failed to process note: {str(e)}"
            )

    def _process_task(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboProcessingResult:
        """Internal method to process tasks using function calling.

        Args:
            content: Raw task content
            context: Optional processing context

        Returns:
            RoboProcessingResult with processed task

        Raises:
            RoboAPIError: If processing fails
        """
        try:
            # Estimate token usage
            estimated_tokens = (
                len(content) // 4
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
                        "content": self.config.task_enrichment_prompt,
                    },
                    {"role": "user", "content": content},
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
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout_seconds,
            )

            # Validate and parse response
            result = self._validate_tool_response(
                response,
                required_fields=["title", "formatted"],
                expected_function="process_task",
            )

            # Record token usage
            self.rate_limiter.record_usage(
                datetime.fromtimestamp(
                    response.created, UTC
                ),
                response.usage.total_tokens,
            )

            return RoboProcessingResult(
                content=result["formatted"],
                metadata={
                    "title": result["title"],
                    "priority": result.get("priority"),
                    "due_date": result.get("due_date"),
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
            if isinstance(
                e, (RoboAPIError, RoboRateLimitError)
            ):
                raise
            logger.error(
                f"Error in _process_task: {str(e)}"
            )
            raise RoboAPIError(
                f"Failed to process task: {str(e)}"
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
    def process_note(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboProcessingResult:
        """Process note content using OpenAI's API.

        This method takes note content and processes it to:
        1. Extract a concise title
        2. Format the content in clean markdown
        3. Apply appropriate formatting (headers, lists, code blocks)

        Args:
            content: Note content to process
            context: Optional context for processing

        Returns:
            RoboProcessingResult: Processing result with:
                - content: Formatted note content
                - metadata: Contains extracted title
                - tokens_used: Number of tokens used
                - model_name: Model used for processing
                - created_at: When processing occurred

        Raises:
            RoboAPIError: If API call fails
            RoboRateLimitError: If rate limit is exceeded
            RoboValidationError: If content is invalid
        """
        if not content:
            raise RoboValidationError(
                message="Note content cannot be empty",
                code="ROBO_VALIDATION_ERROR",
            )

        return self._enrich_note(content, context)

    @with_retry(
        max_retries=3,
        retry_on=(RoboAPIError,),
        exclude_on=(
            RoboConfigError,
            RoboValidationError,
            RoboRateLimitError,
        ),
    )
    def process_task(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboProcessingResult:
        """Process task content using OpenAI's API.

        This method takes task content and processes it to:
        1. Extract a concise title
        2. Format the content in clean markdown
        3. Suggest priority and due date if mentioned
        4. Apply appropriate formatting

        Args:
            content: Task content to process
            context: Optional context for processing

        Returns:
            RoboProcessingResult with processed task

        Raises:
            RoboAPIError: If API call fails
            RoboRateLimitError: If rate limit is exceeded
            RoboValidationError: If content is invalid
        """
        if not content:
            raise RoboValidationError(
                message="Task content cannot be empty",
                code="ROBO_VALIDATION_ERROR",
            )

        return self._process_task(content, context)

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
                f"Schema: {json.dumps(schema)}"
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
                tools=[
                    {
                        "type": "function",
                        "function": PROCESS_ACTIVITY_FUNCTION,
                    }
                ],
                tool_choice={
                    "type": "function",
                    "function": {
                        "name": "process_activity"
                    },
                },
                temperature=0.7,
                max_tokens=500,
                timeout=self.config.timeout_seconds,
            )

            # Validate and parse response
            result = self._validate_tool_response(
                response,
                required_fields=["title", "formatted"],
                expected_function="process_activity",
            )

            # Record token usage
            self.rate_limiter.record_usage(
                datetime.fromtimestamp(
                    response.created, UTC
                ),
                response.usage.total_tokens,
            )

            return result

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

    def extract_tasks(
        self, content: str
    ) -> List[Dict[str, str]]:
        """Extract tasks from note content.

        Args:
            content: The note content to extract tasks from

        Returns:
            List of extracted tasks, each with content string

        Raises:
            OpenAIError: If API call fails
            ValidationError: If response validation fails
        """
        try:
            # Use task extraction prompt from config
            prompt = self.config.task_extraction_prompt

            # Prepare messages for chat completion
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": content},
            ]

            # Call OpenAI with function definition
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                functions=[EXTRACT_TASKS_FUNCTION],
                function_call={"name": "extract_tasks"},
            )

            # Parse and validate response
            try:
                # Try tool_calls first (newer format)
                if (
                    hasattr(
                        response.choices[0].message,
                        "tool_calls",
                    )
                    and response.choices[
                        0
                    ].message.tool_calls
                ):
                    tool_call = response.choices[
                        0
                    ].message.tool_calls[0]
                    if (
                        tool_call.function.name
                        != "extract_tasks"
                    ):
                        raise RoboValidationError(
                            message=(
                                "Expected function name 'extract_tasks', "
                                f"got '{tool_call.function.name}'"
                            ),
                            code="INVALID_FUNCTION_NAME",
                        )
                    arguments = tool_call.function.arguments
                # Fall back to function_call (older format)
                elif (
                    hasattr(
                        response.choices[0].message,
                        "function_call",
                    )
                    and response.choices[
                        0
                    ].message.function_call
                ):
                    function_call = response.choices[
                        0
                    ].message.function_call
                    if (
                        function_call.name
                        != "extract_tasks"
                    ):
                        raise RoboValidationError(
                            message=(
                                "Expected function name 'extract_tasks', "
                                f"got '{function_call.name}'"
                            ),
                            code="INVALID_FUNCTION_NAME",
                        )
                    arguments = function_call.arguments
                else:
                    raise AttributeError(
                        "No tool_calls or function_call found in response"
                    )

                result = json.loads(arguments)
                return result["tasks"]
            except (
                json.JSONDecodeError,
                KeyError,
                AttributeError,
            ) as e:
                logger.error(
                    f"Failed to parse OpenAI response: {str(e)}"
                )
                raise RoboValidationError(
                    message="Invalid response format from OpenAI",
                    code="INVALID_RESPONSE_FORMAT",
                )
        except Exception as e:
            logger.error(
                f"Unexpected error in extract_tasks: {str(e)}"
            )
            raise
