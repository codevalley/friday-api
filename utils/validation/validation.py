"""Validation utilities for common operations across the application.

This module provides a set of validation functions that can be used
to validate various types of data and ensure consistency across
the application. Each function raises appropriate exceptions
when validation fails.
"""

import re
import logging
from typing import Dict, Any, TypeVar, Type
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from jsonschema import (
    validate as validate_json_schema,
    ValidationError as JsonSchemaValidationError,
)

from orm.BaseModel import EntityMeta
from utils.errors.exceptions import ValidationError

# Set up module logger
logger = logging.getLogger(__name__)

M = TypeVar("M", bound=EntityMeta)


def validate_existence(
    db: Session,
    model: Type[M],
    id: any,
    error_message: str = "Resource not found",
) -> M:
    """Validate that a resource exists in the database.

    Args:
        db: SQLAlchemy database session
        model: Model class to query
        id: Resource ID
        error_message: Custom error message if not found

    Returns:
        Instance if found

    Raises:
        HTTPException: If resource not found
    """
    instance = (
        db.query(model).filter(model.id == id).first()
    )
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_message,
        )
    return instance


def validate_pagination(page: int, size: int) -> None:
    """Validate pagination parameters.

    Args:
        page (int): Page number (1-based)
        size (int): Number of items per page

    Raises:
        HTTPException: If validation fails
    """
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page number must be positive",
        )
    if size < 1 or size > 100:
        raise HTTPException(
            status_code=400,
            detail="Page size must be between 1 and 100",
        )


def validate_color(color: str) -> bool:
    """
    Validate if the color is in correct #RRGGBB hex format

    Args:
        color (str): Color string to validate

    Returns:
        bool: True if valid, raises ValidationError if invalid

    Raises:
        ValidationError: If color format is invalid
    """
    if not re.match(r"^#[0-9A-Fa-f]{6}$", color):
        raise ValidationError(
            f"Invalid color format: {color}. Must be in #RRGGBB format"
        )
    return True


def validate_activity_schema(
    schema: Dict[str, Any]
) -> None:
    """Validate an activity schema structure.

    Args:
        schema (Dict[str, Any]): Schema dictionary to validate

    Raises:
        ValidationError: If schema format is invalid
    """
    if not isinstance(schema, dict):
        logger.error("Schema must be a dictionary")
        raise ValidationError("Schema must be a dictionary")

    required_fields = ["type", "properties"]
    if not all(
        field in schema for field in required_fields
    ):
        logger.error(f"Invalid schema format: {schema}")
        raise ValidationError(
            "Activity schema must contain 'type' and 'properties' fields"
        )


def validate_moment_data(
    data: Dict[str, Any], schema: Dict[str, Any]
) -> None:
    """Validate moment data against its activity schema.

    Args:
        data (Dict[str, Any]): Moment data to validate
        schema (Dict[str, Any]): Schema to validate against

    Raises:
        HTTPException: If validation fails
    """
    try:
        validate_json_schema(instance=data, schema=schema)
    except JsonSchemaValidationError as e:
        logger.error(
            f"Invalid moment data: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid moment data: {str(e)}",
        )


def validate_username(username: str) -> None:
    """
    Validate username format.

    Args:
        username (str): Username to validate

    Raises:
        HTTPException: If validation fails
    """
    if (
        not username
        or len(username) < 3
        or len(username) > 50
    ):
        raise HTTPException(
            status_code=400,
            detail="Username must be between 3 and 50 characters",
        )
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        raise HTTPException(
            status_code=400,
            detail=(
                "Username can only contain letters,"
                " numbers, underscores, and hyphens"
            ),
        )
