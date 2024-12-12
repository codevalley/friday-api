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
        description="JSON Schema for validating moment data",
    )
    icon: str = Field(..., min_length=1, max_length=255)
    color: str = Field(..., min_length=1, max_length=50)

    @validator("color")
    def validate_color(cls, v):
        """Validate color format (hex, rgb, or named color)"""
        color_pattern = r"^(#[0-9a-fA-F]{6}|rgb\(\d{1,3},\s*\d{1,3},\s*\d{1,3}\)|[a-zA-Z]+)$"
        if not re.match(color_pattern, v):
            raise ValueError(
                "Invalid color format. Use hex (#RRGGBB), rgb(r,g,b), or color name"
            )
        return v

    @validator("activity_schema")
    def validate_schema(cls, v):
        """Validate that activity_schema is a valid JSON Schema"""
        required_fields = ["type", "properties"]
        if not all(field in v for field in required_fields):
            raise ValueError(
                'activity_schema must be a valid JSON Schema with "type" and "properties" fields'
            )
        return v


class ActivityCreate(ActivityBase):
    """Schema for creating a new Activity"""
    user_id: str = Field(..., description="ID of the user creating the activity")


class ActivityUpdate(ActivityBase):
    """Schema for updating an existing Activity"""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255
    )
    description: Optional[str] = Field(
        None, min_length=1, max_length=1000
    )
    activity_schema: Optional[Dict] = None
    icon: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, min_length=1, max_length=50)


class ActivityResponse(ActivityBase):
    """Schema for Activity response"""

    id: int
    user_id: str

    class Config:
        from_attributes = True  # Enable ORM mode


class ActivityList(BaseModel):
    """Schema for listing activities with pagination metadata"""

    items: List[ActivityResponse]
    total: int
    skip: int
    limit: int

    class Config:
        from_attributes = True
