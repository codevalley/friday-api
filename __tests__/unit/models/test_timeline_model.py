"""Unit tests for TimelineModel."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from orm.TimelineModel import Timeline
from domain.timeline import TimelineEventType


def test_timeline_model_initialization():
    """Test creating a timeline event with all fields."""
    timestamp = datetime.now(timezone.utc)
    event = Timeline(
        event_type=TimelineEventType.TASK_CREATED,
        user_id="test-user",
        event_metadata={"task_id": 123},
        timestamp=timestamp,
    )

    assert (
        event.event_type == TimelineEventType.TASK_CREATED
    )
    assert event.user_id == "test-user"
    assert event.event_metadata == {"task_id": 123}
    assert event.timestamp == timestamp


def test_timeline_model_db_persistence(db_session):
    """Test persisting timeline event to database."""
    # Create and add event
    event = Timeline(
        event_type=TimelineEventType.NOTE_CREATED,
        user_id="test-user",
        event_metadata={"note_id": 456},
    )
    db_session.add(event)
    db_session.commit()

    # Verify it was saved
    saved_event = db_session.get(Timeline, event.id)
    assert saved_event is not None
    assert (
        saved_event.event_type
        == TimelineEventType.NOTE_CREATED
    )
    assert saved_event.user_id == "test-user"
    assert saved_event.event_metadata == {"note_id": 456}
    assert saved_event.timestamp is not None


def test_timeline_model_required_fields(db_session):
    """Test that required fields are enforced."""
    # Test missing event_type
    with pytest.raises(IntegrityError):
        event = Timeline(
            user_id="test-user",
            event_metadata={"task_id": 123},
        )
        db_session.add(event)
        db_session.commit()

    db_session.rollback()

    # Test missing user_id
    with pytest.raises(IntegrityError):
        event = Timeline(
            event_type=TimelineEventType.TASK_CREATED,
            event_metadata={"task_id": 123},
        )
        db_session.add(event)
        db_session.commit()

    db_session.rollback()

    # Test missing event_metadata
    with pytest.raises(IntegrityError):
        event = Timeline(
            event_type=TimelineEventType.TASK_CREATED,
            user_id="test-user",
        )
        db_session.add(event)
        db_session.commit()


def test_timeline_model_string_representation():
    """Test the string representation of timeline events."""
    timestamp = datetime.now(timezone.utc)
    event = Timeline(
        id=1,
        event_type=TimelineEventType.MOMENT_CREATED,
        user_id="test-user",
        event_metadata={"moment_id": 789},
        timestamp=timestamp,
    )

    expected_str = (
        f"Timeline(id=1, "
        f"event_type={TimelineEventType.MOMENT_CREATED}, "
        f"user_id=test-user, "
        f"timestamp={timestamp})"
    )
    assert str(event) == expected_str


def test_timeline_model_indexes(db_session):
    """Test that indexes are working correctly."""
    # Create some test data
    events = [
        Timeline(
            event_type=TimelineEventType.TASK_CREATED,
            user_id="user1",
            event_metadata={"task_id": i},
        )
        for i in range(5)
    ]
    events.extend(
        [
            Timeline(
                event_type=TimelineEventType.NOTE_CREATED,
                user_id="user2",
                event_metadata={"note_id": i},
            )
            for i in range(5)
        ]
    )

    for event in events:
        db_session.add(event)
    db_session.commit()

    # Test event_type index
    task_events = (
        db_session.query(Timeline)
        .filter(
            Timeline.event_type
            == TimelineEventType.TASK_CREATED
        )
        .all()
    )
    assert len(task_events) == 5
    assert all(
        e.event_type == TimelineEventType.TASK_CREATED
        for e in task_events
    )

    # Test user_id index
    user2_events = (
        db_session.query(Timeline)
        .filter(Timeline.user_id == "user2")
        .all()
    )
    assert len(user2_events) == 5
    assert all(e.user_id == "user2" for e in user2_events)

    # Test timestamp index
    recent_events = (
        db_session.query(Timeline)
        .order_by(Timeline.timestamp.desc())
        .limit(3)
        .all()
    )
    assert len(recent_events) == 3
    for i in range(len(recent_events) - 1):
        assert (
            recent_events[i].timestamp
            >= recent_events[i + 1].timestamp
        )
