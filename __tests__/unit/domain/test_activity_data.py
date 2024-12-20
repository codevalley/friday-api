"""Test suite for ActivityData domain model."""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from domain.activity import ActivityData
from domain.moment import MomentData


@pytest.fixture
def valid_activity_dict() -> Dict[str, Any]:
    """Create a valid activity dictionary for testing."""
    return {
        "name": "Test Activity",
        "description": "Test Description",
        "activity_schema": {
            "type": "object",
            "properties": {
                "test_field": {"type": "string"}
            },
        },
        "icon": "test-icon",
        "color": "#000000",
        "user_id": "test-user",
    }


@pytest.fixture
def valid_activity_data(
    valid_activity_dict,
) -> ActivityData:
    """Create a valid ActivityData instance for testing."""
    return ActivityData(**valid_activity_dict)


@pytest.fixture
def valid_moment_data() -> MomentData:
    """Create a valid MomentData instance for testing."""
    return MomentData(
        activity_id=1,
        user_id="test-user",
        data={"test_field": "test_value"},
        timestamp=datetime.now(timezone.utc),
    )


class TestActivityDataValidation:
    """Test validation methods of ActivityData."""

    def test_valid_activity_data(self, valid_activity_data):
        """Test that valid activity data passes validation."""
        # Should not raise any exceptions
        valid_activity_data.validate()

    def test_invalid_name(self, valid_activity_dict):
        """Test validation with invalid name."""
        valid_activity_dict["name"] = ""
        with pytest.raises(ValueError) as exc:
            ActivityData(**valid_activity_dict)
        assert "name must be a non-empty string" in str(
            exc.value
        )

    def test_invalid_description(self, valid_activity_dict):
        """Test validation with invalid description."""
        valid_activity_dict["description"] = ""
        with pytest.raises(ValueError) as exc:
            ActivityData(**valid_activity_dict)
        assert (
            "description must be a non-empty string"
            in str(exc.value)
        )

    def test_invalid_schema(self, valid_activity_dict):
        """Test validation with invalid schema."""
        valid_activity_dict["activity_schema"] = (
            "not a dict"
        )
        with pytest.raises(ValueError) as exc:
            ActivityData(**valid_activity_dict)
        assert (
            "activity_schema must be a dictionary"
            in str(exc.value)
        )

    def test_invalid_icon(self, valid_activity_dict):
        """Test validation with invalid icon."""
        valid_activity_dict["icon"] = ""
        with pytest.raises(ValueError) as exc:
            ActivityData(**valid_activity_dict)
        assert "icon must be a non-empty string" in str(
            exc.value
        )

    def test_invalid_color(self, valid_activity_dict):
        """Test validation with invalid color."""
        valid_activity_dict["color"] = ""
        with pytest.raises(ValueError) as exc:
            ActivityData(**valid_activity_dict)
        assert "color must be a non-empty string" in str(
            exc.value
        )

    def test_complex_schema_validation(
        self, valid_activity_dict
    ):
        """Test validation with complex activity schema."""
        valid_activity_dict["activity_schema"] = {
            "type": "object",
            "properties": {
                "string_field": {"type": "string"},
                "number_field": {"type": "number"},
                "array_field": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "nested_object": {
                    "type": "object",
                    "properties": {
                        "inner_field": {"type": "boolean"}
                    },
                },
            },
            "required": ["string_field", "number_field"],
        }
        activity = ActivityData(**valid_activity_dict)
        assert activity.activity_schema["type"] == "object"
        assert (
            "string_field"
            in activity.activity_schema["properties"]
        )

    def test_color_format_validation(
        self, valid_activity_dict
    ):
        """Test validation of color hex format."""
        # Test valid hex colors
        valid_colors = ["#000000", "#FFFFFF", "#1a2b3c"]
        for color in valid_colors:
            valid_activity_dict["color"] = color
            activity = ActivityData(**valid_activity_dict)
            assert activity.color == color

        # Test invalid hex colors
        invalid_colors = [
            "#12",
            "#12345",
            "123456",
            "invalid",
        ]
        for color in invalid_colors:
            valid_activity_dict["color"] = color
            with pytest.raises(ValueError) as exc:
                ActivityData(**valid_activity_dict)
            assert "color must be a valid hex code" in str(
                exc.value
            )


class TestActivityDataConversion:
    """Test conversion methods of ActivityData."""

    def test_to_dict_without_moments(
        self, valid_activity_data
    ):
        """Test conversion to dictionary without moments."""
        result = valid_activity_data.to_dict()
        assert result["name"] == valid_activity_data.name
        assert (
            result["description"]
            == valid_activity_data.description
        )
        assert (
            result["activity_schema"]
            == valid_activity_data.activity_schema
        )
        assert result["icon"] == valid_activity_data.icon
        assert result["color"] == valid_activity_data.color
        assert (
            result["user_id"] == valid_activity_data.user_id
        )
        assert "moments" not in result

    def test_to_dict_with_moments(
        self,
        valid_activity_data,
        valid_moment_data,
    ):
        """Test conversion to dictionary with moments."""
        valid_activity_data.moments = [valid_moment_data]
        result = valid_activity_data.to_dict()
        assert len(result["moments"]) == 1
        assert (
            result["moments"][0]["activity_id"]
            == valid_moment_data.activity_id
        )

    def test_from_dict_minimal(self, valid_activity_dict):
        """Test creation from minimal dictionary."""
        activity = ActivityData.from_dict(
            valid_activity_dict
        )
        assert activity.name == valid_activity_dict["name"]
        assert (
            activity.description
            == valid_activity_dict["description"]
        )
        assert (
            activity.activity_schema
            == valid_activity_dict["activity_schema"]
        )

    def test_from_dict_with_moments(
        self, valid_activity_dict, valid_moment_data
    ):
        """Test creation from dictionary with moments."""
        valid_activity_dict["moments"] = [
            valid_moment_data.to_dict()
        ]
        activity = ActivityData.from_dict(
            valid_activity_dict
        )
        assert len(activity.moments) == 1  # type: ignore
        assert (
            activity.moments[0].activity_id  # type: ignore
            == valid_moment_data.activity_id
        )


class TestActivityDataTypeHints:
    """Test type hints of ActivityData."""

    def test_generic_type_parameter(self):
        """Test that the generic type parameter works."""
        activity: ActivityData = ActivityData.from_dict(
            {
                "name": "Test",
                "description": "Test",
                "activity_schema": {"type": "object"},
                "icon": "test",
                "color": "#000000",
                "user_id": "test",
            }
        )
        assert isinstance(activity, ActivityData)

    def test_optional_fields(self, valid_activity_dict):
        """Test that optional fields can be None."""
        activity = ActivityData(**valid_activity_dict)
        assert activity.id is None
        assert activity.moment_count == 0
        assert activity.moments is None
        assert activity.created_at is None
        assert activity.updated_at is None


class TestActivityDataErrorHandling:
    """Test error handling of ActivityData."""

    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        with pytest.raises(TypeError):
            ActivityData()  # type: ignore

    def test_type_mismatches(self, valid_activity_dict):
        """Test handling of type mismatches."""
        valid_activity_dict["moment_count"] = "not an int"
        with pytest.raises(ValueError):
            ActivityData(**valid_activity_dict)

    def test_invalid_moments_type(
        self, valid_activity_dict
    ):
        """Test handling of invalid moments type."""
        valid_activity_dict["moments"] = "not a list"
        with pytest.raises(ValueError):
            ActivityData(**valid_activity_dict)


class TestActivityDataRelationships:
    """Test relationship handling in ActivityData."""

    def test_empty_moments_list(self, valid_activity_dict):
        """Test activity with empty moments list."""
        valid_activity_dict["moments"] = []
        activity = ActivityData(**valid_activity_dict)
        assert activity.moments == []
        assert activity.moment_count == 0

    def test_invalid_moment_in_list(
        self, valid_activity_dict, valid_moment_data
    ):
        """Test activity with invalid moment in list."""
        valid_activity_dict["moments"] = [
            valid_moment_data,
            {"not": "a moment"},
        ]
        with pytest.raises(ValueError) as exc:
            ActivityData(**valid_activity_dict)
        assert "invalid moment data in list" in str(
            exc.value
        )

    def test_moment_count_mismatch(
        self, valid_activity_dict, valid_moment_data
    ):
        """Test moment count validation."""
        valid_activity_dict["moments"] = [valid_moment_data]
        valid_activity_dict["moment_count"] = 2
        with pytest.raises(ValueError) as exc:
            ActivityData(**valid_activity_dict)
        assert "moment count mismatch" in str(exc.value)


class TestActivityDataSchemaValidation:
    """Test schema validation in ActivityData."""

    def test_schema_with_references(
        self, valid_activity_dict
    ):
        """Test schema with JSON Schema references."""
        valid_activity_dict["activity_schema"] = {
            "type": "object",
            "definitions": {
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                    },
                }
            },
            "properties": {
                "home": {"$ref": "#/definitions/address"},
                "work": {"$ref": "#/definitions/address"},
            },
        }
        activity = ActivityData(**valid_activity_dict)
        assert "definitions" in activity.activity_schema
        assert (
            "$ref"
            in activity.activity_schema["properties"][
                "home"
            ]
        )

    def test_schema_with_pattern_properties(
        self, valid_activity_dict
    ):
        """Test schema with pattern properties."""
        valid_activity_dict["activity_schema"] = {
            "type": "object",
            "patternProperties": {
                "^S_": {"type": "string"},
                "^I_": {"type": "integer"},
            },
            "additionalProperties": False,
        }
        activity = ActivityData(**valid_activity_dict)
        assert (
            "patternProperties" in activity.activity_schema
        )

    def test_schema_with_dependencies(
        self, valid_activity_dict
    ):
        """Test schema with property dependencies."""
        valid_activity_dict["activity_schema"] = {
            "type": "object",
            "properties": {
                "credit_card": {"type": "string"},
                "billing_address": {"type": "string"},
            },
            "dependencies": {
                "credit_card": ["billing_address"]
            },
        }
        activity = ActivityData(**valid_activity_dict)
        assert "dependencies" in activity.activity_schema
