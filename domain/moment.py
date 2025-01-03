"""Domain model for Moment."""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import (
    Dict,
    Any,
    Optional,
    TypeVar,
    Type,
    Set,
    Union,
)

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
    A moment can optionally reference a note for additional context.

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
        note_id: Optional ID of an associated note
        id: Unique identifier for the moment (optional)
        created_at: When this record was created (optional)
        updated_at: When this record was last updated (optional)
    """

    activity_id: int
    user_id: str
    data: Dict[str, Any]
    timestamp: datetime
    note_id: Optional[int] = None
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
            MomentTimestampError: If timestamp validation fails
        """
        if not isinstance(self.timestamp, datetime):
            raise MomentTimestampError(
                "timestamp must be a datetime object"
            )

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

    def _validate_nested_data(
        self, data: Any, visited: Set[int] = None
    ) -> None:
        """Validate nested data structure for circular references.

        Args:
            data: The data structure to validate
            visited: Set of object ids already visited

        Raises:
            MomentDataError: If a circular reference is detected
        """
        if visited is None:
            visited = set()

        # Check for circular references
        data_id = id(data)
        if data_id in visited:
            raise MomentDataError(
                "Invalid data structure: circular reference detected"
            )

        # Only track references for mutable types that could be circular
        if isinstance(data, (dict, list)):
            visited.add(data_id)

            if isinstance(data, dict):
                for value in data.values():
                    self._validate_nested_data(
                        value, visited
                    )
            else:  # list
                for item in data:
                    self._validate_nested_data(
                        item, visited
                    )

    def validate(self) -> None:
        """Validate the moment data.

        Raises:
            MomentValidationError: If validation fails
            MomentTimestampError: If timestamp validation fails
            MomentDataError: If data validation fails
        """
        # Basic field validations
        if not isinstance(self.activity_id, int):
            raise MomentValidationError(
                "activity_id must be a positive integer"
            )
        if self.activity_id <= 0:
            raise MomentValidationError(
                "activity_id must be a positive integer"
            )

        if (
            not isinstance(self.user_id, str)
            or not self.user_id
        ):
            raise MomentValidationError(
                "user_id must be a non-empty string"
            )

        if not isinstance(self.data, dict):
            raise MomentDataError(
                "data must be a dictionary"
            )

        # Validate nested data structure
        try:
            self._validate_nested_data(self.data)
        except MomentDataError as e:
            raise e

        # Validate note_id if present
        if self.note_id is not None:
            if not isinstance(self.note_id, int):
                raise MomentValidationError(
                    "note_id must be a positive integer"
                )
            if self.note_id <= 0:
                raise MomentValidationError(
                    "note_id must be a positive integer"
                )

        # Validate timestamp
        if not isinstance(self.timestamp, datetime):
            raise MomentTimestampError(
                "timestamp must be a datetime object"
            )

        if self.timestamp.tzinfo is None:
            raise MomentTimestampError(
                "timestamp must be timezone-aware"
            )

        # Validate timestamp range
        now = datetime.now(timezone.utc)
        if self.timestamp > now + timedelta(days=1):
            raise MomentTimestampError(
                "timestamp cannot be more than 1 day in the future"
            )

        ten_years_ago = now - timedelta(days=365 * 10)
        if self.timestamp < ten_years_ago:
            raise MomentTimestampError(
                "timestamp cannot be more than 10 years in the past"
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
            "note_id": self.note_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-compatible dictionary.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary representation
        """
        return {
            "id": str(self.id) if self.id else None,
            "activity_id": self.activity_id,
            "user_id": self.user_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "note_id": self.note_id,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            ),
        }

    @classmethod
    def from_dict(
        cls: Type[T],
        data: Union[Dict[str, Any], "MomentData"],
        user_id: Optional[str] = None,
    ) -> T:
        """Create a MomentData instance from a dictionary.

        Args:
            data: Dictionary containing moment data or MomentData instance
            user_id: Optional user ID to use if not present in data

        Returns:
            MomentData: New instance with validated data

        Raises:
            ValueError: If required fields are missing or invalid
        """
        if isinstance(data, MomentData):
            return data

        # Handle both snake_case and camelCase keys
        activity_id = data.get("activity_id") or data.get(
            "activityId"
        )
        moment_data = data.get("data") or data.get(
            "momentData"
        )
        timestamp = data.get("timestamp")
        note_id = data.get("note_id") or data.get("noteId")
        moment_user_id = data.get("user_id") or data.get(
            "userId"
        )

        # Use provided user_id if not in data
        if not moment_user_id and user_id:
            moment_user_id = user_id

        return cls(
            activity_id=activity_id,
            user_id=moment_user_id,
            data=moment_data,
            timestamp=timestamp,
            note_id=note_id,
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
            note_id=orm_model.note_id,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )
