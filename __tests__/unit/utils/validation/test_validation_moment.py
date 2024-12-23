"""Test moment data validation utilities."""

import pytest
from utils.validation.validation import validate_moment_data


def test_validate_moment_data_valid():
    """Test validation of valid moment data."""
    valid_schema = {
        "type": "object",
        "properties": {"notes": {"type": "string"}},
    }
    valid_data = {"notes": "Test note"}

    # Should not raise
    validate_moment_data(valid_data, valid_schema)


def test_validate_moment_data_invalid_data():
    """Test validation with invalid data."""
    schema = {
        "type": "object",
        "properties": {"notes": {"type": "string"}},
    }
    invalid_data = ["not a dict"]

    with pytest.raises(ValueError):
        validate_moment_data(invalid_data, schema)


def test_validate_moment_data_invalid_schema():
    """Test validation with invalid schema."""
    data = {"notes": "Test"}
    invalid_schema = ["not a dict"]

    with pytest.raises(ValueError):
        validate_moment_data(data, invalid_schema)
