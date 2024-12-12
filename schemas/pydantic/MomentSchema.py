from typing import Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from .ActivitySchema import ActivityResponse


class MomentBase(BaseModel):
    """Base schema for Moment with common attributes"""

    activity_id: int = Field(..., gt=0)
    data: Dict = Field(
        ...,
        description="Activity-specific data that matches the activity's schema",
    )
    timestamp: Optional[datetime] = Field(
        None, description="UTC timestamp of the moment"
    )

    @field_validator("timestamp")
    @classmethod
    def default_timestamp(
        cls, v: Optional[datetime]
    ) -> datetime:
        """Set default timestamp to current UTC time if not provided"""
        return v or datetime.utcnow()


class MomentCreate(MomentBase):
    """Schema for creating a new Moment"""

    pass


class MomentUpdate(BaseModel):
    """Schema for updating an existing Moment"""

    data: Optional[Dict] = Field(
        None,
        description="Activity-specific data that matches the activity's schema",
    )
    timestamp: Optional[datetime] = None


class MomentResponse(MomentBase):
    """Schema for Moment response"""

    id: int
    activity: ActivityResponse

    class Config:
        from_attributes = True
        json_encoders = {
            dict: lambda v: v  # Preserve dictionaries as-is
        }

    @field_validator("data")
    @classmethod
    def ensure_dict_data(cls, v):
        """Ensure data is a dictionary"""
        if hasattr(v, "data_dict"):
            return v.data_dict
        return v


class MomentList(BaseModel):
    """Schema for listing moments with pagination metadata"""

    items: List[MomentResponse]
    total: int
    page: int
    size: int

    class Config:
        from_attributes = True
