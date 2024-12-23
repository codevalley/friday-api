"""Test domain exception handlers."""

from fastapi import HTTPException, status
from domain.exceptions import (
    DomainException,
    ValidationException,
)
from utils.errors.domain_exceptions import (
    handle_domain_exception,
)


def test_handle_validation_exception():
    """Test handling validation exception."""
    exc = ValidationException(
        message="Invalid data", code="VALIDATION_ERROR"
    )
    http_exc = handle_domain_exception(exc)

    assert isinstance(http_exc, HTTPException)
    assert (
        http_exc.status_code == status.HTTP_400_BAD_REQUEST
    )
    assert http_exc.detail == "Invalid data"


def test_handle_generic_domain_exception():
    """Test handling generic domain exception."""
    exc = DomainException(
        message="Some error", code="GENERAL_ERROR"
    )
    http_exc = handle_domain_exception(exc)

    assert isinstance(http_exc, HTTPException)
    assert (
        http_exc.status_code
        == status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    assert http_exc.detail == "An unexpected error occurred"
