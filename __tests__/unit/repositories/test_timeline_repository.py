"""Unit tests for TimelineRepository."""

import pytest
from datetime import datetime, timedelta, timezone

from repositories.TimelineRepository import (
    TimelineRepository,
)
from orm.TimelineModel import Timeline
from domain.timeline import TimelineEventType


@pytest.fixture
def timeline_repository(db_session):
    """Create a timeline repository instance."""
    return TimelineRepository(db_session)


@pytest.fixture
def sample_timeline_events(db_session):
    """Create sample timeline events for testing."""
    # Clear any existing data
    db_session.query(Timeline).delete()
    db_session.commit()

    base_time = datetime.now(timezone.utc)
    events = []

    # Create events for user1
    for i in range(10):
        event = Timeline(
            event_type=(
                TimelineEventType.TASK_CREATED
                if i % 2 == 0
                else TimelineEventType.NOTE_CREATED
            ),
            user_id="user1",
            event_metadata={"id": i},
            timestamp=base_time
            - timedelta(
                hours=i
            ),  # Events spaced 1 hour apart
        )
        events.append(event)
        db_session.add(event)

    # Create events for user2
    for i in range(5):
        event = Timeline(
            event_type=TimelineEventType.MOMENT_CREATED,
            user_id="user2",
            event_metadata={"id": i + 10},
            timestamp=base_time - timedelta(hours=i),
        )
        events.append(event)
        db_session.add(event)

    db_session.commit()
    return events


def test_get_recent_by_user(
    timeline_repository, sample_timeline_events
):
    """Test getting recent events for a specific user."""
    # Test with default limit
    events = timeline_repository.get_recent_by_user("user1")
    assert len(events) == 5
    assert all(e.user_id == "user1" for e in events)
    assert (
        events[0].timestamp > events[-1].timestamp
    )  # Check ordering

    # Test with custom limit
    events = timeline_repository.get_recent_by_user(
        "user1", limit=3
    )
    assert len(events) == 3
    assert all(e.user_id == "user1" for e in events)

    # Test with user having fewer events than limit
    events = timeline_repository.get_recent_by_user(
        "user2", limit=10
    )
    assert len(events) == 5  # user2 only has 5 events
    assert all(e.user_id == "user2" for e in events)

    # Test with non-existent user
    events = timeline_repository.get_recent_by_user(
        "non-existent"
    )
    assert len(events) == 0


def test_list_events_pagination(
    timeline_repository, sample_timeline_events
):
    """Test pagination of timeline events."""
    # Test first page
    result = timeline_repository.list_events(page=1, size=5)
    assert len(result.items) == 5
    assert (
        result.total == 15
    )  # Total sample events (10 for user1 + 5 for user2)
    assert result.page == 1
    assert result.size == 5
    assert (
        result.pages == 3
    )  # 15 items / 5 per page = 3 pages

    # Test last page
    result = timeline_repository.list_events(page=3, size=5)
    assert len(result.items) == 5
    assert result.page == 3

    # Test with page size larger than total
    result = timeline_repository.list_events(
        page=1, size=20
    )
    assert len(result.items) == 15
    assert result.pages == 1


def test_list_events_filtering(
    timeline_repository, sample_timeline_events
):
    """Test filtering of timeline events."""
    # Test event_type filter
    result = timeline_repository.list_events(
        event_type=TimelineEventType.TASK_CREATED
    )
    assert all(
        e.event_type == TimelineEventType.TASK_CREATED
        for e in result.items
    )

    # Test user_id filter
    result = timeline_repository.list_events(
        user_id="user2"
    )
    assert all(e.user_id == "user2" for e in result.items)
    assert result.total == 5  # user2 has 5 events

    # Test time range filter
    base_time = sample_timeline_events[
        0
    ].timestamp  # Use timestamp from sample data
    result = timeline_repository.list_events(
        start_time=base_time - timedelta(hours=3),
        end_time=base_time,
    )
    assert all(
        base_time - timedelta(hours=3)
        <= e.timestamp
        <= base_time
        for e in result.items
    )


def test_list_events_combined_filters(
    timeline_repository, sample_timeline_events
):
    """Test combining multiple filters."""
    base_time = sample_timeline_events[
        0
    ].timestamp  # Use timestamp from sample data

    result = timeline_repository.list_events(
        page=1,
        size=10,
        event_type=TimelineEventType.TASK_CREATED,
        user_id="user1",
        start_time=base_time - timedelta(hours=5),
    )

    assert all(
        e.event_type == TimelineEventType.TASK_CREATED
        for e in result.items
    )
    assert all(e.user_id == "user1" for e in result.items)
    assert all(
        e.timestamp >= base_time - timedelta(hours=5)
        for e in result.items
    )


def test_list_events_empty_results(
    timeline_repository, db_session
):
    """Test listing events when no events exist."""
    # Clear any existing data
    db_session.query(Timeline).delete()
    db_session.commit()

    result = timeline_repository.list_events()
    assert len(result.items) == 0
    assert result.total == 0
    assert result.pages == 0
