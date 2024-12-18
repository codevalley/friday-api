"""Custom exceptions for the application.

This module defines all custom exceptions used throughout the application.
Each exception maps to a specific error scenario and includes appropriate
HTTP status codes and error messages.
"""

from typing import Optional, Any, Dict
from fastapi import status


class AppException(Exception):
    """Base exception for all application errors.

    All custom exceptions should inherit from this class to ensure
    consistent error handling and logging.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code for the error
        details: Additional error details (optional)
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppException):
    """Raised when data validation fails.

    This exception should be used for all validation errors,
    whether they're schema validation, business rule validation,
    or input validation.

    Example:
        raise ValidationError(
            "Invalid color format", details={"color": "#invalid"}
        )
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class NotFoundError(AppException):
    """Raised when a requested resource is not found.

    This exception should be used when a database query returns no results
    or when a resource doesn't exist.

    Example:
        raise NotFoundError("Activity not found", details={"id": activity_id})
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class AuthenticationError(AppException):
    """Raised when authentication fails.

    This exception should be used for all authentication-related errors,
    such as invalid credentials or expired tokens.

    Example:
        raise AuthenticationError("Invalid API key")
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class AuthorizationError(AppException):
    """Raised when a user lacks permission for an operation.

    This exception should be used when a user is authenticated
    but doesn't have the required permissions.

    Example:
        raise AuthorizationError("Not authorized to update this activity")
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ConflictError(AppException):
    """Raised when there's a conflict with existing data.

    This exception should be used for uniqueness violations,
    version conflicts, or other data consistency issues.

    Example:
        raise ConflictError("Username already exists")
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )
