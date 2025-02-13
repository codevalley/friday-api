"""OpenAI implementation of RoboService using instructor library."""

import json
import logging
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
from instructor import OpenAISchema
from pydantic import Field, ConfigDict

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
from domain.values import TaskPriority
from services.RateLimiter import RateLimiter
from utils.retry import with_retry

logger = logging.getLogger(__name__)


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
                        },
                        "priority": {
                            "type": "string",
                            "enum": [
                                "urgent",
                                "high",
                                "medium",
                                "low",
                            ],
                            "description": "Task priority level",
                        },
                        "status": {
                            "type": "string",
                            "enum": [
                                "todo",
                                "in_progress",
                                "done",
                                "blocked",
                            ],
                            "description": "Current task status",
                        },
                    },
                    "required": ["content"],
                },
            },
        },
        "required": ["tasks"],
    },
}


class TextProcessingSchema(OpenAISchema):
    """Schema for general text processing."""

    content: str = Field(
        ...,
        description="Processed and formatted content",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional extracted metadata",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "content": "# Processed Content\n\nThis is the processed and formatted version of the input text.",  # noqa: E501
                    "metadata": {
                        "summary": "A text about content processing",
                        "topics": [
                            "processing",
                            "formatting",
                        ],
                        "sentiment": "neutral",
                    },
                }
            ]
        }
    )

    @classmethod
    def from_completion(cls, completion):
        """Create from OpenAI completion response."""
        return cls(
            content=completion.choices[0].message.content,
            metadata={
                "topics": ["general"],
                "sentiment": "neutral",
                "summary": "Processed text content",
            },
        )


class NoteEnrichmentSchema(OpenAISchema):
    """Schema for note enrichment function."""

    title: str = Field(
        ...,
        max_length=50,
        description="Extracted title for the note",
    )
    formatted: str = Field(
        ...,
        description="Well-formatted markdown content",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional extracted metadata",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Project Planning Meeting",
                    "formatted": "# Project Planning Meeting\n\n"
                    "## Action Items\n"
                    "- Review timeline\n"
                    "- Assign tasks\n"
                    "- Schedule follow-up\n",
                    "metadata": {
                        "topics": ["planning", "meetings"],
                        "sentiment": "neutral",
                    },
                }
            ]
        }
    )

    @classmethod
    def from_completion(cls, completion):
        """Create from OpenAI completion response."""
        try:
            # Parse the JSON response
            response_data = json.loads(
                completion.choices[0].message.content
            )
            return cls(
                title=response_data["title"],
                formatted=response_data["formatted"],
                metadata=response_data.get("metadata", {}),
            )
        except json.JSONDecodeError as e:
            raise RoboValidationError(
                f"Failed to parse OpenAI response as JSON: {str(e)}"
            )
        except KeyError as e:
            raise RoboValidationError(
                f"Missing required field in OpenAI response: {str(e)}"
            )


class TaskEnrichmentSchema(OpenAISchema):
    """Schema for task processing function."""

    title: str = Field(
        ...,
        max_length=50,
        description="Extracted title for the task",
    )
    formatted: str = Field(
        ...,
        description="Formatted task content in markdown",
    )
    suggested_priority: Optional[str] = Field(
        None,
        description="Suggested priority based on content",
    )
    suggested_due_date: Optional[datetime] = Field(
        None,
        description="Suggested due date if mentioned",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Complete Project Proposal",
                    "formatted": "Complete project proposal document "
                    "with timeline and resource estimates",
                    "suggested_priority": "HIGH",
                    "suggested_due_date": "2024-02-15T17:00:00Z",
                    "metadata": {
                        "tags": ["project", "planning"],
                        "estimated_effort": "medium",
                    },
                }
            ]
        }
    )

    def validate_priority(self) -> None:
        """Validate priority value."""
        if self.suggested_priority:
            try:
                TaskPriority(
                    self.suggested_priority.lower()
                )
            except ValueError as e:
                raise ValueError(
                    f"Invalid priority value: {self.suggested_priority}"
                    f" ({str(e)})",
                )

    @classmethod
    def from_completion(cls, completion):
        """Create from OpenAI completion response."""
        if not completion.choices:
            raise ValueError("No choices in completion")

        response_data = json.loads(
            completion.choices[0].message.content
        )

        # Validate and normalize priority if present
        priority = response_data.get("suggested_priority")
        if priority:
            priority = priority.upper()
            try:
                TaskPriority(priority.lower())
            except ValueError as e:
                raise ValueError(
                    f"Invalid priority value: {priority}"
                    f" ({str(e)})",
                )

        instance = cls(
            title=response_data["title"],
            formatted=response_data["formatted"],
            suggested_priority=priority,
            suggested_due_date=response_data.get(
                "suggested_due_date"
            ),
            metadata=response_data.get("metadata", {}),
        )
        instance.validate_priority()
        return instance


