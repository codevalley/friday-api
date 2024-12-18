"""Domain model for Moment."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

from utils.validation import validate_moment_data


@dataclass
class MomentData:
    """Domain model for Moment.

    This class represents a moment in time when a user records an activity.
    It contains all the business logic and validation rules for moments.

    Attributes:
        id: Unique identifier for the moment
        activity_id: ID of the activity this moment belongs to
        user_id: ID of the user who created this moment
        data: Activity-specific data that must conform to the activity's schema
        timestamp: When this moment occurred (in UTC)
        created_at: When this record was created
        updated_at: When this record was last updated
    """

    activity_id: int
    user_id: str
    data: Dict[str, Any]
    timestamp: datetime
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate the moment data after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate the moment data.

        Raises:
            ValueError: If any validation fails
        """
        if (
            not isinstance(self.activity_id, int)
            or self.activity_id <= 0
        ):
            raise ValueError(
                "activity_id must be a positive integer"
            )

        if not self.user_id or not isinstance(
            self.user_id, str
        ):
            raise ValueError(
                "user_id must be a non-empty string"
            )

        if not isinstance(self.data, dict):
            raise ValueError("data must be a dictionary")

        if not isinstance(self.timestamp, datetime):
            raise ValueError(
                "timestamp must be a datetime object"
            )

        if self.id is not None and (
            not isinstance(self.id, int) or self.id <= 0
        ):
            raise ValueError(
                "id must be a positive integer"
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

    def validate_against_schema(
        self, activity_schema: Dict[str, Any]
    ) -> None:
        """Validate the moment data against its activity's schema.

        Args:
            activity_schema: The JSON schema from the activity

        Raises:
            HTTPException: If validation fails
        """
        validate_moment_data(self.data, activity_schema)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the moment data to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the moment
        """
        return {
            "id": self.id,
            "activity_id": self.activity_id,
            "user_id": self.user_id,
            "data": self.data,
            "timestamp": self.timestamp,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_json_dict(
        self, graphql: bool = False
    ) -> Dict[str, Any]:
        """Convert to a JSON-compatible dictionary.

        Args:
            graphql: Whether to use GraphQL field naming (camelCase)

        Returns:
            Dict[str, Any]: JSON-compatible dictionary
        """
        data = self.to_dict()
        if graphql:
            # Convert snake_case to camelCase for GraphQL
            return {
                "id": data["id"],
                "activityId": data["activity_id"],
                "userId": data["user_id"],
                "data": data["data"],
                "timestamp": data["timestamp"],
                "createdAt": data["created_at"],
                "updatedAt": data["updated_at"],
            }
        return data

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> "MomentData":
        """Create a MomentData instance from a dictionary.

        Args:
            data: Dictionary containing moment data
            user_id: Optional user ID to use if not present in data

        Returns:
            MomentData: New instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Handle both snake_case and camelCase keys
        activity_id = data.get("activity_id") or data.get(
            "activityId"
        )
        timestamp = (
            data.get("timestamp") or datetime.utcnow()
        )
        created_at = data.get("created_at") or data.get(
            "createdAt"
        )
        updated_at = data.get("updated_at") or data.get(
            "updatedAt"
        )

        # Get user_id from data or use the provided one
        data_user_id = data.get("user_id") or data.get(
            "userId"
        )
        final_user_id = data_user_id or user_id

        if not activity_id:
            raise ValueError("activity_id is required")

        if not final_user_id:
            raise ValueError("user_id is required")

        return cls(
            id=data.get("id"),
            activity_id=activity_id,
            user_id=final_user_id,
            data=data.get("data", {}),
            timestamp=timestamp,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def from_orm(cls, orm_model: Any) -> "MomentData":
        """Create a MomentData instance from an ORM model.

        Args:
            orm_model: SQLAlchemy model instance

        Returns:
            MomentData: New instance
        """
        return cls(
            id=orm_model.id,
            activity_id=orm_model.activity_id,
            user_id=orm_model.user_id,
            data=orm_model.data,
            timestamp=orm_model.timestamp,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )
