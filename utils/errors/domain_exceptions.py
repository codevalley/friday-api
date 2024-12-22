"""Error handlers for mapping domain exceptions to HTTP exceptions."""

from fastapi import HTTPException, status
from domain.exceptions import (
    DomainException,
    ValidationException,
)


def handle_domain_exception(
    exc: DomainException,
) -> HTTPException:
    """Map domain exceptions to HTTP exceptions.

    Args:
        exc: Domain exception to map

    Returns:
        HTTPException with appropriate status code and detail
    """
    if isinstance(exc, ValidationException):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )

    # Default to internal server error
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred",
    )
