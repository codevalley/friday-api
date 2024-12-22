"""Unit tests for ActivityData domain model."""

import pytest
from domain.activity import ActivityData
from domain.exceptions import ActivityValidationError


@pytest.fixture
def valid_activity_data():
    """Return valid activity data for testing."""
    return {
        "name": "Test Activity",
        "description": "A test activity",
        "activity_schema": {
            "type": "object",
            "properties": {
                "test_field": {"type": "string"}
            },
        },
        "icon": "📝",
        "color": "#FF0000",
        "user_id": "test_user",
    }


class TestActivityDataValidation:
    """Test cases for ActivityData validation."""

    def test_valid_activity_data(self, valid_activity_data):
        """Test creating ActivityData with valid data."""
        activity = ActivityData(**valid_activity_data)
        assert activity.name == valid_activity_data["name"]
        assert (
            activity.color == valid_activity_data["color"]
        )
        assert (
            str(activity.color_value)
            == valid_activity_data["color"]
        )

    def test_color_format_validation(self):
        """Test color format validation."""
        data = {
            "name": "Test",
            "description": "Test",
            "activity_schema": {"type": "object"},
            "icon": "📝",
            "user_id": "test_user",
        }

        # Test valid colors
        valid_colors = ["#FF0000", "#00ff00", "#0000FF"]
        for color in valid_colors:
            activity = ActivityData(**data, color=color)
            assert activity.color == color
            assert str(activity.color_value) == color

        # Test invalid colors
        invalid_colors = ["#12", "invalid", "#GGGGGG", ""]
        for color in invalid_colors:
            with pytest.raises(
                ActivityValidationError
            ) as exc:
                ActivityData(**data, color=color)
            assert "Invalid color format" in str(exc.value)
