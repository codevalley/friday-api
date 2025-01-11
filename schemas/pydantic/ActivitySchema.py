from datetime import datetime
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field, ConfigDict

from domain.activity import ActivityData, MomentData
from schemas.pydantic.PaginationSchema import (
    PaginationResponse,
)


class ActivityBase(BaseModel):
    """Base schema for Activity."""

    name: str = Field(
        ..., description="Name of the activity"
    )
    description: str = Field(
        ..., description="Description of the activity"
    )
    activity_schema: Dict[str, Any] = Field(
        ..., description="JSON schema for activity data"
    )
    icon: str = Field(
        ..., description="Icon for the activity"
    )
    color: str = Field(
        ..., description="Color for the activity"
    )


class ActivityCreate(ActivityBase):
    """Schema for creating an Activity."""

    def to_domain(self, user_id: str) -> ActivityData:
        """Convert to domain model.

        Args:
            user_id: ID of the user creating the activity

        Returns:
            ActivityData: Domain model instance with validated data
        """
        data = self.model_dump()
        data["user_id"] = user_id
        data["processing_status"] = "not_processed"
        return ActivityData.from_dict(data)


class ActivityUpdate(BaseModel):
    """Schema for updating an Activity."""

    name: Optional[str] = Field(
        None, description="Name of the activity"
    )
    description: Optional[str] = Field(
        None, description="Description of the activity"
    )
    activity_schema: Optional[Dict[str, Any]] = Field(
        None, description="JSON schema for activity data"
    )
    icon: Optional[str] = Field(
        None, description="Icon for the activity"
    )
    color: Optional[str] = Field(
        None, description="Color for the activity"
    )

    def to_domain(
        self, existing: ActivityData
    ) -> ActivityData:
        """Convert to domain model, using existing data for missing fields."""
        return ActivityData(
            id=existing.id,
            name=self.name or existing.name,
            description=self.description
            or existing.description,
            activity_schema=self.activity_schema
            or existing.activity_schema,
            icon=self.icon or existing.icon,
            color=self.color or existing.color,
            user_id=existing.user_id,
            moment_count=existing.moment_count,
            moments=existing.moments,
            created_at=existing.created_at,
            updated_at=datetime.now(),
        )


class MomentResponse(BaseModel):
    """Response schema for Moment."""

    id: int
    activity_id: int
    data: Dict[str, Any]
    timestamp: datetime
    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_domain(
        cls, domain: MomentData
    ) -> "MomentResponse":
        """Create from domain model."""
        return cls(
            id=domain.id,
            activity_id=domain.activity_id,
            data=domain.data,
            timestamp=domain.timestamp,
            user_id=domain.user_id,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    model_config = ConfigDict(from_attributes=True)


class ActivityResponse(BaseModel):
    """Response schema for Activity."""

    id: int
    name: str
    description: str
    activity_schema: Dict[str, Any]
    icon: str
    color: str
    user_id: str
    moment_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    moments: Optional[List[MomentResponse]] = None
    processing_status: str = Field(
        default="NOT_PROCESSED",
        description="Current processing status",
    )
    schema_render: Optional[Dict[str, Any]] = Field(
        None,
        description="Rendering suggestions from AI",
    )
    processed_at: Optional[datetime] = Field(
        None,
        description="When processing completed",
    )

    @classmethod
    def from_domain(
        cls, domain: ActivityData
    ) -> "ActivityResponse":
        """Create from domain model."""
        data = {
            "id": domain.id,
            "name": domain.name,
            "description": domain.description,
            "activity_schema": domain.activity_schema,
            "icon": domain.icon,
            "color": domain.color,
            "user_id": domain.user_id,
            "moment_count": domain.moment_count,
            "created_at": domain.created_at,
            "updated_at": domain.updated_at,
            "processing_status": domain.processing_status,
            "schema_render": domain.schema_render,
            "processed_at": domain.processed_at,
        }
        if domain.moments and len(domain.moments) > 0:
            data["moments"] = [
                MomentResponse.from_domain(m)
                for m in domain.moments
            ]
        return cls(**data)

    model_config = ConfigDict(from_attributes=True)


class ActivityList(PaginationResponse):
    """Response schema for list of Activities."""

    items: List[ActivityResponse]

    @classmethod
    def from_domain(
        cls, items: List[ActivityData], page: int, size: int
    ) -> "ActivityList":
        """Create from domain models."""
        return cls(
            items=[
                ActivityResponse.from_domain(item)
                for item in items
            ],
            total=len(items),
            page=page,
            size=size,
            pages=(len(items) + size - 1) // size,
        )


class ProcessingStatusResponse(BaseModel):
    """Response model for activity processing status."""

    status: str = Field(
        description="Current processing status",
        examples=[
            "PENDING",
            "PROCESSING",
            "COMPLETED",
            "FAILED",
            "SKIPPED",
        ],
    )
    processed_at: Optional[datetime] = Field(
        None,
        description="When processing completed (if done)",
    )
    schema_render: Optional[Dict[str, Any]] = Field(
        None,
        description="Rendering suggestions (if done)",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "status": "COMPLETED",
                "processed_at": "2024-01-11T12:00:00Z",
                "schema_render": {
                    "type": "form",
                    "layout": "vertical",
                    "field_groups": [
                        {
                            "name": "basic_info",
                            "fields": [
                                "title",
                                "description",
                            ],
                        }
                    ],
                },
            }
        }


class RetryResponse(BaseModel):
    """Response model for retry processing."""

    job_id: str = Field(
        description="ID of the queued job",
        examples=["job-123"],
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "job_id": "job-123",
            }
        }
