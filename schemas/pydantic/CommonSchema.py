from typing import (
    TypeVar,
    Generic,
    Optional,
    Union,
)
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ConfigDict,
    ValidationInfo,
)
from datetime import datetime
import re

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common validation methods"""

    @field_validator("id", check_fields=False)
    @classmethod
    def validate_id(
        cls, v: Optional[Union[int, str]]
    ) -> Optional[Union[int, str]]:
        """Validate ID is either a positive integer or a non-empty string.

        Args:
            v: The ID value to validate

        Returns:
            The validated ID value

        Raises:
            ValueError: If ID is invalid
        """
        if v is None:
            return v

        if isinstance(v, int) and v <= 0:
            raise ValueError("Integer ID must be positive")
        elif isinstance(v, str) and not v.strip():
            raise ValueError("String ID cannot be empty")
        return v

    @field_validator("user_id", check_fields=False)
    @classmethod
    def validate_user_id(
        cls, v: Optional[str]
    ) -> Optional[str]:
        """Validate user_id is a non-empty string.

        Args:
            v: The user ID to validate

        Returns:
            The validated user ID

        Raises:
            ValueError: If user ID is empty
        """
        if v is not None and not v.strip():
            raise ValueError(
                "User ID cannot be empty if provided"
            )
        return v

    @field_validator("timestamp", check_fields=False)
    @classmethod
    def validate_timestamp(
        cls, v: Optional[datetime]
    ) -> Optional[datetime]:
        """Validate timestamp is a valid datetime.

        Args:
            v: The timestamp to validate

        Returns:
            The validated timestamp

        Raises:
            ValueError: If timestamp is invalid
        """
        if v is not None and not isinstance(v, datetime):
            raise ValueError(
                "Timestamp must be a valid datetime"
            )
        return v

    @field_validator("color", check_fields=False)
    @classmethod
    def validate_color(
        cls, v: Optional[str]
    ) -> Optional[str]:
        """Validate color is a valid hex code.

        Args:
            v: The color code to validate

        Returns:
            The validated color code

        Raises:
            ValueError: If color code is invalid
        """
        if v is not None and not re.match(
            r"^#[0-9A-Fa-f]{6}$", v
        ):
            raise ValueError(
                "Color must be a valid hex color code (e.g., #4A90E2)"
            )
        return v

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        extra="forbid",  # Prevent extra fields
    )


class MessageResponse(BaseSchema):
    """Standard message response.

    Attributes:
        message: The response message
    """

    message: str


class ErrorResponse(BaseSchema):
    """Standard error response.

    Attributes:
        detail: The error details
    """

    detail: str


class ErrorDetail(BaseSchema):
    """Error detail response.

    Attributes:
        code: The error code
        message: Optional error message
    """

    code: str
    message: Optional[str] = None


class GenericResponse(BaseModel, Generic[T]):
    """Generic response wrapper for any data type.

    Attributes:
        data: The response data of type T
        message: Optional response message
        error: Optional error details
    """

    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[ErrorDetail] = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response.

    Attributes:
        items: List of items of type T
        total: Total number of items
        page: Current page number (1-based)
        size: Number of items per page (max 100)
        pages: Total number of pages
    """

    items: list[T]
    total: int
    page: int = Field(
        ge=1, description="Current page number (1-based)"
    )
    size: int = Field(
        ge=1, le=100, description="Items per page (max 100)"
    )
    pages: int = Field(description="Total number of pages")

    model_config = ConfigDict(
        from_attributes=True,
    )

    @field_validator("pages", mode="before")
    @classmethod
    def calculate_pages(
        cls, v: int, info: ValidationInfo
    ) -> int:
        """Calculate total pages based on total items and page size.

        Args:
            v: The current pages value
            info: Validation context information

        Returns:
            The calculated number of pages
        """
        data = info.data
        if "total" in data and "size" in data:
            return (
                data["total"] + data["size"] - 1
            ) // data["size"]
        return v