class ActivitySchemaAnalysis(OpenAISchema):
    """Schema for analyzing activity data structures."""

    title_template: str = Field(
        ...,
        description="Template for activity title using $variable_name syntax",
    )
    content_template: str = Field(
        ...,
        description="Template for activity content using $variable_name syntax",  # noqa: E501
    )
    suggested_layout: Dict[str, Any] = Field(
        ...,
        description="Suggested layout configuration",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title_template": "$action on $project",
                    "content_template": "**Action:** $action\n"
                    "**Project:** $project\n"
                    "**Details:** $details",
                    "suggested_layout": {
                        "type": "card",
                        "sections": [
                            {
                                "title": "Action",
                                "field": "action",
                            },
                            {
                                "title": "Project",
                                "field": "project",
                            },
                            {
                                "title": "Details",
                                "field": "details",
                            },
                        ],
                    },
                }
            ]
        }
    )

    @classmethod
    def from_completion(cls, completion):
        """Create from OpenAI completion response."""
        content = completion.choices[0].message.content
        # Parse the content into sections
        lines = content.split("\n")
        title_template = ""
        content_template = ""
        suggested_layout = {"type": "card", "sections": []}
        for line in lines:
            if line.startswith("title_template:"):
                title_template = line.split(":", 1)[
                    1
                ].strip()
            elif line.startswith("content_template:"):
                content_template = line.split(":", 1)[
                    1
                ].strip()
            elif line.startswith("section:"):
                section = line.split(":", 1)[1].strip()
                suggested_layout["sections"].append(
                    {
                        "title": section,
                        "field": section.lower(),
                    }
                )
        return cls(
            title_template=title_template or "$action",
            content_template=content_template or "$content",
            suggested_layout=suggested_layout,
        )


