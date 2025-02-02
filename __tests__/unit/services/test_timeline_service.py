"""Unit tests for TimelineService."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from fastapi import HTTPException, status

from services.TimelineService import TimelineService
from domain.timeline import TimelineEventType
from schemas.pydantic.TimelineSchema import (
    TimelineList,
    TimelineEvent,
)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def timeline_service(mock_db):
    """Create a TimelineService instance with mocked dependencies."""
    service = TimelineService(db=mock_db)
    # Mock the repository's list_events method
    service.timeline_repo.list_events = MagicMock()
    return service


@pytest.fixture
def sample_timeline_events():
    """Sample timeline events for testing."""
    now = datetime.now(timezone.utc)
    return [
        {
            "id": 1,
            "event_type": TimelineEventType.TASK_CREATED,
            "user_id": "user1",
            "event_metadata": {"task_id": 1},
            "timestamp": now,
        },
        {
            "id": 2,
            "event_type": TimelineEventType.TASK_CREATED,
            "user_id": "user1",
            "event_metadata": {"task_id": 2},
            "timestamp": now + timedelta(minutes=1),
        },
        {
            "id": 3,
            "event_type": TimelineEventType.TASK_CREATED,
            "user_id": "user1",
            "event_metadata": {"task_id": 3},
            "timestamp": now + timedelta(minutes=2),
        },
    ]


@pytest.mark.asyncio
async def test_get_recent_events(
    timeline_service, mock_db, sample_timeline_events
):
    """Test getting recent events for a user."""
    # Setup mock
    mock_result = sample_timeline_events[:2]
    mock_db.query().filter().order_by().limit().all.return_value = (
        mock_result
    )

    # Test
    events = await timeline_service.get_recent_events(
        "user1", limit=2
    )

    # Verify
    assert len(events) == 2
    assert events[0].id == 1
    assert (
        events[0].event_type
        == TimelineEventType.TASK_CREATED
    )
    assert events[1].id == 2
    assert (
        events[1].event_type
        == TimelineEventType.TASK_CREATED
    )


@pytest.mark.asyncio
async def test_list_events_pagination(
    timeline_service, mock_db, sample_timeline_events
):
    """Test pagination of timeline events."""
    # Setup mock
    timeline_list = TimelineList(
        items=[
            TimelineEvent(**event)
            for event in sample_timeline_events
        ],
        total=3,
        page=1,
        size=2,
        pages=2,
    )
    timeline_service.timeline_repo.list_events.return_value = (
        timeline_list
    )

    # Test
    result = await timeline_service.list_events(
        page=1, size=2
    )

    # Verify
    assert len(result["items"]) == 3
    assert result["total"] == 3
    assert result["page"] == 1
    assert result["size"] == 2
    assert result["pages"] == 2


@pytest.mark.asyncio
async def test_get_events_by_type(
    timeline_service, mock_db, sample_timeline_events
):
    """Test filtering events by type."""
    # Setup mock
    timeline_list = TimelineList(
        items=[TimelineEvent(**sample_timeline_events[0])],
        total=1,
        page=1,
        size=50,
        pages=1,
    )
    timeline_service.timeline_repo.list_events.return_value = (
        timeline_list
    )

    # Test
    result = await timeline_service.get_events_by_type(
        event_type=TimelineEventType.TASK_CREATED,
        user_id="user1",
    )

    # Verify
    assert len(result["items"]) == 1
    assert result["total"] == 1
    assert result["page"] == 1
    assert result["size"] == 50
    assert result["pages"] == 1


@pytest.mark.asyncio
async def test_get_events_in_timerange(
    timeline_service, mock_db, sample_timeline_events
):
    """Test getting events within a time range."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=4)
    end_time = now

    # Setup mock
    timeline_list = TimelineList(
        items=[
            TimelineEvent(**event)
            for event in sample_timeline_events
        ],
        total=3,
        page=1,
        size=50,
        pages=1,
    )
    timeline_service.timeline_repo.list_events.return_value = (
        timeline_list
    )

    # Test
    result = await timeline_service.get_events_in_timerange(
        user_id="user1",
        start_time=start_time,
        end_time=end_time,
    )

    # Verify
    assert len(result["items"]) == 3
    assert result["total"] == 3
    assert result["page"] == 1
    assert result["size"] == 50
    assert result["pages"] == 1


@pytest.mark.asyncio
async def test_get_events_in_timerange_invalid_range(
    timeline_service,
):
    """Test error handling for invalid time range."""
    now = datetime.now(timezone.utc)

    # Test with end_time before start_time
    with pytest.raises(HTTPException) as exc_info:
        await timeline_service.get_events_in_timerange(
            user_id="user1",
            start_time=now,
            end_time=now - timedelta(hours=1),
        )

    # Verify the error details
    assert (
        exc_info.value.status_code
        == status.HTTP_400_BAD_REQUEST
    )
    assert (
        exc_info.value.detail["message"]
        == "Start time must be before end time"
    )
    assert (
        exc_info.value.detail["code"]
        == "timeline_validation_error"
    )
