"""Test domain validation utilities."""

import pytest
from domain.validation import validate_activity_schema
from domain.exceptions import ActivityValidationError


def test_validate_activity_schema_valid():
    """Test validation of valid activity schema."""
    valid_schema = {
        "type": "object",
        "properties": {"notes": {"type": "string"}},
        "required": ["notes"],
    }

    # Should not raise any exception
    validate_activity_schema(valid_schema)


def test_validate_activity_schema_not_dict():
    """Test validation fails when schema is not a dictionary."""
    with pytest.raises(ActivityValidationError) as exc:
        validate_activity_schema(
            []
        )  # Passing a list instead of dict

    assert "must be a dictionary" in str(exc.value)


def test_validate_activity_schema_missing_type():
    """Test validation fails when type field is missing."""
    invalid_schema = {"properties": {}}

    with pytest.raises(ActivityValidationError) as exc:
        validate_activity_schema(invalid_schema)

    assert "type" in str(exc.value)


def test_validate_activity_schema_invalid_type():
    """Test validation fails when type is not 'object'."""
    invalid_schema = {"type": "string"}

    with pytest.raises(ActivityValidationError) as exc:
        validate_activity_schema(invalid_schema)

    assert "type" in str(exc.value)


def test_validate_activity_schema_invalid_properties():
    """Test validation fails when properties is not a dictionary."""
    invalid_schema = {
        "type": "object",
        "properties": "invalid",
    }

    with pytest.raises(ActivityValidationError) as exc:
        validate_activity_schema(invalid_schema)

    assert "properties" in str(exc.value)


def test_validate_activity_schema_invalid_property_type():
    """Test validation fails when property schema is invalid."""
    invalid_schema = {
        "type": "object",
        "properties": {
            "field": "not_a_schema"  # Should be a dict
        },
    }

    with pytest.raises(ActivityValidationError) as exc:
        validate_activity_schema(invalid_schema)

    assert "field" in str(exc.value)


def test_validate_activity_schema_missing_property_type():
    """Test validation fails when property type is missing."""
    invalid_schema = {
        "type": "object",
        "properties": {"field": {}},  # Missing type
    }

    with pytest.raises(ActivityValidationError) as exc:
        validate_activity_schema(invalid_schema)

    assert "type" in str(exc.value)


def test_validate_activity_schema_with_ref():
    """Test validation passes when using $ref instead of type."""
    valid_schema = {
        "type": "object",
        "properties": {
            "field": {"$ref": "#/definitions/something"}
        },
    }

    # Should not raise any exception
    validate_activity_schema(valid_schema)


def test_validate_activity_schema_invalid_pattern_properties():
    """Test validation fails when patternProperties is invalid."""
    invalid_schema = {
        "type": "object",
        "patternProperties": "invalid"
    }
    
    with pytest.raises(ActivityValidationError) as exc:
        validate_activity_schema(invalid_schema)
    
    # The actual error message from ActivityValidationError
    assert "Pattern properties must be a dictionary" in str(exc.value)


def test_validate_activity_schema_constraints_without_properties():
    """Test validation fails with constraints but no properties."""
    invalid_schema = {
        "type": "object",
        "required": ["field"],
        "additionalProperties": False,
    }

    with pytest.raises(ActivityValidationError) as exc:
        validate_activity_schema(invalid_schema)

    assert "constraints" in str(exc.value)
