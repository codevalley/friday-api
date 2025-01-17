"""Domain model for Topic."""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Optional, Dict, Any, TypeVar, Type

from domain.exceptions import (
    TopicValidationError,
    TopicNameError,
    TopicIconError,
)

T = TypeVar("T", bound="TopicData")


@dataclass
class TopicData:
    """Domain model for Topic.

    This class represents a user-specific tag or classification object.
    Each topic must have a unique name per user and a valid icon.
    Topics can be used to categorize various entities in the system.

    Attributes:
        name: Unique name for the topic (per user)
        icon: Emoji character or URI for the icon
        user_id: ID of the user who owns this topic
        id: Optional primary key (None for new topics)
        created_at: When this topic was created
        updated_at: When this topic was last updated
    """

    name: str
    icon: str
    user_id: str
    id: Optional[int] = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        """Validate topic data after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate topic data according to business rules.

        Raises:
            TopicValidationError: If validation fails
            TopicNameError: If name validation fails
            TopicIconError: If icon validation fails
        """
        if (
            not isinstance(self.user_id, str)
            or not self.user_id
        ):
            raise TopicValidationError(
                "user_id must be a non-empty string"
            )

        if not isinstance(self.name, str):
            raise TopicNameError("name must be a string")

        if not self.name.strip():
            raise TopicNameError("name cannot be empty")

        if len(self.name) > 255:
            raise TopicNameError(
                "name cannot exceed 255 characters"
            )

        if not isinstance(self.icon, str):
            raise TopicIconError("icon must be a string")

        if not self.icon.strip():
            raise TopicIconError("icon cannot be empty")

        if len(self.icon) > 255:
            raise TopicIconError(
                "icon cannot exceed 255 characters"
            )

        if self.id is not None and (
            not isinstance(self.id, int) or self.id <= 0
        ):
            raise TopicValidationError(
                "id must be a positive integer"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for repository operations.

        Returns:
            dict: Dictionary representation of the topic
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "icon": self.icon,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create TopicData from dictionary data.

        Args:
            data: Dictionary containing topic data

        Returns:
            TopicData instance
        """
        # Handle both snake_case and camelCase keys
        user_id = data.get("user_id") or data.get("userId")
        created_at = (
            data.get("created_at")
            or data.get("createdAt")
            or datetime.now(UTC)
        )
        updated_at = (
            data.get("updated_at")
            or data.get("updatedAt")
            or datetime.now(UTC)
        )

        return cls(
            id=data.get("id"),
            user_id=user_id,
            name=data["name"],
            icon=data["icon"],
            created_at=created_at,
            updated_at=updated_at,
        )

    def update_name(self, new_name: str) -> None:
        """Update topic name.

        Args:
            new_name: New name for the topic

        Raises:
            TopicNameError: If name validation fails
        """
        if not isinstance(new_name, str):
            raise TopicNameError("name must be a string")

        if not new_name.strip():
            raise TopicNameError("name cannot be empty")

        if len(new_name) > 255:
            raise TopicNameError(
                "name cannot exceed 255 characters"
            )

        self.name = new_name
        self.updated_at = datetime.now(UTC)

    def update_icon(self, new_icon: str) -> None:
        """Update topic icon.

        Args:
            new_icon: New icon for the topic

        Raises:
            TopicIconError: If icon validation fails
        """
        if not isinstance(new_icon, str):
            raise TopicIconError("icon must be a string")

        if not new_icon.strip():
            raise TopicIconError("icon cannot be empty")

        if len(new_icon) > 255:
            raise TopicIconError(
                "icon cannot exceed 255 characters"
            )

        self.icon = new_icon
        self.updated_at = datetime.now(UTC)
