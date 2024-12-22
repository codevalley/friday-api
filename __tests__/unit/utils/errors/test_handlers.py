"""Tests for error handlers."""

import pytest
from fastapi import Request, status
from pydantic import BaseModel, Field

from pydantic import (
    ValidationError as PydanticValidationError,
)

from utils.errors.exceptions import (
    ValidationError,
    NotFoundError,
    AppException,
)
from utils.errors.handlers import (
    get_error_code,
    create_error_response,
    app_exception_handler,
    validation_exception_handler,
    internal_exception_handler,
)


class TestModel(BaseModel):
    """Test model for validation errors."""

    name: str = Field(..., min_length=3)
    age: int = Field(..., gt=0)


@pytest.fixture
def mock_request():
    """Create a mock request object."""
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
            "query_string": b"",
            "client": ("127.0.0.1", 8000),
            "server": ("127.0.0.1", 8000),
        }
    )


def test_get_error_code():
    """Test error code generation for different exceptions."""
    assert (
        get_error_code(ValidationError("test"))
        == "validation_error"
    )
    assert (
        get_error_code(NotFoundError("test")) == "not_found"
    )
    assert get_error_code(Exception()) == "internal_error"
    assert (
        get_error_code(Exception(), "custom_error")
        == "custom_error"
    )


def test_create_error_response():
    """Test error response creation."""
    response = create_error_response(
        status_code=400,
        message="Test error",
        errors={
            "field": {
                "message": "Invalid value",
                "details": {"value": "test"},
                "exception": ValidationError("test"),
            }
        },
        request_id="test-123",
    )

    assert response.status == 400
    assert response.message == "Test error"
    assert response.request_id == "test-123"
    assert len(response.errors) == 1
    assert response.errors[0].field == "field"
    assert response.errors[0].code == "validation_error"


@pytest.mark.asyncio
async def test_app_exception_handler(mock_request):
    """Test handling of AppException."""
    exc = AppException(
        "Test error",
        status_code=status.HTTP_400_BAD_REQUEST,
        details={"test": "value"},
    )
    response = await app_exception_handler(
        mock_request, exc
    )

    assert response.status_code == 400
    content = response.body.decode()
    assert "Test error" in content
    assert "test" in content
    assert "value" in content


@pytest.mark.asyncio
async def test_validation_exception_handler(mock_request):
    """Test handling of Pydantic validation errors."""
    try:
        TestModel(name="a", age=0)
        pytest.fail("Should raise ValidationError")
    except PydanticValidationError as exc:
        response = await validation_exception_handler(
            mock_request, exc
        )

        assert response.status_code == 422
        content = response.body.decode()
        assert "Validation error" in content
        assert "age" in content
        assert "name" in content


@pytest.mark.asyncio
async def test_internal_exception_handler(mock_request):
    """Test handling of unexpected exceptions."""
    exc = Exception("Unexpected error")
    response = await internal_exception_handler(
        mock_request, exc
    )

    assert response.status_code == 500
    content = response.body.decode()
    assert "Internal server error" in content
