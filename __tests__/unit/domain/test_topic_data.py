"""Test suite for TopicData domain model.

This test suite verifies the functionality of the TopicData domain model,
including validation, conversion, and error handling. It ensures that the
model maintains data integrity and follows business rules.
"""

import pytest
from typing import Dict, Any

from domain.topic import TopicData
from domain.exceptions import (
    TopicValidationError,
    TopicNameError,
    TopicIconError,
)


@pytest.fixture
def valid_topic_dict() -> Dict[str, Any]:
    """Create a valid topic dictionary for testing.

    This fixture provides a baseline valid topic data dictionary
    that can be modified for specific test cases.
    """
    return {
        "name": "Work",
        "icon": "💼",
        "user_id": "test-user",
    }


@pytest.fixture
def valid_topic_data(valid_topic_dict) -> TopicData:
    """Create a valid TopicData instance for testing.

    This fixture provides a baseline valid TopicData instance
    that can be used directly in tests.
    """
    return TopicData(**valid_topic_dict)


class TestTopicDataValidation:
    """Test validation methods of TopicData."""

    def test_valid_topic_data(self, valid_topic_data):
        """Test that valid topic data passes validation."""
        # Should not raise any exceptions
        valid_topic_data.validate()

    def test_invalid_name_type(self, valid_topic_dict):
        """Test validation with invalid name type."""
        valid_topic_dict["name"] = 123
        with pytest.raises(TopicNameError) as exc:
            TopicData(**valid_topic_dict)
        assert str(exc.value) == "name must be a string"

    def test_empty_name(self, valid_topic_dict):
        """Test validation with empty name."""
        valid_topic_dict["name"] = ""
        with pytest.raises(TopicNameError) as exc:
            TopicData(**valid_topic_dict)
        assert str(exc.value) == "name cannot be empty"

    def test_name_too_long(self, valid_topic_dict):
        """Test validation with name exceeding max length."""
        valid_topic_dict["name"] = "a" * 256
        with pytest.raises(TopicNameError) as exc:
            TopicData(**valid_topic_dict)
        assert (
            str(exc.value)
            == "name cannot exceed 255 characters"
        )

    def test_invalid_icon_type(self, valid_topic_dict):
        """Test validation with invalid icon type."""
        valid_topic_dict["icon"] = 123
        with pytest.raises(TopicIconError) as exc:
            TopicData(**valid_topic_dict)
        assert str(exc.value) == "icon must be a string"

    def test_empty_icon(self, valid_topic_dict):
        """Test validation with empty icon."""
        valid_topic_dict["icon"] = ""
        with pytest.raises(TopicIconError) as exc:
            TopicData(**valid_topic_dict)
        assert str(exc.value) == "icon cannot be empty"

    def test_icon_too_long(self, valid_topic_dict):
        """Test validation with icon exceeding max length."""
        valid_topic_dict["icon"] = "a" * 256
        with pytest.raises(TopicIconError) as exc:
            TopicData(**valid_topic_dict)
        assert (
            str(exc.value)
            == "icon cannot exceed 255 characters"
        )

    def test_invalid_user_id(self, valid_topic_dict):
        """Test validation with invalid user_id."""
        valid_topic_dict["user_id"] = ""
        with pytest.raises(TopicValidationError) as exc:
            TopicData(**valid_topic_dict)
        assert (
            str(exc.value)
            == "user_id must be a non-empty string"
        )


class TestTopicDataConversion:
    """Test conversion methods of TopicData."""

    def test_to_dict(self, valid_topic_data):
        """Test conversion to dictionary."""
        result = valid_topic_data.to_dict()
        assert result["name"] == valid_topic_data.name
        assert result["icon"] == valid_topic_data.icon
        assert result["user_id"] == valid_topic_data.user_id
        assert "created_at" in result
        assert "updated_at" in result

    def test_from_dict(self, valid_topic_dict):
        """Test creation from dictionary."""
        topic = TopicData.from_dict(valid_topic_dict)
        assert topic.name == valid_topic_dict["name"]
        assert topic.icon == valid_topic_dict["icon"]
        assert topic.user_id == valid_topic_dict["user_id"]
        assert topic.created_at is not None
        assert topic.updated_at is not None


class TestTopicDataErrorHandling:
    """Test error handling of TopicData."""

    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        with pytest.raises(TypeError):
            TopicData()  # type: ignore

    def test_type_mismatches(self, valid_topic_dict):
        """Test handling of type mismatches."""
        valid_topic_dict["name"] = 123
        with pytest.raises(TopicNameError) as exc:
            TopicData(**valid_topic_dict)
        assert str(exc.value) == "name must be a string"
