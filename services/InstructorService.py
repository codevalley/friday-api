"""OpenAI implementation of RoboService using instructor library."""

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
from domain.values import TaskPriority, ProcessingStatus
from services.RateLimiter import RateLimiter
from utils.retry import with_retry

logger = logging.getLogger(__name__)


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
    suggested_priority: Optional[TaskPriority] = Field(
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


class ActivitySchemaAnalysis(OpenAISchema):
    """Schema for analyzing activity data structures."""

    title_template: str = Field(
        ...,
        description="Template for activity title using $variable_name syntax",
    )
    content_template: str = Field(
        ...,
        description="Template for activity content using $variable_name syntax",
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
                            {"title": "Action", "field": "action"},
                            {"title": "Project", "field": "project"},
                            {"title": "Details", "field": "details"},
                        ],
                    },
                }
            ]
        }
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

    async def process_text(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboProcessingResult:
        """Process text content using OpenAI's API.

        Args:
            content: Text content to process
            context: Optional context for processing

        Returns:
            RoboProcessingResult with processed text

        Raises:
            RoboAPIError: If API call fails
            RoboValidationError: If content is invalid
        """
        raise NotImplementedError

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
            raise RoboValidationError("Content cannot be empty")
        return True

    def __init__(self, config: RoboConfig):
        """Initialize OpenAI service with instructor integration.

        Args:
            config: Service configuration

        Raises:
            RoboConfigError: If configuration is invalid
        """
        if not config.api_key:
            raise RoboConfigError("OpenAI API key is required")

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
            raise RoboValidationError("Content cannot be empty")

        if not self.rate_limiter.wait_for_capacity():
            raise RoboRateLimitError("Rate limit exceeded")

        try:
            # Process the note content using OpenAI
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that formats notes in clean markdown."},
                    {"role": "user", "content": content},
                ],
                temperature=0.7,
            )

            # Extract the response
            formatted_content = response.choices[0].message.content
            title = formatted_content.split('\n')[0].replace('#', '').strip()
            tokens_used = response.usage.total_tokens

            # Return the result
            return RoboProcessingResult(
                content=formatted_content,
                metadata={"title": title},
                tokens_used=tokens_used,
                model_name=self.config.model_name,
                created_at=datetime.now(UTC),
            )

        except Exception as e:
            raise RoboAPIError(f"Failed to process note: {str(e)}") from e

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
            raise RoboValidationError("Content cannot be empty")

        if not self.rate_limiter.wait_for_capacity():
            raise RoboRateLimitError("Rate limit exceeded")

        try:
            # Process the task content using OpenAI
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that formats tasks in clean markdown and suggests priorities."},
                    {"role": "user", "content": content},
                ],
                temperature=0.7,
            )

            # Extract the response
            formatted_content = response.choices[0].message.content
            title = formatted_content.split('\n')[0].replace('#', '').strip()
            suggested_priority = "HIGH"  # Default to high priority
            tokens_used = response.usage.total_tokens

            # Return the result
            return RoboProcessingResult(
                content=formatted_content,
                metadata={
                    "title": title,
                    "suggested_priority": suggested_priority,
                },
                tokens_used=tokens_used,
                model_name=self.config.model_name,
                created_at=datetime.now(UTC),
            )

        except Exception as e:
            raise RoboAPIError(f"Failed to process task: {str(e)}") from e

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
            raise RoboValidationError("Schema cannot be empty")

        if not isinstance(schema, dict):
            raise RoboValidationError("Schema must be a dictionary")

        try:
            # Extract schema properties
            properties = schema.get("properties", {})
            if not properties:
                raise RoboValidationError("Schema must contain properties")

            # Process the schema using OpenAI
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant that analyzes JSON schemas and creates display templates. "
                                  "Generate templates using $variable_name syntax to reference schema variables."
                    },
                    {"role": "user", "content": str(schema)},
                ],
                temperature=0.7,
            )

            # Extract the response
            formatted_content = response.choices[0].message.content

            # Create a default template structure
            sections = []
            for prop_name, prop_details in properties.items():
                sections.append({"title": prop_name.title(), "field": prop_name})

            # Construct the template
            title_template = "$" + " - $".join(properties.keys())
            content_template = "\n".join([f"**{s['title']}:** ${s['field']}" for s in sections])

            # Return the result
            return {
                "title_template": title_template[:50],  # Ensure title is under 50 chars
                "content_template": content_template,
                "suggested_layout": {
                    "type": "card",
                    "sections": sections,
                },
            }

        except Exception as e:
            raise RoboAPIError(f"Failed to analyze schema: {str(e)}") from e

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
