"""Test validation utilities."""

import pytest
from fastapi import HTTPException
from utils.validation.validation import (
    validate_color,
    validate_username,
)


def test_validate_color_valid():
    """Test validation of valid color."""
    valid_colors = ["#123456", "#ABCDEF", "#abcdef"]
    for color in valid_colors:
        validate_color(color)  # Should not raise


def test_validate_color_invalid():
    """Test validation of invalid colors."""
    invalid_colors = [
        "",  # Empty
        "123456",  # Missing #
        "#12345",  # Too short
        "#1234567",  # Too long
        "#GHIJKL",  # Invalid chars
        "#12345G",  # Invalid char
    ]

    for color in invalid_colors:
        with pytest.raises(ValueError):
            validate_color(color)


def test_validate_username_valid():
    """Test validation of valid usernames."""
    valid_usernames = [
        "john",
        "john_doe",
        "john-doe",
        "john123",
        "j_123",
    ]

    for username in valid_usernames:
        validate_username(username)  # Should not raise


def test_validate_username_invalid():
    """Test validation of invalid usernames."""
    invalid_cases = [
        ("", "between 3 and 50"),  # Empty
        ("ab", "between 3 and 50"),  # Too short
        ("a" * 51, "between 3 and 50"),  # Too long
        (
            "123john",
            "start with a letter",
        ),  # Starts with number
        ("john@doe", "only letters"),  # Invalid char
        (
            "john__doe",
            "consecutive",
        ),  # Consecutive special chars
        (
            "john--doe",
            "consecutive",
        ),  # Consecutive special chars
        (
            "john1234doe",
            "consecutive numbers",
        ),  # Too many numbers
        ("admin", "reserved"),  # Reserved username
        ("root", "reserved"),  # Reserved username
        ("system", "reserved"),  # Reserved username
    ]

    for username, expected_error in invalid_cases:
        with pytest.raises(HTTPException) as exc:
            validate_username(username)
        assert expected_error in str(exc.value.detail)
