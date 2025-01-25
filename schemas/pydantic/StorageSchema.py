"""Storage-related schemas."""

from pydantic import BaseModel, Field


class StorageUsageResponse(BaseModel):
    """Schema for storage usage response."""

    used_bytes: int = Field(
        ...,
        description="Total storage used in bytes",
        example=1024,
    )
    total_bytes: int = Field(
        ...,
        description="Total storage limit in bytes",
        example=1073741824,  # 1GB default
    )
