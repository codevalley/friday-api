from datetime import datetime, UTC
from typing import Any, Dict, Optional

from pydantic import Field, field_validator, ConfigDict

from domain.moment import MomentData
from schemas.pydantic.ActivitySchema import ActivityResponse
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


class MomentBase(BaseSchema):
    """Base schema for Moment with common attributes.

    Attributes:
        activity_id: ID of the activity this moment belongs to
        data: Activity-specific data matching activity's schema
        timestamp: UTC timestamp of when this moment occurred
    """

    activity_id: int = Field(
        ...,
        gt=0,
        description="ID of the activity this moment belongs to",
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Activity-specific data matching activity's schema",
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="UTC timestamp of when this moment occurred",
    )

    model_config = model_config

    @field_validator("timestamp")
    @classmethod
    def default_timestamp(
        cls, v: Optional[datetime]
    ) -> datetime:
        """Set default timestamp to current UTC time if not provided.

        Args:
            v: The timestamp value to validate

        Returns:
            datetime: The validated timestamp or current UTC time
        """
        return v or datetime.now(UTC)

    def to_domain(
        self, user_id: Optional[str] = None
    ) -> MomentData:
        """Convert to domain model.

        Args:
            user_id: Optional user ID to use when creating the domain model

        Returns:
            MomentData: Domain model instance with validated data
        """
        data = self.model_dump()
        if user_id:
            data["user_id"] = user_id
        return MomentData.from_dict(data, user_id=user_id)


class MomentCreate(MomentBase):
    """Schema for creating a new Moment.

    Inherits all fields from MomentBase.
    """

    def to_domain(self, user_id: str) -> MomentData:
        """Convert to domain model.

        Args:
            user_id: ID of the user creating the moment

        Returns:
            MomentData: Domain model instance with validated data
        """
        data = self.model_dump()
        data["user_id"] = user_id
        return MomentData.from_dict(data)


class MomentUpdate(BaseSchema):
    """Schema for updating an existing Moment.

    All fields are optional since this is used for partial updates.

    Attributes:
        data: Optional new activity-specific data
        timestamp: Optional new timestamp
    """

    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Activity-specific data matching activity's schema",
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="UTC timestamp of when this moment occurred",
    )

    model_config = model_config

    def to_domain(self, existing: MomentData) -> MomentData:
        """Convert to domain model, preserving existing data.

        Args:
            existing: Existing moment data to update

        Returns:
            MomentData: Updated domain model instance
        """
        update_dict = self.model_dump(exclude_unset=True)
        existing_dict = existing.to_dict()
        existing_dict.update(update_dict)
        return MomentData.from_dict(existing_dict)


class MomentResponse(MomentBase):
    """Full moment response model with all fields.

    Attributes:
        id: Unique identifier for the moment
        activity: Full activity response data
    """

    id: int = Field(
        ...,
        description="Unique identifier for the moment",
    )
    activity: ActivityResponse = Field(
        ...,
        description="Full activity response data",
    )

    @classmethod
    def from_domain(
        cls, moment: MomentData, activity: ActivityResponse
    ) -> "MomentResponse":
        """Create from domain model.

        Args:
            moment: Domain model instance to convert
            activity: Activity response data to include

        Returns:
            MomentResponse: Response model instance
        """
        moment_dict = moment.to_dict()
        moment_dict["activity"] = activity
        return cls(**moment_dict)


class MomentList(PaginatedResponse[MomentResponse]):
    """Paginated list of moments."""

    model_config = model_config
