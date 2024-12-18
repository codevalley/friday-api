import re
from typing import Dict, Any
from fastapi import HTTPException
from jsonschema import (
    validate as validate_json_schema,
    ValidationError,
)


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
