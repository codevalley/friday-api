from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
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

    @validator("timestamp", pre=True)
    def default_timestamp(cls, v):
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
        orm_mode = True


class MomentList(BaseModel):
    """Schema for listing moments with pagination metadata"""

    items: list[MomentResponse]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        orm_mode = True
