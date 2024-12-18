"""Error handlers for the application.

This module contains the error handlers that convert exceptions
into standardized API responses. It also includes utilities for
logging errors and generating error responses.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import (
    ValidationError as PydanticValidationError,
)

from .exceptions import (
    AppException,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
)
from .responses import ErrorResponse, ErrorDetail

# Set up logger
logger = logging.getLogger(__name__)


def get_error_code(
    exception: Exception,
    default_code: str = "internal_error",
) -> str:
    """Get a machine-readable error code from an exception.

    Args:
        exception: The exception to get the code from
        default_code: Default code if none can be determined

    Returns:
        A machine-readable error code
    """
    if isinstance(exception, ValidationError):
        return "validation_error"
    if isinstance(exception, NotFoundError):
        return "not_found"
    if isinstance(exception, AuthenticationError):
        return "authentication_error"
    if isinstance(exception, AuthorizationError):
        return "authorization_error"
    if isinstance(exception, ConflictError):
        return "conflict_error"
    if isinstance(exception, PydanticValidationError):
        return "validation_error"
    return default_code


def create_error_response(
    status_code: int,
    message: str,
    errors: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> ErrorResponse:
    """Create a standardized error response.

    Args:
        status_code: HTTP status code
        message: Main error message
        errors: Additional error details
        request_id: Unique request identifier

    Returns:
        Standardized error response
    """
    error_details = []
    if errors:
        for field, details in errors.items():
            if isinstance(details, dict):
                error_details.append(
                    ErrorDetail(
                        code=get_error_code(
                            details.get(
                                "exception", Exception()
                            )
                        ),
                        message=str(
                            details.get("message", "")
                        ),
                        field=field,
                        details=details.get("details"),
                    )
                )
            else:
                # Handle non-dictionary details
                error_details.append(
                    ErrorDetail(
                        code="error",
                        message=str(details),
                        field=field,
                    )
                )

    return ErrorResponse(
        status=status_code,
        message=message,
        errors=error_details,
        request_id=request_id,
    )


async def app_exception_handler(
    request: Request, exc: AppException
) -> JSONResponse:
    """Handle all application-specific exceptions.

    Args:
        request: FastAPI request object
        exc: Application exception

    Returns:
        JSON response with error details
    """
    request_id = str(uuid.uuid4())
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            message=exc.message,
            errors=exc.details,
            request_id=request_id,
        ).model_dump(),
    )


async def validation_exception_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Args:
        request: FastAPI request object
        exc: Pydantic validation error

    Returns:
        JSON response with validation error details
    """
    request_id = str(uuid.uuid4())
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors[field] = {
            "message": error["msg"],
            "details": {"type": error["type"]},
            "exception": ValidationError,
        }

    logger.warning(
        "Validation error",
        extra={
            "request_id": request_id,
            "errors": errors,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Validation error",
            errors=errors,
            request_id=request_id,
        ).model_dump(),
    )


async def internal_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions.

    Args:
        request: FastAPI request object
        exc: Unexpected exception

    Returns:
        JSON response with error details
    """
    request_id = str(uuid.uuid4())
    logger.exception(
        "Unexpected error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error",
            request_id=request_id,
        ).model_dump(),
    )
