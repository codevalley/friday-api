"""Unit tests for TimelineSchema."""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from schemas.pydantic.TimelineSchema import (
    TimelineEvent,
    TimelineList,
)
from domain.timeline import TimelineEventType
from orm.TimelineModel import Timeline


def test_timeline_event_schema_valid():
    """Test creating a valid timeline event schema."""
    timestamp = datetime.now(timezone.utc)
    data = {
        "id": 1,
        "event_type": TimelineEventType.TASK_CREATED,
        "user_id": "test-user",
        "event_metadata": {"task_id": 123},
        "timestamp": timestamp,
    }
    event = TimelineEvent(**data)

    assert event.id == 1
    assert (
        event.event_type == TimelineEventType.TASK_CREATED
    )
    assert event.user_id == "test-user"
    assert event.event_metadata == {"task_id": 123}
    assert event.timestamp == timestamp


def test_timeline_event_schema_from_orm():
    """Test creating schema from ORM model."""
    timestamp = datetime.now(timezone.utc)
    orm_event = Timeline(
        id=1,
        event_type=TimelineEventType.NOTE_CREATED,
        user_id="test-user",
        event_metadata={"note_id": 456},
        timestamp=timestamp,
    )

    event = TimelineEvent.model_validate(orm_event)
    assert event.id == 1
    assert (
        event.event_type == TimelineEventType.NOTE_CREATED
    )
    assert event.user_id == "test-user"
    assert event.event_metadata == {"note_id": 456}
    assert event.timestamp == timestamp


@pytest.mark.parametrize(
    "field,invalid_value,error_msg",
    [
        (
            "id",
            "not-an-int",
            "Input should be a valid integer",
        ),
        (
            "event_type",
            "invalid-type",
            "Input should be 'task_created', 'task_updated', 'task_completed'",
        ),
        ("user_id", None, "Input should be a valid string"),
        (
            "event_metadata",
            "not-a-dict",
            "Input should be a valid dictionary",
        ),
        (
            "timestamp",
            "not-a-date",
            "Input should be a valid datetime",
        ),
    ],
)
def test_timeline_event_schema_validation(
    field, invalid_value, error_msg
):
    """Test validation of timeline event schema fields."""
    timestamp = datetime.now(timezone.utc)
    valid_data = {
        "id": 1,
        "event_type": TimelineEventType.TASK_CREATED,
        "user_id": "test-user",
        "event_metadata": {"task_id": 123},
        "timestamp": timestamp,
    }

    # Replace valid value with invalid one
    data = valid_data.copy()
    data[field] = invalid_value

    with pytest.raises(ValidationError) as exc:
        TimelineEvent(**data)
    assert error_msg in str(exc.value)


def test_timeline_list_schema():
    """Test timeline list schema with pagination."""
    timestamp = datetime.now(timezone.utc)
    events = [
        TimelineEvent(
            id=i,
            event_type=TimelineEventType.TASK_CREATED,
            user_id="test-user",
            event_metadata={"task_id": i},
            timestamp=timestamp,
        )
        for i in range(1, 4)
    ]

    timeline_list = TimelineList(
        items=events,
        total=10,
        page=1,
        size=3,
        pages=4,
    )

    assert len(timeline_list.items) == 3
    assert timeline_list.total == 10
    assert timeline_list.page == 1
    assert timeline_list.size == 3
    assert timeline_list.pages == 4

    # Verify each event in the list
    for i, event in enumerate(timeline_list.items, 1):
        assert event.id == i
        assert (
            event.event_type
            == TimelineEventType.TASK_CREATED
        )
        assert event.user_id == "test-user"
        assert event.event_metadata == {"task_id": i}
        assert event.timestamp == timestamp


def test_timeline_list_schema_empty():
    """Test timeline list schema with no items."""
    timeline_list = TimelineList(
        items=[],
        total=0,
        page=1,
        size=10,
        pages=0,
    )

    assert len(timeline_list.items) == 0
    assert timeline_list.total == 0
    assert timeline_list.page == 1
    assert timeline_list.size == 10
    assert timeline_list.pages == 0


def test_timeline_list_schema_validation():
    """Test validation of timeline list schema."""
    with pytest.raises(ValidationError) as exc:
        TimelineList(
            items="not-a-list",
            total=0,
            page=1,
            size=10,
            pages=0,
        )
    assert "Input should be a valid list" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        TimelineList(
            items=[{"invalid": "event"}],
            total=0,
            page=1,
            size=10,
            pages=0,
        )
    assert "validation error" in str(exc.value)
