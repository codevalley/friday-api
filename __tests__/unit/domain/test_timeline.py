"""Unit tests for timeline domain models."""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from domain.timeline import (
    TimelineEventData,
    TimelineEventType,
)
from domain.exceptions import TimelineValidationError


@pytest.fixture
def valid_timeline_data() -> Dict[str, Any]:
    """Fixture providing valid timeline event data."""
    return {
        "entity_type": TimelineEventType.TASK_CREATED,
        "entity_id": 1,
        "user_id": "test-user",
        "timestamp": datetime.now(timezone.utc),
        "title": "Test Task",
        "description": "Test Description",
        "content": "Test Content",
        "metadata": {"status": "pending"},
    }


def test_create_valid_timeline_event(valid_timeline_data):
    """Test creating a valid timeline event."""
    event = TimelineEventData(**valid_timeline_data)
    assert (
        event.entity_type == TimelineEventType.TASK_CREATED
    )
    assert event.entity_id == 1
    assert event.user_id == "test-user"
    assert isinstance(event.timestamp, datetime)
    assert event.title == "Test Task"
    assert event.description == "Test Description"
    assert event.content == "Test Content"
    assert event.metadata == {"status": "pending"}


def test_create_minimal_timeline_event():
    """Test creating a timeline event with only required fields."""
    event = TimelineEventData(
        entity_type=TimelineEventType.NOTE_CREATED,
        entity_id=1,
        user_id="test-user",
        timestamp=datetime.now(timezone.utc),
    )
    assert (
        event.entity_type == TimelineEventType.NOTE_CREATED
    )
    assert event.title is None
    assert event.description is None
    assert event.content is None
    assert event.metadata is None


@pytest.mark.parametrize(
    "field,invalid_value,expected_error",
    [
        (
            "entity_type",
            "invalid_type",
            "Invalid entity type",
        ),
        ("entity_id", 0, "Invalid entity ID"),
        ("entity_id", -1, "Invalid entity ID"),
        ("user_id", "", "user_id cannot be empty"),
        (
            "timestamp",
            "not-a-datetime",
            "Invalid timestamp",
        ),
        ("title", 123, "Title must be a string"),
        (
            "description",
            123,
            "Description must be a string",
        ),
        ("content", 123, "Content must be a string"),
        (
            "metadata",
            "not-a-dict",
            "Metadata must be a dictionary",
        ),
    ],
)
def test_invalid_timeline_event_data(
    valid_timeline_data,
    field: str,
    invalid_value: Any,
    expected_error: str,
):
    """Test validation errors for invalid timeline event data."""
    data = valid_timeline_data.copy()
    data[field] = invalid_value

    with pytest.raises(TimelineValidationError) as exc:
        TimelineEventData(**data)
    assert expected_error in str(exc.value)


def test_to_dict_conversion(valid_timeline_data):
    """Test converting timeline event to dictionary."""
    event = TimelineEventData(**valid_timeline_data)
    event_dict = event.to_dict()

    assert (
        event_dict["type"]
        == valid_timeline_data["entity_type"].value
    )
    assert (
        event_dict["id"] == valid_timeline_data["entity_id"]
    )
    assert (
        event_dict["user_id"]
        == valid_timeline_data["user_id"]
    )
    assert isinstance(
        event_dict["timestamp"], str
    )  # ISO format string
    assert (
        event_dict["title"] == valid_timeline_data["title"]
    )
    assert (
        event_dict["description"]
        == valid_timeline_data["description"]
    )
    assert (
        event_dict["content"]
        == valid_timeline_data["content"]
    )
    assert (
        event_dict["metadata"]
        == valid_timeline_data["metadata"]
    )


def test_to_dict_with_minimal_data():
    """Test converting minimal timeline event to dictionary."""
    event = TimelineEventData(
        entity_type=TimelineEventType.MOMENT_CREATED,
        entity_id=1,
        user_id="test-user",
        timestamp=datetime.now(timezone.utc),
    )
    event_dict = event.to_dict()

    assert event_dict["type"] == "moment_created"
    assert event_dict["id"] == 1
    assert event_dict["title"] is None
    assert event_dict["description"] is None
    assert event_dict["content"] is None
    assert (
        event_dict["metadata"] == {}
    )  # Empty dict for None metadata


def test_timeline_event_immutability(valid_timeline_data):
    """Test that timeline event data is immutable after creation."""
    event = TimelineEventData(**valid_timeline_data)

    # Metadata should be a new dict
    assert (
        event.metadata
        is not valid_timeline_data["metadata"]
    )

    # Modifying the original data should not affect the event
    valid_timeline_data["metadata"]["new_key"] = "new_value"
    assert "new_key" not in event.metadata
