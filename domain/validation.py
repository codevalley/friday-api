"""Domain-specific validation utilities."""

from typing import Dict, Any

from .exceptions import ActivityValidationError


def validate_activity_schema(
    schema: Dict[str, Any]
) -> None:
    """Validate activity schema structure.

    Args:
        schema: Schema to validate

    Raises:
        ActivityValidationError: If schema is invalid
    """
    if not isinstance(schema, dict):
        raise ActivityValidationError.invalid_field_value(
            "activity_schema",
            "Activity schema must be a dictionary",
        )

    if "type" not in schema:
        raise ActivityValidationError.missing_type_field()

    if schema["type"] != "object":
        raise ActivityValidationError.invalid_schema_type()

    # Additional domain-specific validation
    if "properties" in schema:
        if not isinstance(schema["properties"], dict):
            raise ActivityValidationError.invalid_field_value(
                "properties",
                "Schema properties must be a dictionary",
            )

        # Validate property types
        for prop_name, prop_schema in schema[
            "properties"
        ].items():
            if not isinstance(prop_schema, dict):
                raise ActivityValidationError.invalid_field_value(
                    prop_name,
                    f"Property {prop_name} schema must be a dictionary",
                )
            # Skip type check if it's a reference
            if (
                "$ref" not in prop_schema
                and "type" not in prop_schema
            ):
                raise ActivityValidationError.invalid_field_value(
                    prop_name,
                    f"Property {prop_name} must specify a type",
                )

    if "patternProperties" in schema:
        if not isinstance(
            schema["patternProperties"], dict
        ):
            raise ActivityValidationError.invalid_field_value(
                "patternProperties",
                "Pattern properties must be a dictionary",
            )

        # Validate pattern property types
        for pattern, prop_schema in schema[
            "patternProperties"
        ].items():
            if not isinstance(prop_schema, dict):
                raise ActivityValidationError.invalid_field_value(
                    pattern,
                    f"Pattern {pattern} schema must be a dictionary",
                )
            if (
                "$ref" not in prop_schema
                and "type" not in prop_schema
            ):
                raise ActivityValidationError.invalid_field_value(
                    pattern,
                    f"Pattern {pattern} must specify a type",
                )

    # Check for schema constraints
    constraint_fields = [
        "required",
        "additionalProperties",
        "minProperties",
        "maxProperties",
    ]
    has_constraints = any(
        field in schema for field in constraint_fields
    )
    has_properties = "properties" in schema
    has_pattern_props = "patternProperties" in schema

    if has_constraints and not (
        has_properties or has_pattern_props
    ):
        raise ActivityValidationError.invalid_schema_constraints()
