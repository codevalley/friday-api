"""Base schema for pagination parameters and response."""

from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field, validator


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Base schema for pagination parameters"""

    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-based indexing)",
    )
    size: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of items per page (max 100)",
    )

    @validator("page")
    @classmethod
    def validate_page(cls, v: int) -> int:
        """Ensure page number is positive"""
        if v < 1:
            raise ValueError("Page number must be positive")
        return v

    @validator("size")
    @classmethod
    def validate_size(cls, v: int) -> int:
        """Ensure page size is within bounds"""
        if v < 1:
            raise ValueError("Page size must be positive")
        if v > 100:
            raise ValueError("Page size cannot exceed 100")
        return v


class PaginationResponse(BaseModel, Generic[T]):
    """Base schema for paginated responses"""

    items: List[T]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    size: int = Field(
        description="Number of items per page"
    )
    pages: int = Field(description="Total number of pages")

    class Config:
        """Pydantic config"""

        from_attributes = True
