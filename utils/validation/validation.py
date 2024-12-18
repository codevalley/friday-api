"""Validation utilities for common operations across the application.

This module provides a set of validation functions that can be used
to validate various types of data and ensure consistency across
the application. Each function raises appropriate HTTP exceptions
when validation fails.
"""

import re
import logging
from typing import Dict, Any, TypeVar, Type
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from jsonschema import (
    validate as validate_json_schema,
    ValidationError,
)

from orm.BaseModel import EntityMeta

# Set up module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

M = TypeVar("M", bound=EntityMeta)


def validate_existence(
    db: Session,
    model: Type[M],
    id: any,
    error_message: str = "Resource not found",
) -> M:
    """Validate that a resource exists in the database

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
    """
    Validate pagination parameters.
    Raises HTTPException if validation fails.
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


def validate_color(color: str) -> None:
    """
    Validate hex color format.
    Raises HTTPException if validation fails.
    """
    if not re.match(r"^#[0-9A-Fa-f]{6}$", color):
        raise HTTPException(
            status_code=400,
            detail="Color must be a valid hex code",
        )


def validate_activity_schema(
    schema: Dict[str, Any]
) -> None:
    """
    Validate activity schema structure.
    Raises HTTPException if validation fails.
    """
    try:
        # Meta-schema for validating activity schemas
        meta_schema = {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "properties": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"}
                        },
                        "required": ["type"],
                    },
                },
                "required": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["type", "properties"],
        }

        validate_json_schema(
            instance=schema, schema=meta_schema
        )
    except ValidationError as e:
        print(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid activity schema format",
        )


def validate_moment_data(
    data: Dict[str, Any], schema: Dict[str, Any]
) -> None:
    """
    Validate moment data against its activity schema.
    Raises HTTPException if validation fails.
    """
    try:
        validate_json_schema(instance=data, schema=schema)
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid moment data: {str(e)}",
        )


def validate_username(username: str) -> None:
    """
    Validate username format.
    Raises HTTPException if validation fails.
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
