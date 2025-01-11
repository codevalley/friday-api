"""Domain model for Activity."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, TypeVar
from enum import Enum

from domain.moment import MomentData
from domain.exceptions import ActivityValidationError
from domain.values import Color, ActivitySchema
from utils.validation import validate_moment_data

T = TypeVar("T", bound="ActivityData")


class ProcessingStatus(str, Enum):
    """Status of activity schema processing."""

    NOT_PROCESSED = "NOT_PROCESSED"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class ActivityData:
    """Domain model for Activity.

    This class represents an activity type in the system and contains
    all business logic and validation rules for activities.

    Data Flow and Conversions:
    1. API Layer: Incoming data is validated by Pydantic schemas
       (ActivityCreate/ActivityUpdate)
    2. Domain Layer: Data is converted to ActivityData using to_domain()
       methods
    3. Database Layer: ActivityData is converted to ORM models
       using from_dict()
    4. Response: ORM models are converted back to ActivityData using from_orm()
    5. API Response: ActivityData is converted to response schemas
       using from_domain()

    Attributes:
        name: Name of the activity type
        description: Description of what this activity represents
        activity_schema: JSON Schema defining the structure of moment data
        icon: Emoji or icon representing this activity
        color: Hex color code for UI display
        user_id: ID of the user who owns this activity
        id: Unique identifier for this activity (optional)
        moment_count: Number of moments of this activity type
        moments: List of moments of this activity type (optional)
        processing_status: Status of schema render processing
        schema_render: Rendered schema suggestions from AI
        processed_at: When the schema was last processed
        created_at: When this record was created (optional)
        updated_at: When this record was last updated (optional)
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
    processing_status: str = "NOT_PROCESSED"
    schema_render: Optional[Dict[str, Any]] = None
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    _color_obj: Optional[Color] = None
    _schema_obj: Optional[ActivitySchema] = None

    def __post_init__(self):
        """Validate the activity data after initialization."""
        self._color_obj = Color.from_string(self.color)
        self._schema_obj = ActivitySchema.from_dict(
            self.activity_schema
        )
        self.validate()

    def validate(self) -> None:
        """Validate the activity data.

        This method performs comprehensive validation of all fields
        to ensure data integrity and consistency.

        Raises:
            ValueError: If any validation fails
        """
        if not self.name or not isinstance(self.name, str):
            raise ActivityValidationError.invalid_field_value(
                "name", "name must be a non-empty string"
            )

        if not self.description or not isinstance(
            self.description, str
        ):
            raise ActivityValidationError.invalid_field_value(
                "description",
                "description must be a non-empty string",
            )

        if not isinstance(self.activity_schema, dict):
            raise ActivityValidationError.invalid_field_value(
                "activity_schema",
                "activity_schema must be a dictionary",
            )

        # Validate activity schema structure
        self._validate_activity_schema(self.activity_schema)

        if not self.icon or not isinstance(self.icon, str):
            raise ActivityValidationError.invalid_field_value(
                "icon", "icon must be a non-empty string"
            )

        if not self.user_id or not isinstance(
            self.user_id, str
        ):
            raise ActivityValidationError.invalid_field_value(
                "user_id",
                "user_id must be a non-empty string",
            )

        if self.id is not None and (
            not isinstance(self.id, int) or self.id <= 0
        ):
            raise ActivityValidationError.invalid_field_value(
                "id", "id must be a positive integer"
            )

        if (
            not isinstance(self.moment_count, int)
            or self.moment_count < 0
        ):
            raise ActivityValidationError.invalid_field_value(
                "moment_count",
                "moment_count must be a non-negative integer",
            )

        if self.moments is not None:
            if not isinstance(self.moments, list):
                raise ActivityValidationError.invalid_field_value(
                    "moments",
                    "moments must be a list or None",
                )

            for moment in self.moments:
                if not isinstance(moment, MomentData):
                    raise ActivityValidationError.invalid_field_value(
                        "moments",
                        "invalid moment data in list",
                    )

            if self.moment_count != len(self.moments):
                raise ActivityValidationError.invalid_field_value(
                    "moment_count",
                    "moment count mismatch: count does not match list length",
                )

        if self.created_at is not None:
            if not isinstance(self.created_at, datetime):
                raise ActivityValidationError.invalid_field_value(
                    "created_at",
                    "created_at must be a datetime object",
                )
            if self.created_at.tzinfo is None:
                self.created_at = self.created_at.replace(
                    tzinfo=timezone.utc
                )

        if self.updated_at is not None:
            if not isinstance(self.updated_at, datetime):
                raise ActivityValidationError.invalid_field_value(
                    "updated_at",
                    "updated_at must be a datetime object",
                )
            if self.updated_at.tzinfo is None:
                self.updated_at = self.updated_at.replace(
                    tzinfo=timezone.utc
                )

        if self.processed_at is not None:
            if not isinstance(self.processed_at, datetime):
                raise ActivityValidationError.invalid_field_value(
                    "processed_at",
                    "processed_at must be a datetime object",
                )
            if self.processed_at.tzinfo is None:
                self.processed_at = (
                    self.processed_at.replace(
                        tzinfo=timezone.utc
                    )
                )

        # Validate processing_status
        valid_statuses = {
            "NOT_PROCESSED",
            "PENDING",
            "PROCESSING",
            "COMPLETED",
            "FAILED",
            "SKIPPED",
        }
        if self.processing_status not in valid_statuses:
            raise ActivityValidationError.invalid_field_value(
                "processing_status",
                f"processing_status must be one of: "
                f"{', '.join(valid_statuses)}",
            )

        # Validate schema_render if status is COMPLETED
        if (
            self.processing_status == "COMPLETED"
            and self.schema_render is None
        ):
            raise ActivityValidationError.invalid_field_value(
                "schema_render",
                "schema_render must be set when status is COMPLETED",
            )

        # Validate processed_at if status is COMPLETED
        if (
            self.processing_status == "COMPLETED"
            and self.processed_at is None
        ):
            raise ActivityValidationError.invalid_field_value(
                "processed_at",
                "processed_at must be set when status is COMPLETED",
            )

    def _validate_color(self) -> None:
        """Validate color format.

        This is now handled by the Color value object in __post_init__
        """
        pass

    @property
    def color_value(self) -> Color:
        """Get the color as a Color value object."""
        return self._color_obj

    def _validate_activity_schema(
        self, schema: Dict[str, Any]
    ) -> None:
        """Validate activity schema structure.

        Args:
            schema: Schema to validate

        Raises:
            ActivityValidationError: If schema is invalid
        """
        # Schema validation is now handled by ActivitySchema value object
        pass

    @property
    def schema_value(self) -> ActivitySchema:
        """Get the schema as an ActivitySchema value object."""
        return self._schema_obj

    def validate_moment_data(
        self, data: Dict[str, Any]
    ) -> None:
        """Validate moment data against this activity's schema.

        Args:
            data: Moment data to validate

        Raises:
            ValueError: If data does not match the schema
        """
        try:
            validate_moment_data(
                data, self.schema_value.to_dict()
            )
        except Exception as e:
            raise ValueError(
                f"Invalid moment data: {str(e)}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the activity data to a dictionary.

        This method is used when we need to serialize the domain model,
        typically for API responses or database operations.

        Returns:
            Dict[str, Any]: Dictionary representation of the activity,
                           with all fields properly serialized
        """
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "activity_schema": self.schema_value.to_dict(),
            "icon": self.icon,
            "color": str(self.color_value),
            "user_id": self.user_id,
            "moment_count": self.moment_count,
            "processing_status": self.processing_status,
            "schema_render": self.schema_render,
            "processed_at": self.processed_at,
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
        cls,
        data: Dict[str, Any],
    ) -> "ActivityData":
        """Create an ActivityData instance from a dictionary.

        This method is used when we receive data from an API request
        or need to reconstruct the domain model from stored data.

        The method handles moment_count in the following ways:
        1. If moment_count is provided in the data, use that value
        2. If moments list provided but no moment_count, use length of moments
        3. If neither is provided, default to 0

        Args:
            data: Dictionary containing activity data with the fields:
                - name: Display name of the activity (required)
                - description: Detailed description (required)
                - activity_schema: JSON Schema for validating moment data
                  (required)
                - icon: Display icon (required)
                - color: Hex color code for UI (required)
                - user_id: ID of the user who created this activity (required)
                - id: Unique identifier for the activity (optional)
                - moment_count: Number of moments (optional)
                - moments: List of moment data (optional)
                - processing_status: Status of schema render processing
                - schema_render: Rendered schema suggestions from AI
                - processed_at: When the schema was last processed
                - created_at: Creation timestamp (optional)
                - updated_at: Last update timestamp (optional)

        Returns:
            ActivityData: New instance with validated data

        Raises:
            ValueError: If required fields are missing or invalid
            ValueError: If moment_count doesn't match moments list length
        """
        moments_data = data.get("moments", [])
        moments = (
            [MomentData.from_dict(m) for m in moments_data]
            if moments_data
            else None
        )

        # Set moment_count based on moments list if not provided
        moment_count = data.get("moment_count")
        if moments is not None and moment_count is None:
            moment_count = len(moments)

        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data["description"],
            activity_schema=data["activity_schema"],
            icon=data["icon"],
            color=data["color"],
            user_id=data["user_id"],
            moment_count=moment_count or 0,
            moments=moments,
            processing_status=data.get(
                "processing_status", "NOT_PROCESSED"
            ),
            schema_render=data.get("schema_render"),
            processed_at=data.get("processed_at"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def from_orm(cls, orm_model: Any) -> "ActivityData":
        """Create an ActivityData instance from an ORM model.

        This method is the bridge between the database layer and domain layer.
        It ensures that data from the database is properly
        validated before use.

        Args:
            orm_model: SQLAlchemy model instance

        Returns:
            ActivityData: New instance with validated data from the database
        """
        moments = None
        if (
            hasattr(orm_model, "moments")
            and orm_model.moments
        ):
            # Ensure each moment's timestamps are timezone-aware
            for moment in orm_model.moments:
                if moment.timestamp.tzinfo is None:
                    moment.timestamp = (
                        moment.timestamp.replace(
                            tzinfo=timezone.utc
                        )
                    )
                if (
                    moment.created_at
                    and moment.created_at.tzinfo is None
                ):
                    moment.created_at = (
                        moment.created_at.replace(
                            tzinfo=timezone.utc
                        )
                    )
                if (
                    moment.updated_at
                    and moment.updated_at.tzinfo is None
                ):
                    moment.updated_at = (
                        moment.updated_at.replace(
                            tzinfo=timezone.utc
                        )
                    )

            moments = [
                MomentData.from_orm(m)
                for m in orm_model.moments
            ]

        # Ensure activity timestamps are timezone-aware
        created_at = orm_model.created_at
        if created_at and created_at.tzinfo is None:
            created_at = created_at.replace(
                tzinfo=timezone.utc
            )

        updated_at = orm_model.updated_at
        if updated_at and updated_at.tzinfo is None:
            updated_at = updated_at.replace(
                tzinfo=timezone.utc
            )

        processed_at = orm_model.processed_at
        if processed_at and processed_at.tzinfo is None:
            processed_at = processed_at.replace(
                tzinfo=timezone.utc
            )

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
            processing_status=orm_model.processing_status,
            schema_render=orm_model.schema_render,
            processed_at=processed_at,
            created_at=created_at,
            updated_at=updated_at,
        )
