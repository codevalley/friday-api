from datetime import datetime, timedelta, UTC
import pytest
from sqlalchemy.orm import Session

from repositories.TimelineRepository import (
    TimelineRepository,
)
from orm.TimelineModel import Timeline as TimelineModel
from domain.timeline import TimelineEventType


@pytest.fixture
def timeline_repository(
    db_session: Session,
) -> TimelineRepository:
    """Create a timeline repository instance for testing"""
    return TimelineRepository(db_session)


@pytest.fixture
def sample_events(
    db_session: Session,
) -> list[TimelineModel]:
    """Create sample timeline events for testing"""
    # Clear existing events
    db_session.query(TimelineModel).delete()
    db_session.commit()

    events = []
    base_time = datetime.now(UTC)

    # Create events for two users with different types
    for i in range(5):
        events.append(
            TimelineModel(
                event_type=TimelineEventType.TASK_CREATED,
                user_id="user1",
                event_metadata={"task_id": f"task{i}"},
                timestamp=base_time - timedelta(hours=i),
            )
        )
        events.append(
            TimelineModel(
                event_type=TimelineEventType.NOTE_CREATED,
                user_id="user2",
                event_metadata={"note_id": f"note{i}"},
                timestamp=base_time - timedelta(hours=i),
            )
        )

    # Add to database
    for event in events:
        db_session.add(event)
    db_session.commit()

    return events


def test_get_recent_by_user(
    timeline_repository: TimelineRepository,
    sample_events: list[TimelineModel],
):
    """Test getting recent events for a specific user"""
    # Get recent events for user1
    events = timeline_repository.get_recent_by_user(
        "user1", limit=3
    )
    assert len(events) == 3
    assert all(e.user_id == "user1" for e in events)
    assert all(
        e.event_type == TimelineEventType.TASK_CREATED
        for e in events
    )

    # Verify ordering (most recent first)
    for i in range(len(events) - 1):
        assert events[i].timestamp > events[i + 1].timestamp


def test_list_events_pagination(
    timeline_repository: TimelineRepository,
    sample_events: list[TimelineModel],
):
    """Test pagination of timeline events"""
    # Get first page
    result = timeline_repository.list_events(page=1, size=4)
    assert len(result.items) == 4
    assert result.total == 10  # Total sample events
    assert result.pages == 3  # Ceil(10/4)
    assert result.page == 1
    assert result.size == 4

    # Get second page
    result = timeline_repository.list_events(page=2, size=4)
    assert len(result.items) == 4

    # Get last page
    result = timeline_repository.list_events(page=3, size=4)
    assert len(result.items) == 2  # Remaining items


def test_list_events_filtering(
    timeline_repository: TimelineRepository,
    sample_events: list[TimelineModel],
):
    """Test filtering timeline events"""
    # Filter by event type
    result = timeline_repository.list_events(
        event_type=TimelineEventType.TASK_CREATED
    )
    assert len(result.items) == 5
    assert all(
        e.event_type == TimelineEventType.TASK_CREATED
        for e in result.items
    )

    # Filter by user
    result = timeline_repository.list_events(
        user_id="user2"
    )
    assert len(result.items) == 5
    assert all(e.user_id == "user2" for e in result.items)


def test_list_events_time_range(
    timeline_repository: TimelineRepository,
    sample_events: list[TimelineModel],
):
    """Test filtering timeline events by time range"""
    now = datetime.now(UTC)

    # Get events from last 2 hours
    result = timeline_repository.list_events(
        start_time=now - timedelta(hours=2)
    )
    assert (
        len(result.items) == 4
    )  # 2 events per user in last 2 hours
    # (excluding events exactly 2 hours ago)

    # Get events between 2-4 hours ago
    result = timeline_repository.list_events(
        start_time=now - timedelta(hours=4),
        end_time=now - timedelta(hours=2),
    )
    assert (
        len(result.items) == 4
    )  # 2 events per user in this range


def test_list_events_combined_filters(
    timeline_repository: TimelineRepository,
    sample_events: list[TimelineModel],
):
    """Test combining multiple filters"""
    now = datetime.now(UTC)

    result = timeline_repository.list_events(
        event_type=TimelineEventType.TASK_CREATED,
        user_id="user1",
        start_time=now - timedelta(hours=3),
    )
    assert len(result.items) == 3
    assert all(
        e.event_type == TimelineEventType.TASK_CREATED
        and e.user_id == "user1"
        for e in result.items
    )