class InstructorService(RoboService):
    """OpenAI service implementation using instructor library.

    This service implements the RoboService interface using OpenAI's API
    with the instructor library for improved type safety and validation.

    Attributes:
        config: Service configuration
        client: OpenAI API client
        rate_limiter: Rate limiter for API calls
    """

    @with_retry(
        max_retries=3,
        retry_on=(RoboAPIError, RoboRateLimitError),
        exclude_on=tuple(),  # Allow retrying on RoboRateLimitError
    )
    def process_text(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboProcessingResult:
        """Process text content using OpenAI's API with instructor.

        Args:
            content: Text content to process
            context: Optional context for processing

        Returns:
            RoboProcessingResult with processed text

        Raises:
            RoboAPIError: If API call fails
            RoboValidationError: If content is invalid
        """
        if not content:
            raise RoboValidationError(
                "Content cannot be empty"
            )

        # Estimate tokens needed for this request
        estimated_tokens = self._estimate_tokens(content)

        if not self.rate_limiter.wait_for_capacity(
            tokens=estimated_tokens
        ):
            raise RoboRateLimitError("Rate limit exceeded")

        try:
            # Create context string if provided
            context_str = (
                "\n\nContext:\n" + json.dumps(context)
                if context
                else ""
            )

            # Process with OpenAI using instructor
            result = TextProcessingSchema.from_completion(
                completion=self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": self.config.note_enrichment_prompt,
                        },
                        {
                            "role": "user",
                            "content": f"{content}{context_str}",
                        },
                    ],
                    model=self.config.model_name,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
            )

            # Return the result
            return RoboProcessingResult(
                content=result.content,
                metadata=result.metadata,
                tokens_used=self._estimate_tokens(
                    content
                ),  # Estimate since instructor doesn't provide usage
                model_name=self.config.model_name,
                created_at=datetime.now(UTC),
            )

        except Exception as e:
            raise RoboAPIError(
                f"Failed to process text: {str(e)}"
            ) from e

    async def extract_entities(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Extract entities from text content.

        Args:
            content: Text content to extract from
            context: Optional context for extraction

        Returns:
            List of extracted entities

        Raises:
            RoboAPIError: If API call fails
            RoboValidationError: If content is invalid
        """
        raise NotImplementedError

    def validate_content(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate content before processing.

        Args:
            content: Content to validate
            context: Optional context for validation

        Returns:
            True if content is valid

        Raises:
            RoboValidationError: If content is invalid
        """
        if not content or not content.strip():
            raise RoboValidationError(
                "Content cannot be empty"
            )
        return True

    def __init__(self, config: RoboConfig):
        """Initialize OpenAI service with instructor integration.

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

    def _get_datetime_context(self) -> str:
        """Generate current datetime context for LLM.

        Returns:
            str: Formatted datetime context
        """
        now = datetime.now(UTC)
        return f"Current time: {now.isoformat()}"

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
        # Simple estimation: ~4 chars per token + buffer
        return (len(text) // 4) + buffer

    def _prepare_messages(
        self,
        content: str,
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, str]]:
        """Prepare messages for OpenAI API call.

        Args:
            content: The content to process
            system_prompt: The system prompt to use
            context: Optional context to include

        Returns:
            List of message dictionaries
        """
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # Add datetime context if available
        if (
            hasattr(self.config, "include_datetime")
            and self.config.include_datetime
        ):
            dt_context = self._get_datetime_context()
            messages.append(
                {"role": "system", "content": dt_context}
            )

        # Add any additional context
        if context:
            context_str = "\n".join(
                f"{key}: {value}"
                for key, value in context.items()
            )
            messages.append(
                {"role": "system", "content": context_str}
            )

        # Add user content
        messages.append(
            {"role": "user", "content": content}
        )

        return messages

    @with_retry(
        max_retries=3,
        retry_on=(RoboAPIError, RoboRateLimitError),
        exclude_on=tuple(),  # Allow retrying on RoboRateLimitError
    )
    def process_note(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboProcessingResult:
        """Process note content using OpenAI's API with instructor.

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
                "Content cannot be empty"
            )

        # Estimate tokens needed for this request
        estimated_tokens = self._estimate_tokens(content)

        if not self.rate_limiter.wait_for_capacity(
            tokens=estimated_tokens
        ):
            raise RoboRateLimitError("Rate limit exceeded")

        try:
            # Create context string if provided
            context_str = (
                "\n\nContext:\n" + json.dumps(context)
                if context
                else ""
            )

            # Process with OpenAI using instructor
            enrichment = NoteEnrichmentSchema.from_completion(
                completion=self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": self.config.note_enrichment_prompt,
                        },
                        {
                            "role": "user",
                            "content": f"{content}{context_str}",
                        },
                    ],
                    model=self.config.model_name,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
            )

            # Return the result
            return RoboProcessingResult(
                content=enrichment.formatted,
                metadata={
                    "title": enrichment.title,
                    **enrichment.metadata,
                },
                tokens_used=self._estimate_tokens(
                    content
                ),  # Estimate since instructor doesn't provide usage
                model_name=self.config.model_name,
                created_at=datetime.now(UTC),
            )

        except Exception as e:
            raise RoboAPIError(
                f"Failed to process note: {str(e)}"
            ) from e

    @with_retry(
        max_retries=3,
        retry_on=(RoboAPIError, RoboRateLimitError),
        exclude_on=tuple(),  # Allow retrying on RoboRateLimitError
    )
    def process_task(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboProcessingResult:
        """Process task content using OpenAI's API with instructor.

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
                "Content cannot be empty"
            )

        # Estimate tokens needed for this request
        estimated_tokens = self._estimate_tokens(content)

        if not self.rate_limiter.wait_for_capacity(
            tokens=estimated_tokens
        ):
            raise RoboRateLimitError("Rate limit exceeded")

        try:
            # Create context string if provided
            context_str = (
                "\n\nContext:\n" + json.dumps(context)
                if context
                else ""
            )

            # Process with OpenAI using instructor
            enrichment = TaskEnrichmentSchema.from_completion(
                completion=self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": self.config.task_enrichment_prompt,
                        },
                        {
                            "role": "user",
                            "content": f"{content}{context_str}",
                        },
                    ],
                    model=self.config.model_name,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
            )

            # Return the result with properly structured metadata
            metadata = {
                "title": enrichment.title,
                "suggested_priority": enrichment.suggested_priority,
                "suggested_due_date": enrichment.suggested_due_date,
            }
            metadata.update(enrichment.metadata)

            return RoboProcessingResult(
                content=enrichment.formatted,
                metadata=metadata,
                tokens_used=self._estimate_tokens(content),
                model_name=self.config.model_name,
                created_at=datetime.now(UTC),
            )

        except Exception as e:
            raise RoboAPIError(
                f"Failed to process task: {str(e)}"
            ) from e

    @with_retry(
        max_retries=3,
        retry_on=(RoboAPIError, RoboRateLimitError),
        exclude_on=tuple(),  # Allow retrying on RoboRateLimitError
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
        if not schema:
            raise RoboValidationError(
                "Schema cannot be empty"
            )

        if not isinstance(schema, dict):
            raise RoboValidationError(
                "Schema must be a dictionary"
            )

        if "properties" not in schema:
            raise RoboValidationError(
                "Schema must contain properties"
            )

        # Create schema string for token estimation and prompt
        schema_str = json.dumps(schema, indent=2)
        estimated_tokens = self._estimate_tokens(
            schema_str, buffer=1000
        )  # Large buffer for template generation

        if not self.rate_limiter.wait_for_capacity(
            tokens=estimated_tokens
        ):
            raise RoboRateLimitError("Rate limit exceeded")

        try:
            prompt = f"""Analyze this JSON Schema and create display templates.

Schema:
{schema_str}

Create templates that:
1. Use $variable_name syntax to reference schema properties
2. Create a concise title template (max 50 chars)
3. Create a detailed content template in markdown
4. Consider required vs optional fields
5. Use appropriate markdown formatting

Respond with templates that will look good when populated."""

            # Process with OpenAI using instructor
            analysis = ActivitySchemaAnalysis.from_completion(
                completion=self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": self.config.activity_schema_prompt,
                        },
                        {"role": "user", "content": prompt},
                    ],
                    model=self.config.model_name,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
            )

            return {
                "title_template": analysis.title_template,
                "content_template": analysis.content_template,
                "suggested_layout": analysis.suggested_layout,
            }

        except Exception as e:
            raise RoboAPIError(
                f"Failed to analyze schema: {str(e)}"
            ) from e

    def health_check(self) -> bool:
        """Check if the service is operational.

        Returns:
            bool: True if service is operational
        """
        try:
            # Simple model list call to check API access
            self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    @with_retry(
        max_retries=3,
        retry_on=(RoboAPIError, RoboRateLimitError),
        exclude_on=tuple(),  # Allow retrying on RoboRateLimitError
    )
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
            # Prepare messages with datetime context
            messages = self._prepare_messages(
                content=content,
                system_prompt=self.config.task_extraction_prompt,
            )

            # Estimate tokens needed
            estimated_tokens = self._estimate_tokens(
                content
            )
            self.rate_limiter.wait_for_capacity(
                estimated_tokens
            )

            # Call OpenAI with function definition
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                tools=[
                    {
                        "type": "function",
                        "function": EXTRACT_TASKS_FUNCTION,
                    }
                ],
                tool_choice={
                    "type": "function",
                    "function": {"name": "extract_tasks"},
                },
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
                            )
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
                            )
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
                    message="Invalid response format from OpenAI"
                )

            # Record token usage
            self.rate_limiter.record_usage(
                datetime.fromtimestamp(
                    response.created, UTC
                ),
                response.usage.total_tokens,
            )

        except (
            RoboRateLimitError,
            RoboValidationError,
        ) as e:
            # Let these errors propagate as they are
            logger.error(
                f"Error extracting tasks: {str(e)}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Error extracting tasks: {str(e)}"
            )
            raise RoboAPIError(
                f"OpenAI API error: {str(e)}"
            )
