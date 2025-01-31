"""Domain model for Timeline events."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from domain.exceptions import TimelineValidationError


class TimelineEventType(str, Enum):
    """Valid types of timeline events."""

    TASK = "task"
    NOTE = "note"
    MOMENT = "moment"


@dataclass
class TimelineEventData:
    """Value object representing an event in the timeline.

    This is an ephemeral domain model that aggregates data from various
    entity types (Tasks, Notes, Moments) into a unified timeline view.

    Attributes:
        entity_type: Type of the entity ("task", "note", "moment")
        entity_id: ID of the original entity
        user_id: ID of the user who owns this entity
        timestamp: When this event occurred (created_at or updated_at)
        title: Optional title (e.g. for tasks)
        description: Optional description text
        content: Optional content text (e.g. for notes)
        metadata: Additional type-specific data (e.g. task status, priority)
    """

    entity_type: TimelineEventType
    entity_id: int
    user_id: str
    timestamp: datetime
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Validate the timeline event data after initialization."""
        # Validate first to catch any type errors
        self.validate()

        # Make a copy of metadata to ensure immutability
        if self.metadata is not None:
            self.metadata = dict(self.metadata)

    def validate(self) -> None:
        """Validate the timeline event data.

        Raises:
            TimelineValidationError: If validation fails
        """
        if not isinstance(
            self.entity_type, TimelineEventType
        ):
            raise TimelineValidationError(
                "Invalid entity type",
                code="invalid_entity_type",
            )

        if (
            not isinstance(self.entity_id, int)
            or self.entity_id <= 0
        ):
            raise TimelineValidationError(
                "Invalid entity ID",
                code="invalid_entity_id",
            )

        # Custom validation for user_id to use TimelineValidationError
        if not self.user_id or not self.user_id.strip():
            raise TimelineValidationError(
                "user_id cannot be empty",
                code="empty_user_id",
            )

        if not isinstance(self.timestamp, datetime):
            raise TimelineValidationError(
                "Invalid timestamp",
                code="invalid_timestamp",
            )

        # Title, description, and content are optional
        # but should be strings if present
        if self.title is not None and not isinstance(
            self.title, str
        ):
            raise TimelineValidationError(
                "Title must be a string",
                code="invalid_title_type",
            )

        if self.description is not None and not isinstance(
            self.description, str
        ):
            raise TimelineValidationError(
                "Description must be a string",
                code="invalid_description_type",
            )

        if self.content is not None and not isinstance(
            self.content, str
        ):
            raise TimelineValidationError(
                "Content must be a string",
                code="invalid_content_type",
            )

        if self.metadata is not None and not isinstance(
            self.metadata, dict
        ):
            raise TimelineValidationError(
                "Metadata must be a dictionary",
                code="invalid_metadata_type",
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the timeline event to a dictionary.

        Returns:
            Dict containing the timeline event data
        """
        return {
            "type": self.entity_type.value,
            "id": self.entity_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "metadata": self.metadata or {},
        }
