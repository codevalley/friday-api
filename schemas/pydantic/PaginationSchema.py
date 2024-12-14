from pydantic import BaseModel, Field, validator


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
