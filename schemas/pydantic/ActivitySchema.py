from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field, validator
import re
from schemas.base.activity_schema import ActivityData


class ActivityBase(BaseModel):
    """Base schema for Activity with common attributes"""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(
        ..., min_length=1, max_length=1000
    )
    activity_schema: Dict[str, Any] = Field(
        ...,
        description="JSON Schema that defines the structure of moment data",
    )
    icon: str = Field(..., min_length=1, max_length=255)
    color: str = Field(..., min_length=1, max_length=7)

    def to_domain(self) -> ActivityData:
        """Convert to domain model"""
        return ActivityData.from_dict(self.dict())

    @validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate that color is a valid hex color code"""
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError(
                "Color must be a valid hex color code (e.g., #4A90E2)"
            )
        return v


class ActivityCreate(ActivityBase):
    """Schema for creating a new Activity"""

    user_id: Optional[str] = Field(
        None,
        description="ID of the user creating the activity",
    )


class ActivityUpdate(BaseModel):
    """Schema for updating an existing Activity"""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255
    )
    description: Optional[str] = Field(
        None, min_length=1, max_length=1000
    )
    activity_schema: Optional[Dict[str, Any]] = None
    icon: Optional[str] = Field(
        None, min_length=1, max_length=255
    )
    color: Optional[str] = Field(
        None, min_length=1, max_length=7
    )

    def to_domain(
        self, existing: ActivityData
    ) -> ActivityData:
        """Convert to domain model, preserving existing data"""
        update_dict = self.dict(exclude_unset=True)
        existing_dict = existing.to_dict()
        existing_dict.update(update_dict)
        return ActivityData.from_dict(existing_dict)

    @validator("color")
    @classmethod
    def validate_color(
        cls, v: Optional[str]
    ) -> Optional[str]:
        """Validate that color is a valid hex color code if provided"""
        if v is not None and not re.match(
            r"^#[0-9A-Fa-f]{6}$", v
        ):
            raise ValueError(
                "Color must be a valid hex color code (e.g., #4A90E2)"
            )
        return v


class ActivityResponse(BaseModel):
    """Schema for Activity response"""

    id: int
    name: str
    description: str
    activity_schema: Dict[str, Any]
    icon: str
    color: str
    user_id: str
    moment_count: int = 0

    @classmethod
    def from_domain(
        cls, activity: ActivityData
    ) -> "ActivityResponse":
        """Create from domain model"""
        return cls(**activity.to_dict())

    class Config:
        from_attributes = True


class ActivityList(BaseModel):
    """Schema for listing activities with pagination metadata"""

    items: List[ActivityResponse]
    total: int
    page: int = Field(
        ge=1,
        description="Current page number (1-based)",
    )
    size: int = Field(
        ge=1,
        le=100,
        description="Number of items per page (max 100)",
    )
    pages: int = Field(
        description="Total number of pages",
    )

    @validator("pages", pre=True)
    @classmethod
    def calculate_pages(cls, v: int, values: dict) -> int:
        """Calculate total pages based on total items and page size"""
        if "total" in values and "size" in values:
            return (
                values["total"] + values["size"] - 1
            ) // values["size"]
        return v

    class Config:
        from_attributes = True
