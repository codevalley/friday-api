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

from orm.BaseModel import EntityMeta

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
        ValueError: If parameters are invalid
    """
    if page < 1:
        raise ValueError("Page number must be positive")
    if size < 1 or size > 100:
        raise ValueError(
            "Page size must be between 1 and 100"
        )


def validate_color(color: str) -> None:
    """Validate color format.

    Args:
        color: Color string to validate

    Raises:
        ValueError: If color format is invalid
    """
    if not color:
        raise ValueError("color must be a valid hex code")

    if not re.match(r"^#[0-9A-Fa-f]{6}$", color):
        raise ValueError("color must be a valid hex code")


def validate_activity_schema(schema: Dict) -> None:
    """Validate basic activity schema structure.
    This validates only the minimal requirements for a JSON Schema.
    More complex validation should be done in the domain layer.

    Args:
        schema: Schema dictionary to validate

    Raises:
        ValueError: If schema is invalid
    """
    if not isinstance(schema, dict):
        raise ValueError(
            "Activity schema must be a dictionary"
        )

    if "type" not in schema:
        raise ValueError(
            "Activity schema must contain 'type' field"
        )

    if schema["type"] != "object":
        raise ValueError(
            "Activity schema type must be 'object'"
        )

    # A schema with just {"type": "object"} is valid and matches any object
    # If there are additional fields, validate them
    if len(schema) > 1:
        has_properties = "properties" in schema
        has_pattern_props = "patternProperties" in schema

        # Check for any schema constraints
        constraint_fields = [
            "required",
            "additionalProperties",
            "minProperties",
            "maxProperties",
        ]
        has_constraints = any(
            field in schema for field in constraint_fields
        )

        # If schema has constraints or additional fields beyond type,
        # it must have properties or patternProperties
        if has_constraints and not (
            has_properties or has_pattern_props
        ):
            raise ValueError(
                "Activity schema with constraints must contain "
                "either 'properties' or 'patternProperties'"
            )


def validate_moment_data(
    data: Dict[str, Any], schema: Dict[str, Any]
) -> None:
    """Validate moment data against schema.

    Args:
        data: Data to validate
        schema: Schema to validate against

    Raises:
        ValueError: If data is invalid
    """
    if not isinstance(data, dict):
        raise ValueError("Invalid moment data")

    if not isinstance(schema, dict):
        raise ValueError("Invalid moment data")

    if "type" not in schema:
        raise ValueError("Invalid moment data")

    # Basic type validation
    if schema["type"] != "object":
        raise ValueError("Invalid moment data")

    # If schema has properties, validate them
    if "properties" in schema:
        # Validate required properties
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                raise ValueError("Invalid moment data")

        # Validate property types
        for field, value in data.items():
            if field not in schema["properties"]:
                raise ValueError("Invalid moment data")

            field_schema = schema["properties"][field]
            field_type = field_schema["type"]

            if field_type == "string":
                if not isinstance(value, str):
                    raise ValueError("Invalid moment data")
            elif field_type == "number":
                if not isinstance(value, (int, float)):
                    raise ValueError("Invalid moment data")
            elif field_type == "integer":
                if not isinstance(value, int):
                    raise ValueError("Invalid moment data")
            elif field_type == "boolean":
                if not isinstance(value, bool):
                    raise ValueError("Invalid moment data")
            elif field_type == "array":
                if not isinstance(value, list):
                    raise ValueError("Invalid moment data")
            elif field_type == "object":
                if not isinstance(value, dict):
                    raise ValueError("Invalid moment data")

    # If schema has patternProperties, validate them
    if "patternProperties" in schema:
        for field, value in data.items():
            for pattern, field_schema in schema[
                "patternProperties"
            ].items():
                if re.match(pattern, field):
                    field_type = field_schema["type"]
                    if (
                        field_type == "string"
                        and not isinstance(value, str)
                    ):
                        raise ValueError(
                            "Invalid moment data"
                        )
                    elif field_type == "number" and not (
                        isinstance(value, (int, float))
                    ):
                        raise ValueError(
                            "Invalid moment data"
                        )
                    elif (
                        field_type == "integer"
                        and not isinstance(value, int)
                    ):
                        raise ValueError(
                            "Invalid moment data"
                        )
                    elif (
                        field_type == "boolean"
                        and not isinstance(value, bool)
                    ):
                        raise ValueError(
                            "Invalid moment data"
                        )
                    elif (
                        field_type == "array"
                        and not isinstance(value, list)
                    ):
                        raise ValueError(
                            "Invalid moment data"
                        )
                    elif (
                        field_type == "object"
                        and not isinstance(value, dict)
                    ):
                        raise ValueError(
                            "Invalid moment data"
                        )


def validate_username(username: str) -> None:
    """Validate username format.

    Args:
        username: Username to validate

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
            detail="Username must be between 3 and 50 characters long",
        )

    if not username[0].isalpha():
        raise HTTPException(
            status_code=400,
            detail="Username must start with a letter",
        )

    if not all(c.isalnum() or c in "_-" for c in username):
        raise HTTPException(
            status_code=400,
            detail=(
                "Username must start with a letter and contain only letters,"
                " numbers, underscores, and hyphens"
            ),
        )

    if "__" in username or "--" in username:
        raise HTTPException(
            status_code=400,
            detail="Username cannot contain consecutive special characters",
        )

    if any(str(i) in username for i in range(1000, 10000)):
        raise HTTPException(
            status_code=400,
            detail="Username cannot contain more than 3 consecutive numbers",
        )

    if username.lower() in ["admin", "root", "system"]:
        raise HTTPException(
            status_code=400,
            detail="This username is reserved",
        )
