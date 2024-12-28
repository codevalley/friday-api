"""Domain model for Moment."""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta, UTC
from typing import Dict, Any, Optional, TypeVar, Type

from domain.exceptions import (
    MomentValidationError,
    MomentTimestampError,
    MomentDataError,
    MomentSchemaError,
)
from utils.validation import validate_moment_data

# Type variable for the class itself
T = TypeVar("T", bound="MomentData")


@dataclass
class MomentData:
    """Domain model for Moment.

    This class represents a single moment or event recorded for an activity.
    It contains all the business logic and validation rules for moments.

    Data Flow and Conversions:
    1. API Layer: Incoming data is validated by Pydantic schemas
       (MomentCreate/MomentUpdate)
    2. Domain Layer: Data is converted to MomentData using to_domain()
       methods
    3. Database Layer: MomentData is converted to ORM models
       using from_dict()
    4. Response: ORM models are converted back to MomentData using from_orm()
    5. API Response: MomentData is converted to response schemas
       using from_domain()

    Attributes:
        activity_id: ID of the activity this moment belongs to
        user_id: ID of the user who created this moment
        data: JSON data specific to the activity type
        timestamp: When this moment occurred
        id: Unique identifier for the moment (optional)
        created_at: When this record was created (optional)
        updated_at: When this record was last updated (optional)
    """

    activity_id: int
    user_id: str
    data: Dict[str, Any]
    timestamp: datetime
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate the moment data after initialization."""
        self.validate()

    def validate_timestamp(self) -> None:
        """Validate timestamp constraints.

        Ensures the timestamp is:
        1. Not more than 1 day in the future
        2. Not more than 10 years in the past
        3. Timezone-aware

        Raises:
            ValueError: If timestamp validation fails
        """
        if self.timestamp.tzinfo is None:
            raise MomentTimestampError(
                "timestamp must be timezone-aware"
            )

        now = datetime.now(timezone.utc)
        max_future = now + timedelta(days=1)
        min_past = now - timedelta(days=365 * 10)

        if self.timestamp > max_future:
            raise MomentTimestampError(
                "timestamp cannot be more than 1 day in the future"
            )

        if self.timestamp < min_past:
            raise MomentTimestampError(
                "timestamp cannot be more than 10 years in the past"
            )

    def validate(self) -> None:
        """Validate the moment data.

        This method performs comprehensive validation of all fields
        to ensure data integrity and consistency.

        Raises:
            ValueError: If any validation fails
        """
        if (
            not isinstance(self.activity_id, int)
            or self.activity_id <= 0
        ):
            raise MomentValidationError(
                "activity_id must be a positive integer"
            )

        if not self.user_id or not isinstance(
            self.user_id, str
        ):
            raise MomentValidationError(
                "user_id must be a non-empty string"
            )

        if not isinstance(self.data, dict):
            raise MomentDataError(
                "data must be a dictionary"
            )

        # Validate data structure
        try:
            self._validate_nested_data(self.data)
        except ValueError as e:
            raise MomentDataError(
                f"Invalid data structure: {str(e)}"
            )

        if not isinstance(self.timestamp, datetime):
            raise MomentTimestampError(
                "timestamp must be a datetime object"
            )

        # Validate timestamp constraints
        self.validate_timestamp()

        # Validate microsecond precision
        if self.timestamp.microsecond >= 1000000:
            raise MomentTimestampError(
                "microsecond must be in 0..999999"
            )

        if self.id is not None and (
            not isinstance(self.id, int) or self.id <= 0
        ):
            raise MomentValidationError(
                "id must be a positive integer"
            )

        if self.created_at is not None and not isinstance(
            self.created_at, datetime
        ):
            raise MomentValidationError(
                "created_at must be a datetime object"
            )

        if self.updated_at is not None and not isinstance(
            self.updated_at, datetime
        ):
            raise MomentValidationError(
                "updated_at must be a datetime object"
            )

    def _validate_nested_data(
        self, data: Dict[str, Any], depth: int = 0
    ) -> None:
        """Validate nested data structures.

        Args:
            data: Data to validate
            depth: Current recursion depth

        Raises:
            ValueError: If validation fails
        """
        if depth > 10:
            raise ValueError("circular reference detected")

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    self._validate_nested_data(
                        value, depth + 1
                    )
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._validate_nested_data(
                        item, depth + 1
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
        try:
            validate_moment_data(self.data, activity_schema)
        except Exception as e:
            raise MomentSchemaError(str(e))

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
        cls: Type[T],
        data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> T:
        """Create a MomentData instance from a dictionary.

        Args:
            data: Dictionary containing moment data
            user_id: Optional user ID to use if not present in data

        Returns:
            MomentData: New instance with validated data

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Handle both snake_case and camelCase keys
        activity_id = data.get("activity_id") or data.get(
            "activityId"
        )
        timestamp = data.get("timestamp") or datetime.now(
            UTC
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
    def from_orm(cls: Type[T], orm_model: Any) -> T:
        """Create a MomentData instance from an ORM model.

        Args:
            orm_model: SQLAlchemy model instance

        Returns:
            MomentData: New instance with validated data from the database
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
