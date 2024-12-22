"""Infrastructure validation utilities.

This module contains validation functions that are specific to the
infrastructure/application layer, such as pagination parameters,
request data validation, etc.

Domain-specific validation should be in the domain layer.
"""

from typing import Dict, Any
from fastapi import HTTPException, status
from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError


def validate_pagination(page: int, size: int) -> None:
    """Validate pagination parameters.

    Args:
        page: Page number (1-based)
        size: Number of items per page

    Raises:
        HTTPException: If validation fails
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be positive",
        )

    if size < 1 or size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100",
        )


def validate_moment_data(
    data: Dict[str, Any], schema: Dict[str, Any]
) -> None:
    """Validate moment data against a JSON schema.

    Args:
        data: Data to validate
        schema: JSON Schema to validate against

    Raises:
        HTTPException: If validation fails
    """
    try:
        jsonschema_validate(instance=data, schema=schema)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid moment data: {str(e)}",
        )
