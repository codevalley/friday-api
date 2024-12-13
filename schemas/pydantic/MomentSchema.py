from typing import Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from schemas.base.moment_schema import MomentData
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

    def to_domain(self) -> MomentData:
        """Convert to domain model"""
        return MomentData.from_dict(self.model_dump())

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

    def to_domain(self, existing: MomentData) -> MomentData:
        """Convert to domain model, preserving existing data"""
        update_dict = self.model_dump(exclude_unset=True)
        existing_dict = existing.to_dict()
        existing_dict.update(update_dict)
        return MomentData.from_dict(existing_dict)


class MomentResponse(BaseModel):
    """Schema for Moment response"""

    id: int
    activity_id: int
    data: Dict
    timestamp: datetime
    activity: ActivityResponse

    @classmethod
    def from_domain(
        cls, moment: MomentData, activity: ActivityResponse
    ) -> "MomentResponse":
        """Create from domain model"""
        moment_dict = moment.to_dict()
        moment_dict["activity"] = activity
        return cls(**moment_dict)

    class Config:
        from_attributes = True


class MomentList(BaseModel):
    """Schema for listing moments with pagination metadata"""

    items: List[MomentResponse]
    total: int
    page: int
    size: int
    pages: int = Field(
        0, description="Total number of pages"
    )

    @field_validator("pages", mode="before")
    @classmethod
    def calculate_pages(cls, v: int, info) -> int:
        """Calculate total pages based on total items and page size"""
        data = info.data
        if "total" in data and "size" in data:
            return (
                data["total"] + data["size"] - 1
            ) // data["size"]
        return v

    class Config:
        from_attributes = True
