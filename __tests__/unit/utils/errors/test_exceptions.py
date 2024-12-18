"""Tests for custom exceptions."""

from fastapi import status

from utils.errors.exceptions import (
    AppException,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
)


def test_app_exception_basic():
    """Test basic AppException creation."""
    exc = AppException("Test error")
    assert exc.message == "Test error"
    assert (
        exc.status_code
        == status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    assert exc.details == {}


def test_app_exception_with_details():
    """Test AppException with custom details."""
    details = {"field": "test", "value": 123}
    exc = AppException(
        "Test error",
        status_code=status.HTTP_400_BAD_REQUEST,
        details=details,
    )
    assert exc.message == "Test error"
    assert exc.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.details == details


def test_validation_error():
    """Test ValidationError creation and properties."""
    details = {"field": "color", "value": "#invalid"}
    exc = ValidationError("Invalid format", details=details)
    assert exc.message == "Invalid format"
    assert exc.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.details == details


def test_not_found_error():
    """Test NotFoundError creation and properties."""
    details = {"id": 123}
    exc = NotFoundError(
        "Resource not found", details=details
    )
    assert exc.message == "Resource not found"
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.details == details


def test_authentication_error():
    """Test AuthenticationError creation and properties."""
    exc = AuthenticationError("Invalid credentials")
    assert exc.message == "Invalid credentials"
    assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.details == {}


def test_authorization_error():
    """Test AuthorizationError creation and properties."""
    details = {"required_role": "admin"}
    exc = AuthorizationError(
        "Insufficient permissions", details=details
    )
    assert exc.message == "Insufficient permissions"
    assert exc.status_code == status.HTTP_403_FORBIDDEN
    assert exc.details == details


def test_conflict_error():
    """Test ConflictError creation and properties."""
    details = {"field": "username", "value": "existing"}
    exc = ConflictError(
        "Resource already exists", details=details
    )
    assert exc.message == "Resource already exists"
    assert exc.status_code == status.HTTP_409_CONFLICT
    assert exc.details == details


def test_exception_inheritance():
    """Test exception inheritance hierarchy."""
    exceptions = [
        ValidationError("test"),
        NotFoundError("test"),
        AuthenticationError("test"),
        AuthorizationError("test"),
        ConflictError("test"),
    ]
    for exc in exceptions:
        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)
