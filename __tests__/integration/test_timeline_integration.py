"""Integration tests for Timeline API endpoints."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from fastapi import status
from typing import AsyncGenerator
from httpx import ASGITransport

from domain.timeline import TimelineEventType
from orm.TimelineModel import Timeline as TimelineModel
from configs.Database import get_db_connection
from dependencies import get_current_user


@pytest_asyncio.fixture
async def sample_timeline_events(
    test_db_session, test_user
):
    """Create sample timeline events for testing."""
    now = datetime.now(timezone.utc)
    events = [
        TimelineModel(
            id=1,
            event_type=TimelineEventType.TASK_CREATED,
            user_id=test_user.id,
            event_metadata={"task_id": 1},
            timestamp=now,
        ),
        TimelineModel(
            id=2,
            event_type=TimelineEventType.NOTE_CREATED,
            user_id=test_user.id,
            event_metadata={"note_id": 1},
            timestamp=now + timedelta(minutes=1),
        ),
        TimelineModel(
            id=3,
            event_type=TimelineEventType.TASK_COMPLETED,
            user_id=test_user.id,
            event_metadata={"task_id": 2},
            timestamp=now + timedelta(minutes=2),
        ),
    ]

    for event in events:
        test_db_session.add(event)
    test_db_session.commit()

    # Query the events back from the database to ensure they're attached
    # to the session
    fresh_events = (
        test_db_session.query(TimelineModel)
        .order_by(TimelineModel.id)
        .all()
    )
    yield fresh_events

    # Cleanup
    for event in fresh_events:
        test_db_session.delete(event)
    test_db_session.commit()


@pytest.fixture
def auth_headers(mock_auth_credentials):
    """Create authorization headers for requests."""
    return {
        "Authorization": f"Bearer {mock_auth_credentials.credentials}"
    }


@pytest_asyncio.fixture
async def async_client(
    fastapi_app, test_db_session, test_user
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""

    def override_get_db():
        try:
            yield test_db_session
        finally:
            test_db_session.close()

    async def mock_get_current_user():
        return test_user

    fastapi_app.dependency_overrides[
        get_db_connection
    ] = override_get_db
    fastapi_app.dependency_overrides[
        get_current_user
    ] = mock_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_list_timeline_events(
    async_client: AsyncClient,
    sample_timeline_events,
    auth_headers,
):
    """Test listing timeline events with pagination."""
    response = await async_client.get(
        "/v1/timeline",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert len(data["items"]) == len(sample_timeline_events)
    assert data["total"] == len(sample_timeline_events)
    assert data["page"] == 1
    assert (
        data["size"] == 50
    )  # Matches PaginationParams default

    # Verify the response structure matches our model
    first_event = data["items"][0]
    assert "event_type" in first_event
    assert "timestamp" in first_event
    assert (
        "event_metadata" in first_event
    )  # Updated to match TimelineEvent schema


@pytest.mark.asyncio
async def test_get_recent_events(
    async_client: AsyncClient,
    sample_timeline_events,
    auth_headers,
):
    """Test retrieving recent timeline events."""
    response = await async_client.get(
        "/v1/timeline/recent",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    events = response.json()["data"]
    assert len(events) == len(sample_timeline_events)

    # Verify events are ordered by timestamp (most recent first)
    timestamps = [event["timestamp"] for event in events]
    assert timestamps == sorted(timestamps, reverse=True)


@pytest.mark.asyncio
async def test_get_events_by_type(
    async_client: AsyncClient,
    sample_timeline_events,
    auth_headers,
):
    """Test filtering timeline events by type."""
    # Use enum value for the URL
    event_type = TimelineEventType.TASK_CREATED.value
    response = await async_client.get(
        f"/v1/timeline/by-type/{event_type}",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert len(data["items"]) > 0
    assert all(
        item["event_type"]
        == TimelineEventType.TASK_CREATED.value
        for item in data["items"]
    )


@pytest.mark.asyncio
async def test_get_events_in_timerange(
    async_client: AsyncClient,
    sample_timeline_events,
    auth_headers,
):
    """Test getting timeline events within a time range."""
    now = datetime.now(timezone.utc)
    start_time = (now - timedelta(minutes=5)).isoformat()
    end_time = (now + timedelta(minutes=5)).isoformat()

    response = await async_client.get(
        "/v1/timeline/in-timerange",
        params={
            "start_time": start_time,
            "end_time": end_time,
        },
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert len(data["items"]) > 0

    # Verify all events are within the time range
    for event in data["items"]:
        # Convert timestamp to datetime for comparison
        datetime.fromisoformat(
            event["timestamp"].replace("Z", "+00:00")
        )
        assert start_time <= event["timestamp"] <= end_time


@pytest.mark.asyncio
async def test_combined_type_and_time_filter(
    async_client: AsyncClient,
    sample_timeline_events,
    auth_headers,
):
    """Test combining type and time filters in a single query."""
    now = datetime.now(timezone.utc)
    start_time = (now - timedelta(minutes=5)).isoformat()
    end_time = (now + timedelta(minutes=5)).isoformat()

    response = await async_client.get(
        "/v1/timeline",
        params={
            "event_type": TimelineEventType.TASK_CREATED.value,
            "start_time": start_time,
            "end_time": end_time,
        },
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert all(
        item["event_type"]
        == TimelineEventType.TASK_CREATED.value
        for item in data["items"]
    )


@pytest.mark.asyncio
async def test_invalid_timerange(
    async_client: AsyncClient,
    auth_headers,
):
    """Test error handling for invalid time ranges."""
    now = datetime.now(timezone.utc)
    # End time before start time
    start_time = (now + timedelta(minutes=5)).isoformat()
    end_time = (now - timedelta(minutes=5)).isoformat()

    response = await async_client.get(
        "/v1/timeline/in-timerange",
        params={
            "start_time": start_time,
            "end_time": end_time,
        },
        headers=auth_headers,
    )

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    )
    error = response.json()
    assert "detail" in error
    assert (
        "Start time must be before end time"
        in error["detail"]["message"]
    )


@pytest.mark.asyncio
async def test_unauthorized_access(
    async_client: AsyncClient,
):
    """Test accessing timeline endpoints without authentication."""
    response = await async_client.get("/v1/timeline")

    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    )
    error = response.json()
    assert "detail" in error
    assert (
        "Invalid or missing authentication token"
        in error["detail"]["message"]
    )
