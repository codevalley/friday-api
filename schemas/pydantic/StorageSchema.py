"""Storage-related schemas."""

from pydantic import BaseModel, Field


class StorageUsageResponse(BaseModel):
    """Response model for storage usage."""

    usage_bytes: int = Field(
        ...,
        description="Total storage usage in bytes",
        example=1024,
    )
