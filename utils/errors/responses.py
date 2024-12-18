"""Standardized error response models.

This module defines the structure of error responses returned by the API.
All error responses follow a consistent format to make error handling
easier for API consumers.
"""

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error information.

    This model represents a single error detail, which can include
    field-specific errors or general error information.

    Attributes:
        code: Machine-readable error code
        message: Human-readable error message
        field: Name of the field that caused the error (optional)
        details: Additional error details (optional)
    """

    code: str = Field(
        ..., description="Machine-readable error code"
    )
    message: str = Field(
        ..., description="Human-readable error message"
    )
    field: Optional[str] = Field(
        None,
        description="Name of the field that caused the error",
    )
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


class ErrorResponse(BaseModel):
    """Standard error response model.

    This is the main error response model that will be returned
    by the API when an error occurs.

    Attributes:
        status: HTTP status code
        message: Main error message
        errors: List of detailed errors
        request_id: Unique identifier for the request (optional)
    """

    status: int = Field(..., description="HTTP status code")
    message: str = Field(
        ..., description="Main error message"
    )
    errors: List[ErrorDetail] = Field(
        default_factory=list,
        description="List of detailed errors",
    )
    request_id: Optional[str] = Field(
        None,
        description="Unique identifier for the request",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "status": 400,
                "message": "Validation error",
                "errors": [
                    {
                        "code": "invalid_color",
                        "message": "Invalid color format",
                        "field": "color",
                        "details": {"value": "#invalid"},
                    }
                ],
                "request_id": "req-123-456",
            }
        }
