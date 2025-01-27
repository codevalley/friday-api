"""Domain interfaces for Robo service."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime, UTC


@dataclass
class RoboConfig:
    """Configuration for Robo service."""

    api_key: str
    model_name: str
    max_retries: int = 3
    timeout_seconds: int = 30
    temperature: float = 0.7
    max_tokens: int = 150
    note_enrichment_prompt: str = (
        "You are a note formatting assistant. "
        "Your task is to:\n"
        "1. Extract a concise title (<50 chars)\n"
        "2. Format the content in clean markdown\n"
        "3. Use appropriate formatting (bold, italic, lists)\n"
        "4. Keep the content concise but complete"
    )
    activity_schema_prompt: str = (
        "You are a helpful assistant that creates templates for "
        "displaying activity content. Your task is to analyze a JSON "
        "schema that defines the structure of an activity and create "
        "templates for displaying the activity's title and content. "
        "Use $variable_name syntax to reference schema variables that "
        "will be populated dynamically. For the title, create a short "
        "template (< 50 chars) that captures the key information. For "
        "the formatted content, use Markdown for emphasis (bold, "
        "italics, bullet points) to create a well-structured template."
    )
    schema_analysis_prompt: str = (
        "You are a UI/UX expert analyzing JSON schemas. "
        "Your task is to:\n"
        "1. Analyze the schema structure\n"
        "2. Suggest optimal rendering strategy\n"
        "3. Group related fields\n"
        "4. Provide layout recommendations"
    )


@dataclass
class RoboResponse:
    """Response from Robo service."""

    content: str
    metadata: Dict[str, Any]
    tokens_used: int
    model_name: str
    created_at: datetime = datetime.now(UTC)


@dataclass
class RoboProcessingResult:
    """Result of a Robo processing operation."""

    content: str
    metadata: Dict[str, Any]
    tokens_used: int
    model_name: str
    created_at: datetime = datetime.now(UTC)


class RoboService(ABC):
    """Interface for Robo service operations."""

    @abstractmethod
    def process_text(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboResponse:
        """Process text input and return enhanced/analyzed result.

        The processing type is determined by the context:
        - context["type"] == "note_enrichment": Format note and extract title
        - No context: Default text processing

        Args:
            text: Text to process
            context: Optional context for processing

        Returns:
            RoboResponse: Processing result
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def extract_entities(
        self, text: str, entity_types: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract specified entity types from text."""
        pass

    @abstractmethod
    def validate_content(
        self, content: str, validation_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate content against specified rules."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the service is operational."""
        pass
