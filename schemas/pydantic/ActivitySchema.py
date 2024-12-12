from typing import Dict, Optional, List
from pydantic import BaseModel, Field, validator
import re


class ActivityBase(BaseModel):
    """Base schema for Activity with common attributes"""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(
        None, min_length=1, max_length=1000
    )
    activity_schema: Dict = Field(
        ...,
        description="JSON Schema that defines the structure of moment data",
    )
    icon: str = Field(..., min_length=1, max_length=255)
    color: str = Field(..., min_length=1, max_length=50)

    @validator("color")
    def validate_color(cls, v):
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
    activity_schema: Optional[Dict] = None
    icon: Optional[str] = Field(
        None, min_length=1, max_length=255
    )
    color: Optional[str] = Field(
        None, min_length=1, max_length=50
    )


class ActivityResponse(ActivityBase):
    """Schema for Activity response"""

    id: int
    user_id: str
    moment_count: int = 0

    class Config:
        from_attributes = True
        json_encoders = {
            dict: lambda v: v  # Preserve dictionaries as-is
        }


class ActivityList(BaseModel):
    """Schema for listing activities with pagination metadata"""

    items: List[ActivityResponse]
    total: int
    skip: int
    limit: int

    class Config:
        from_attributes = True
