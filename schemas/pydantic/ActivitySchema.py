from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import Field, validator, ConfigDict

from schemas.base.activity_schema import ActivityData
from schemas.pydantic.CommonSchema import (
    BaseSchema,
    PaginatedResponse,
)


# Common model configuration
model_config = ConfigDict(
    from_attributes=True,  # Enable ORM mode
    json_encoders={
        datetime: lambda v: v.isoformat()  # Format datetime as ISO string
    },
)


class ActivityBase(BaseSchema):
    """Base schema for Activity with common attributes.

    Attributes:
        name: Display name of the activity
        description: Detailed description of what this activity represents
        activity_schema: JSON Schema for validating moment data
        icon: Visual representation identifier (emoji)
        color: Color code for UI consistency (hex format: #RRGGBB)
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Display name of the activity",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Detailed description of what this activity represents",
    )
    activity_schema: Dict[str, Any] = Field(
        ...,
        description=(
            "JSON Schema that defines the structure and validation rules "
            "for moment data"
        ),
    )
    icon: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Visual representation identifier (emoji)",
    )
    color: str = Field(
        ...,
        min_length=7,
        max_length=7,
        description="Color code for UI consistency (hex format: #RRGGBB)",
        example="#4A90E2",
    )

    model_config = model_config

    @validator("activity_schema")
    def validate_activity_schema(
        cls, v: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that activity_schema is a valid JSON Schema.

        Args:
            v: The activity schema to validate

        Returns:
            The validated activity schema

        Raises:
            ValueError: If schema is invalid
        """
        if not isinstance(v, dict):
            raise ValueError(
                "Activity schema must be a valid JSON object"
            )

        # Basic schema validation
        required_fields = {"type", "properties"}
        if not all(field in v for field in required_fields):
            raise ValueError(
                f"Activity schema must contain: {required_fields}"
            )

        if v.get("type") != "object":
            raise ValueError(
                "Activity schema root type must be 'object'"
            )

        return v

    def to_domain(self) -> ActivityData:
        """Convert to domain model.

        Returns:
            ActivityData: Domain model instance with validated data
        """
        return ActivityData.from_dict(self.model_dump())


class ActivityCreate(ActivityBase):
    """Schema for creating a new Activity.

    Attributes:
        user_id: Optional ID of the user creating the activity
    """

    user_id: Optional[str] = Field(
        None,
        description="ID of the user creating the activity",
    )


class ActivityUpdate(BaseSchema):
    """Schema for updating an existing Activity.

    All fields are optional since this is used for partial updates.

    Attributes:
        name: Optional new name for the activity
        description: Optional new description
        activity_schema: Optional new JSON Schema
        icon: Optional new icon
        color: Optional new color code
    """

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Display name of the activity",
    )
    description: Optional[str] = Field(
        None,
        min_length=1,
        max_length=1000,
        description="Detailed description of what this activity represents",
    )
    activity_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON Schema that defines the structure of moment data",
    )
    icon: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Visual representation identifier",
    )
    color: Optional[str] = Field(
        None,
        min_length=7,
        max_length=7,
        description="Color code for UI consistency (hex format: #RRGGBB)",
    )

    model_config = model_config

    def to_domain(
        self, existing: ActivityData
    ) -> ActivityData:
        """Convert to domain model, preserving existing data.

        Args:
            existing: Existing activity data to update

        Returns:
            ActivityData: Updated domain model instance
        """
        update_dict = self.model_dump(exclude_unset=True)
        existing_dict = existing.to_dict()
        existing_dict.update(update_dict)
        return ActivityData.from_dict(existing_dict)


class ActivityResponse(ActivityBase):
    """Full activity response model with all fields.

    Attributes:
        id: Unique identifier for the activity
        user_id: ID of the user who created the activity
        moment_count: Number of moments using this activity
        created_at: When the activity was created
        updated_at: When the activity was last updated
    """

    id: int = Field(
        ...,
        description="Unique identifier for the activity",
    )
    user_id: str = Field(
        ...,
        description="ID of the user who created the activity",
    )
    moment_count: int = Field(
        0,
        ge=0,
        description="Number of moments using this activity",
    )
    created_at: datetime = Field(
        ..., description="When the activity was created"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="When the activity was last updated",
    )

    model_config = model_config

    @classmethod
    def from_domain(
        cls, activity: ActivityData
    ) -> "ActivityResponse":
        """Create from domain model.

        Args:
            activity: Domain model instance to convert

        Returns:
            ActivityResponse: Response model instance
        """
        return cls(**activity.to_dict())


class ActivityList(PaginatedResponse[ActivityResponse]):
    """Paginated list of activities."""

    model_config = model_config
