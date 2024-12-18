"""Domain model for Activity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional

from domain.models.moment import MomentData


@dataclass
class ActivityData:
    """Domain model for Activity.

    This class represents an activity type that can be tracked through moments.
    It contains all the business logic and validation rules for activities.

    Attributes:
        id: Unique identifier for the activity
        name: Display name of the activity
        description: Detailed description
        activity_schema: JSON Schema for validating moment data
        icon: Display icon
        color: Hex color code for UI
        user_id: ID of the user who created this activity
        moment_count: Number of moments recorded for this activity
        moments: List of moments for this activity (optional)
        created_at: When this record was created
        updated_at: When this record was last updated
    """

    name: str
    description: str
    activity_schema: Dict[str, Any]
    icon: str
    color: str
    user_id: str
    id: Optional[int] = None
    moment_count: int = 0
    moments: Optional[List[MomentData]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate the activity data after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate the activity data.

        Raises:
            ValueError: If any validation fails
        """
        if not self.name or not isinstance(self.name, str):
            raise ValueError(
                "name must be a non-empty string"
            )

        if not self.description or not isinstance(
            self.description, str
        ):
            raise ValueError(
                "description must be a non-empty string"
            )

        if not isinstance(self.activity_schema, dict):
            raise ValueError(
                "activity_schema must be a dictionary"
            )

        if not self.icon or not isinstance(self.icon, str):
            raise ValueError(
                "icon must be a non-empty string"
            )

        if not self.color or not isinstance(
            self.color, str
        ):
            raise ValueError(
                "color must be a non-empty string"
            )

        if not self.user_id or not isinstance(
            self.user_id, str
        ):
            raise ValueError(
                "user_id must be a non-empty string"
            )

        if self.id is not None and (
            not isinstance(self.id, int) or self.id <= 0
        ):
            raise ValueError(
                "id must be a positive integer"
            )

        if (
            not isinstance(self.moment_count, int)
            or self.moment_count < 0
        ):
            raise ValueError(
                "moment_count must be a non-negative integer"
            )

        if self.moments is not None and not isinstance(
            self.moments, list
        ):
            raise ValueError(
                "moments must be a list or None"
            )

        if self.created_at is not None and not isinstance(
            self.created_at, datetime
        ):
            raise ValueError(
                "created_at must be a datetime object"
            )

        if self.updated_at is not None and not isinstance(
            self.updated_at, datetime
        ):
            raise ValueError(
                "updated_at must be a datetime object"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the activity data to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the activity
        """
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "activity_schema": self.activity_schema,
            "icon": self.icon,
            "color": self.color,
            "user_id": self.user_id,
            "moment_count": self.moment_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.moments:
            data["moments"] = [
                m.to_dict() for m in self.moments
            ]
        return data

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any]
    ) -> "ActivityData":
        """Create an ActivityData instance from a dictionary.

        Args:
            data: Dictionary containing activity data

        Returns:
            ActivityData: New instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        moments_data = data.get("moments", [])
        moments = (
            [MomentData.from_dict(m) for m in moments_data]
            if moments_data
            else None
        )

        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data["description"],
            activity_schema=data["activity_schema"],
            icon=data["icon"],
            color=data["color"],
            user_id=data["user_id"],
            moment_count=data.get("moment_count", 0),
            moments=moments,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def from_orm(cls, orm_model: Any) -> "ActivityData":
        """Create an ActivityData instance from an ORM model.

        Args:
            orm_model: SQLAlchemy model instance

        Returns:
            ActivityData: New instance
        """
        moments = None
        if (
            hasattr(orm_model, "moments")
            and orm_model.moments
        ):
            moments = [
                MomentData.from_orm(m)
                for m in orm_model.moments
            ]

        return cls(
            id=orm_model.id,
            name=orm_model.name,
            description=orm_model.description,
            activity_schema=orm_model.activity_schema,
            icon=orm_model.icon,
            color=orm_model.color,
            user_id=orm_model.user_id,
            moment_count=orm_model.moment_count,
            moments=moments,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )
