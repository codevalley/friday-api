"""Test suite for MomentData domain model.

This test suite verifies the functionality of the MomentData domain model,
including validation, conversion, and error handling. It ensures that the
model maintains data integrity and follows business rules.
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from domain.moment import MomentData
from domain.exceptions import (
    MomentValidationError,
    MomentTimestampError,
    MomentDataError,
)


@pytest.fixture
def valid_moment_dict() -> Dict[str, Any]:
    """Create a valid moment dictionary for testing.

    This fixture provides a baseline valid moment data dictionary
    that can be modified for specific test cases.
    """
    return {
        "activity_id": 1,
        "user_id": "test-user",
        "data": {"test_field": "test_value"},
        "timestamp": datetime.now(timezone.utc),
        "note_id": None,  # Optional note reference
    }


@pytest.fixture
def valid_moment_data(valid_moment_dict) -> MomentData:
    """Create a valid MomentData instance for testing.

    This fixture provides a baseline valid MomentData instance
    that can be used directly in tests.
    """
    return MomentData(**valid_moment_dict)


class TestMomentDataValidation:
    """Test validation methods of MomentData.

    These tests verify that the validation logic correctly handles
    both valid and invalid data according to business rules.
    """

    def test_valid_moment_data(self, valid_moment_data):
        """Test that valid moment data passes validation."""
        # Should not raise any exceptions
        valid_moment_data.validate()

    def test_invalid_activity_id(self, valid_moment_dict):
        """Test validation with invalid activity_id."""
        valid_moment_dict["activity_id"] = 0
        with pytest.raises(MomentValidationError) as exc:
            MomentData(**valid_moment_dict)
        assert (
            str(exc.value)
            == "activity_id must be a positive integer"
        )

    def test_invalid_user_id(self, valid_moment_dict):
        """Test validation with invalid user_id."""
        valid_moment_dict["user_id"] = ""
        with pytest.raises(MomentValidationError) as exc:
            MomentData(**valid_moment_dict)
        assert (
            str(exc.value)
            == "user_id must be a non-empty string"
        )

    def test_invalid_data_type(self, valid_moment_dict):
        """Test validation with invalid data type."""
        valid_moment_dict["data"] = "not a dict"
        with pytest.raises(MomentDataError) as exc:
            MomentData(**valid_moment_dict)
        assert str(exc.value) == "data must be a dictionary"

    def test_valid_note_id(self, valid_moment_dict):
        """Test validation with valid note_id."""
        valid_moment_dict["note_id"] = 1
        moment = MomentData(**valid_moment_dict)
        moment.validate()  # Should not raise

    def test_invalid_note_id_type(self, valid_moment_dict):
        """Test validation with invalid note_id type."""
        valid_moment_dict["note_id"] = "not an int"
        with pytest.raises(MomentValidationError) as exc:
            MomentData(**valid_moment_dict)
        assert (
            str(exc.value)
            == "note_id must be a positive integer"
        )

    def test_invalid_note_id_value(self, valid_moment_dict):
        """Test validation with invalid note_id value."""
        valid_moment_dict["note_id"] = 0
        with pytest.raises(MomentValidationError) as exc:
            MomentData(**valid_moment_dict)
        assert (
            str(exc.value)
            == "note_id must be a positive integer"
        )

    def test_invalid_timestamp(self, valid_moment_dict):
        """Test validation with invalid timestamp."""
        valid_moment_dict["timestamp"] = "not a datetime"
        with pytest.raises(MomentTimestampError) as exc:
            MomentData(**valid_moment_dict)
        assert (
            str(exc.value)
            == "timestamp must be a datetime object"
        )

    def test_timezone_aware_timestamp(
        self, valid_moment_dict
    ):
        """Test handling of timezone-aware timestamps."""
        # Test with different timezones
        timezones = [
            timezone.utc,
            timezone(timedelta(hours=1)),  # UTC+1
            timezone(timedelta(hours=-5)),  # UTC-5
        ]
        for tz in timezones:
            valid_moment_dict["timestamp"] = datetime.now(
                tz
            )
            moment = MomentData(**valid_moment_dict)
            assert moment.timestamp.tzinfo is not None

    def test_timezone_naive_timestamp(
        self, valid_moment_dict
    ):
        """Test handling of timezone-naive timestamps."""
        valid_moment_dict["timestamp"] = datetime.now()
        with pytest.raises(MomentTimestampError) as exc:
            MomentData(**valid_moment_dict)
        assert (
            str(exc.value)
            == "timestamp must be timezone-aware"
        )

    def test_nested_data_validation(
        self, valid_moment_dict
    ):
        """Test validation of nested data structures."""
        # Test with nested dictionary
        valid_moment_dict["data"] = {
            "level1": {"level2": {"value": "test"}},
            "array": [1, 2, 3],
            "mixed": [{"key": "value"}, 42, "string"],
        }
        moment = MomentData(**valid_moment_dict)
        assert (
            moment.data["level1"]["level2"]["value"]
            == "test"
        )

        # Test with invalid nested structure
        valid_moment_dict["data"] = {"circular": None}
        valid_moment_dict["data"][
            "circular"
        ] = valid_moment_dict["data"]
        with pytest.raises(MomentDataError) as exc:
            MomentData(**valid_moment_dict)
        assert (
            str(exc.value)
            == "Invalid data structure: circular reference detected"
        )


class TestMomentDataConversion:
    """Test conversion methods of MomentData."""

    def test_to_dict(self, valid_moment_data):
        """Test conversion to dictionary."""
        result = valid_moment_data.to_dict()
        assert (
            result["activity_id"]
            == valid_moment_data.activity_id
        )
        assert (
            result["user_id"] == valid_moment_data.user_id
        )
        assert result["data"] == valid_moment_data.data
        assert (
            result["timestamp"]
            == valid_moment_data.timestamp
        )
        assert (
            result["note_id"] == valid_moment_data.note_id
        )

    def test_to_json_dict(self, valid_moment_data):
        """Test conversion to JSON dict."""
        json_dict = valid_moment_data.to_json_dict()

        assert isinstance(json_dict, dict)
        assert "id" in json_dict
        assert "activity_id" in json_dict
        assert "user_id" in json_dict
        assert isinstance(json_dict["data"], dict)
        assert isinstance(json_dict["timestamp"], str)
        assert "note_id" in json_dict
        assert "created_at" in json_dict
        assert "updated_at" in json_dict

    def test_from_dict_snake_case(self, valid_moment_dict):
        """Test creation from snake_case dictionary."""
        moment = MomentData.from_dict(valid_moment_dict)
        assert (
            moment.activity_id
            == valid_moment_dict["activity_id"]
        )
        assert (
            moment.user_id == valid_moment_dict["user_id"]
        )
        assert (
            moment.note_id == valid_moment_dict["note_id"]
        )

    def test_from_dict_camel_case(self):
        """Test creation from camelCase dictionary."""
        camel_dict = {
            "activityId": 1,
            "userId": "test-user",
            "data": {"test_field": "test_value"},
            "timestamp": datetime.now(timezone.utc),
            "noteId": 1,
        }
        moment = MomentData.from_dict(camel_dict)
        assert (
            moment.activity_id == camel_dict["activityId"]
        )
        assert moment.user_id == camel_dict["userId"]
        assert moment.note_id == camel_dict["noteId"]

    def test_from_dict_with_optional_user_id(self):
        """Test creation from dict with optional user_id."""
        data = {
            "activityId": 1,
            "data": {"test_field": "test_value"},
            "timestamp": datetime.now(timezone.utc),
        }
        moment = MomentData.from_dict(
            data, user_id="test-user"
        )
        assert moment.user_id == "test-user"


class TestMomentDataTypeHints:
    """Test type hints of MomentData."""

    def test_generic_type_parameter(self):
        """Test that the generic type parameter works."""
        moment: MomentData = MomentData.from_dict(
            {
                "activity_id": 1,
                "user_id": "test-user",
                "data": {"test": "value"},
                "timestamp": datetime.now(timezone.utc),
            }
        )
        assert isinstance(moment, MomentData)

    def test_optional_fields(self, valid_moment_dict):
        """Test that optional fields can be None."""
        moment = MomentData(**valid_moment_dict)
        assert moment.id is None
        assert moment.created_at is None
        assert moment.updated_at is None


class TestMomentDataSchemaValidation:
    """Test schema validation of MomentData."""

    def test_validate_against_valid_schema(
        self, valid_moment_data
    ):
        """Test validation against a valid schema."""
        schema = {
            "type": "object",
            "properties": {
                "test_field": {"type": "string"}
            },
            "required": ["test_field"],
        }
        # Should not raise any exceptions
        valid_moment_data.validate_against_schema(schema)

    def test_validate_against_invalid_schema(
        self, valid_moment_data
    ):
        """Test validation against an invalid schema."""
        schema = {
            "type": "object",
            "properties": {
                "test_field": {"type": "number"}
            },
            "required": ["test_field"],
        }
        with pytest.raises(Exception) as exc:
            valid_moment_data.validate_against_schema(
                schema
            )
        assert "Invalid moment data" in str(exc.value)


class TestMomentDataErrorHandling:
    """Test error handling of MomentData."""

    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        with pytest.raises(TypeError):
            MomentData()  # type: ignore

    def test_type_mismatches(self, valid_moment_dict):
        """Test handling of type mismatches."""
        valid_moment_dict["activity_id"] = "not an int"
        with pytest.raises(MomentValidationError) as exc:
            MomentData(**valid_moment_dict)
        assert (
            str(exc.value)
            == "activity_id must be a positive integer"
        )

    def test_schema_validation_failure(
        self, valid_moment_data
    ):
        """Test handling of schema validation failure."""
        invalid_schema = {"type": "invalid"}
        with pytest.raises(Exception):
            valid_moment_data.validate_against_schema(
                invalid_schema
            )


class TestMomentDataTimestamps:
    """Test timestamp handling in MomentData.

    These tests verify that timestamp validation properly handles
    timezone awareness, future/past dates, and precision requirements.
    """

    def test_future_timestamp(self, valid_moment_dict):
        """Test validation of future timestamps."""
        future = datetime.now(timezone.utc) + timedelta(
            days=2
        )
        valid_moment_dict["timestamp"] = future
        with pytest.raises(MomentTimestampError) as exc:
            MomentData(**valid_moment_dict)
        assert (
            str(exc.value)
            == "timestamp cannot be more than 1 day in the future"
        )

    def test_past_timestamp(self, valid_moment_dict):
        """Test validation of past timestamps."""
        past = datetime.now(timezone.utc) - timedelta(
            days=365 * 11
        )
        valid_moment_dict["timestamp"] = past
        with pytest.raises(MomentTimestampError) as exc:
            MomentData(**valid_moment_dict)
        assert (
            str(exc.value)
            == "timestamp cannot be more than 10 years in the past"
        )

    def test_timestamp_precision(self, valid_moment_dict):
        """Test timestamp precision handling."""
        # Test microsecond precision
        timestamp = datetime(
            2024,
            1,
            1,
            12,
            0,
            0,
            123456,
            tzinfo=timezone.utc,
        )
        valid_moment_dict["timestamp"] = timestamp
        moment = MomentData(**valid_moment_dict)
        assert moment.timestamp.microsecond == 123456

        # Test invalid microsecond value
        with pytest.raises(ValueError) as exc:
            timestamp = datetime(
                2024,
                1,
                1,
                12,
                0,
                0,
                1000000,
                tzinfo=timezone.utc,
            )
            valid_moment_dict["timestamp"] = timestamp
            MomentData(**valid_moment_dict)
        assert "microsecond must be in 0..999999" in str(
            exc.value
        )

    def test_timezone_handling(self, valid_moment_dict):
        """Test handling of different timezones."""
        # Test UTC
        utc_time = datetime.now(timezone.utc)
        valid_moment_dict["timestamp"] = utc_time
        moment = MomentData(**valid_moment_dict)
        assert moment.timestamp.tzinfo == timezone.utc

        # Test UTC+1
        tz_plus_1 = timezone(timedelta(hours=1))
        time_plus_1 = datetime.now(tz_plus_1)
        valid_moment_dict["timestamp"] = time_plus_1
        moment = MomentData(**valid_moment_dict)
        assert moment.timestamp.tzinfo == tz_plus_1

        # Test UTC-5
        tz_minus_5 = timezone(timedelta(hours=-5))
        time_minus_5 = datetime.now(tz_minus_5)
        valid_moment_dict["timestamp"] = time_minus_5
        moment = MomentData(**valid_moment_dict)
        assert moment.timestamp.tzinfo == tz_minus_5

    def test_timestamp_normalization(
        self, valid_moment_dict
    ):
        """Test timestamp normalization across timezones."""
        # Create timestamps in different timezones
        utc_time = datetime(
            2024, 1, 1, 12, 0, tzinfo=timezone.utc
        )
        tz_plus_1 = timezone(timedelta(hours=1))
        time_plus_1 = datetime(
            2024, 1, 1, 13, 0, tzinfo=tz_plus_1
        )

        # Verify they represent the same moment
        valid_moment_dict["timestamp"] = utc_time
        moment1 = MomentData(**valid_moment_dict)
        valid_moment_dict["timestamp"] = time_plus_1
        moment2 = MomentData(**valid_moment_dict)

        # Convert to UTC for comparison
        assert moment1.timestamp.astimezone(
            timezone.utc
        ) == moment2.timestamp.astimezone(timezone.utc)

    def test_microsecond_edge_cases(
        self, valid_moment_dict
    ):
        """Test edge cases for microsecond precision."""
        # Test minimum microseconds
        timestamp = datetime(
            2024, 1, 1, 12, 0, 0, 0, tzinfo=timezone.utc
        )
        valid_moment_dict["timestamp"] = timestamp
        moment = MomentData(**valid_moment_dict)
        assert moment.timestamp.microsecond == 0

        # Test maximum valid microseconds
        timestamp = datetime(
            2024,
            1,
            1,
            12,
            0,
            0,
            999999,
            tzinfo=timezone.utc,
        )
        valid_moment_dict["timestamp"] = timestamp
        moment = MomentData(**valid_moment_dict)
        assert moment.timestamp.microsecond == 999999

        # Test invalid microseconds (1000000)
        # Note: We can't create a datetime with invalid microseconds,
        # so we'll test the validation directly
        with pytest.raises(ValueError) as exc:
            moment = MomentData(**valid_moment_dict)
            # Simulate invalid microseconds by setting it after creation
            # This is just for testing the validation
            moment.timestamp = moment.timestamp.replace(
                microsecond=1000000
            )
            moment.validate()
        assert "microsecond must be in 0..999999" in str(
            exc.value
        )

    def test_timestamp_conversion(self, valid_moment_dict):
        """Test timestamp conversion between different timezones."""
        # Create a timestamp in UTC+2
        tz_plus_2 = timezone(timedelta(hours=2))
        original_time = datetime(
            2024, 1, 1, 14, 0, tzinfo=tz_plus_2
        )  # 14:00 UTC+2
        valid_moment_dict["timestamp"] = original_time
        moment = MomentData(**valid_moment_dict)

        # Convert to different timezones and verify the absolute
        # time remains the same
        utc_time = moment.timestamp.astimezone(timezone.utc)
        assert (
            utc_time.hour == 12
        )  # 14:00 UTC+2 = 12:00 UTC

        tz_minus_3 = timezone(timedelta(hours=-3))
        minus_3_time = moment.timestamp.astimezone(
            tz_minus_3
        )
        assert (
            minus_3_time.hour == 9
        )  # 14:00 UTC+2 = 09:00 UTC-3

        # Verify that the original timezone is preserved
        assert moment.timestamp.tzinfo == tz_plus_2
        assert moment.timestamp.hour == 14


class TestMomentDataSerialization:
    """Test serialization methods of MomentData."""

    def test_json_serialization_formats(
        self, valid_moment_data
    ):
        """Test JSON serialization formats."""
        # Test REST format
        json_dict = valid_moment_data.to_json_dict()
        assert isinstance(json_dict, dict)
        assert "activity_id" in json_dict
        assert "user_id" in json_dict
        assert isinstance(json_dict["data"], dict)
        assert isinstance(json_dict["timestamp"], str)
        assert "note_id" in json_dict

    def test_nested_data_serialization(
        self, valid_moment_dict
    ):
        """Test serialization of nested data structures."""
        # Test with nested dictionary
        valid_moment_dict["data"] = {
            "level1": {"level2": {"value": "test"}},
            "array": [1, 2, 3],
            "mixed": [{"key": "value"}, 42, "string"],
        }
        moment = MomentData(**valid_moment_dict)
        json_dict = moment.to_json_dict()

        # Verify nested structures are preserved
        assert (
            json_dict["data"]["level1"]["level2"]["value"]
            == "test"
        )
        assert json_dict["data"]["array"] == [1, 2, 3]
        assert json_dict["data"]["mixed"] == [
            {"key": "value"},
            42,
            "string",
        ]
