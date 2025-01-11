"""Test stub implementation of RoboService."""

from datetime import datetime, UTC
from functools import lru_cache
from typing import Dict, Any, List, Optional

from domain.robo import (
    RoboService,
    RoboConfig,
    RoboProcessingResult,
)


class TestRoboService(RoboService):
    """Test stub implementation of RoboService for testing."""

    def __init__(self, config: RoboConfig):
        """Initialize TestRoboService.

        Args:
            config: RoboService configuration
        """
        self.config = config

    def analyze_activity_schema(
        self, schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze activity schema and return form layout suggestions.

        Args:
            schema: JSON Schema to analyze

        Returns:
            Dict with form layout suggestions
        """
        # For testing, return a simple form layout based on schema
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Create a form section for each property
        form_layout = {
            "type": "form",
            "sections": [
                {
                    "title": "Activity Information",
                    "fields": [
                        {
                            "name": prop_name,
                            "type": prop_info.get(
                                "type", "string"
                            ),
                            "required": prop_name
                            in required,
                            "label": prop_name.title(),
                        }
                        for prop_name, prop_info in properties.items()
                    ],
                }
            ],
        }

        return form_layout

    def process_text(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoboProcessingResult:
        """Process text input and return stubbed result.

        Args:
            text: Text to process
            context: Optional context for processing

        Returns:
            RoboProcessingResult: Stubbed processing result
        """
        # Handle note enrichment
        if (
            context
            and context.get("type") == "note_enrichment"
        ):
            return RoboProcessingResult(
                content="- Test formatted content\n- Second line",
                metadata={
                    "title": "Test Note Title",
                    "processed": True,
                },
                tokens_used=0,
                model_name="test_model",
                created_at=datetime.now(UTC),
            )

        # Default processing
        return RoboProcessingResult(
            content=text,
            metadata={"processed": True},
            tokens_used=0,
            model_name="test_model",
            created_at=datetime.now(UTC),
        )

    def extract_entities(
        self, text: str, entity_types: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Stub implementation of entity extraction.

        Args:
            text: Text to analyze
            entity_types: Types of entities to extract

        Returns:
            Empty dict for testing
        """
        return {
            entity_type: [] for entity_type in entity_types
        }

    def validate_content(
        self, content: str, validation_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Stub implementation of content validation.

        Args:
            content: Content to validate
            validation_rules: Rules to validate against

        Returns:
            Dict with validation results
        """
        return {"valid": True}

    def health_check(self) -> bool:
        """Stub implementation of health check."""
        try:
            self.process_text("test")
            return True
        except Exception:
            return False


@lru_cache()
def get_robo_service() -> TestRoboService:
    """Get TestRoboService instance."""
    config = RoboConfig(
        api_key="test_key",
        model_name="test_model",
    )
    return TestRoboService(config)
