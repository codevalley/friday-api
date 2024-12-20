"""Domain model for Activity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional, TypeVar
import re

from domain.moment import MomentData
from utils.validation import (
    validate_activity_schema,
    validate_moment_data,
)

T = TypeVar("T", bound="ActivityData")


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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate the activity data after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate the activity data.

        This method performs comprehensive validation of all fields
        to ensure data integrity and consistency.

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

        # Validate activity schema structure
        self._validate_activity_schema(self.activity_schema)

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

        # Validate color format
        self._validate_color()

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

        if self.moments is not None:
            if not isinstance(self.moments, list):
                raise ValueError(
                    "moments must be a list or None"
                )

            for moment in self.moments:
                if not isinstance(moment, MomentData):
                    raise ValueError(
                        "invalid moment data in list"
                    )

            if self.moment_count != len(self.moments):
                raise ValueError(
                    "moment count mismatch: count does not match list length"
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

    def _validate_color(self) -> None:
        """Validate color format.

        Raises:
            ValueError: If color format is invalid
        """
        if not self.color:
            return

        if not re.match(r"^#[0-9A-Fa-f]{6}$", self.color):
            raise ValueError(
                "color must be a valid hex code"
            )

    def _validate_activity_schema(
        self, schema: Dict[str, Any]
    ) -> None:
        """Validate activity schema structure.

        Args:
            schema: Schema to validate

        Raises:
            ValueError: If schema is invalid
        """
        # Basic schema validation
        validate_activity_schema(schema)

        # Additional domain-specific validation
        if "properties" in schema:
            if not isinstance(schema["properties"], dict):
                raise ValueError(
                    "Schema properties must be a dictionary"
                )

            # Validate property types
            for prop_name, prop_schema in schema[
                "properties"
            ].items():
                if not isinstance(prop_schema, dict):
                    raise ValueError(
                        f"Property {prop_name} schema must be a dictionary"
                    )
                # Skip type check if it's a reference
                if (
                    "$ref" not in prop_schema
                    and "type" not in prop_schema
                ):
                    raise ValueError(
                        f"Property {prop_name} must specify a type"
                    )

        if "patternProperties" in schema:
            if not isinstance(
                schema["patternProperties"], dict
            ):
                raise ValueError(
                    "Pattern properties must be a dictionary"
                )

            # Validate pattern property types
            for pattern, prop_schema in schema[
                "patternProperties"
            ].items():
                if not isinstance(prop_schema, dict):
                    raise ValueError(
                        f"Pattern {pattern} schema must be a dictionary"
                    )
                if (
                    "$ref" not in prop_schema
                    and "type" not in prop_schema
                ):
                    raise ValueError(
                        f"Pattern {pattern} must specify a type"
                    )

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
            validate_moment_data(data, self.activity_schema)
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
