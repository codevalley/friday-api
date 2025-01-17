"""Tests for activity router endpoints."""

from datetime import datetime

import pytest

from domain.exceptions import (
    ActivityNotFoundError,
    ActivityServiceError,
)
from auth.bearer import CustomHTTPBearer
from dependencies import (
    get_current_user,
    get_activity_service,
)
from schemas.pydantic.ActivitySchema import (
    ActivityData,
    ActivityList,
    ActivityResponse,
)


@pytest.fixture(autouse=True)
def setup_dependencies(
    mock_activity_service,
    mock_auth_middleware,
    sample_user,
    fastapi_app,
):
    """Set up dependencies for all tests in this module."""
    fastapi_app.dependency_overrides[
        get_activity_service
    ] = lambda: mock_activity_service
    fastapi_app.dependency_overrides[get_current_user] = (
        lambda: sample_user
    )
    fastapi_app.dependency_overrides[CustomHTTPBearer] = (
        lambda: mock_auth_middleware
    )
    yield
    fastapi_app.dependency_overrides = {}


@pytest.fixture
def auth_headers():
    """Get authorization headers for test requests."""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def sample_activity_data():
    """Sample activity data for tests."""
    return {
        "name": "Test Activity",
        "description": "Test Description",
        "activity_schema": {
            "type": "object",
            "properties": {"test": {"type": "string"}},
        },
        "icon": "📝",
        "color": "#FF0000",
    }


@pytest.mark.asyncio
async def test_create_activity_queues_for_processing(
    test_client,
    mock_activity_service,
    auth_headers,
    sample_activity_data,
):
    """Test creating activity queues it for processing."""
    # Setup
    created_activity = {
        **sample_activity_data,
        "id": 1,
        "user_id": "test-user",
        "processing_status": "pending",
        "created_at": datetime.now(),
    }
    mock_activity_service.create_activity.return_value = (
        created_activity
    )

    # Execute
    response = test_client.post(
        "/v1/activities",
        headers=auth_headers,
        json=sample_activity_data,
    )

    # Assert
    assert response.status_code == 201
    response_data = response.json()["data"]
    assert response_data["processing_status"] == "pending"
    assert response_data["schema_render"] is None
    assert response_data["processed_at"] is None


@pytest.mark.asyncio
async def test_get_activity_includes_processing_status(
    test_client,
    mock_activity_service,
    auth_headers,
    sample_activity_data,
):
    """Test getting activity includes processing status."""
    # Setup
    activity_id = 1
    activity_data = {
        **sample_activity_data,
        "id": activity_id,
        "user_id": "test-user",
        "processing_status": "completed",
        "schema_render": {"type": "form"},
        "processed_at": datetime.now(),
        "created_at": datetime.now(),
    }
    mock_activity_service.get_activity.return_value = (
        activity_data
    )

    # Execute
    response = test_client.get(
        f"/v1/activities/{activity_id}",
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == 200
    response_data = response.json()["data"]
    assert response_data["processing_status"] == "completed"
    assert response_data["schema_render"] == {
        "type": "form"
    }
    assert "processed_at" in response_data


@pytest.mark.asyncio
async def test_list_activities_includes_processing_status(
    test_client,
    mock_activity_service,
    auth_headers,
    sample_activity_data,
):
    """Test listing activities includes processing status."""
    # Setup
    activities = [
        ActivityData(
            **sample_activity_data,
            id=1,
            user_id="test-user",
            processing_status="completed",
            schema_render={"type": "form"},
            processed_at=datetime.now(),
            created_at=datetime.now(),
        ),
        ActivityData(
            **sample_activity_data,
            id=2,
            user_id="test-user",
            processing_status="pending",
            schema_render=None,
            processed_at=None,
            created_at=datetime.now(),
        ),
    ]
    mock_activity_service.list_activities.return_value = (
        ActivityList(
            items=[
                ActivityResponse.from_domain(a)
                for a in activities
            ],
            total=len(activities),
            page=1,
            size=10,
            pages=1,
        )
    )

    # Execute
    response = test_client.get(
        "/v1/activities",
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == 200
    response_data = response.json()["data"]
    assert len(response_data["items"]) == 2
    assert (
        response_data["items"][0]["processing_status"]
        == "completed"
    )
    assert response_data["items"][0]["schema_render"] == {
        "type": "form"
    }
    assert (
        response_data["items"][1]["processing_status"]
        == "pending"
    )
    assert (
        response_data["items"][1]["schema_render"] is None
    )


@pytest.mark.asyncio
async def test_get_processing_status_success(
    test_client,
    mock_activity_service,
    auth_headers,
    sample_user,
):
    """Test get processing status for an activity."""
    # Setup
    activity_id = 1
    mock_activity_service.get_processing_status.return_value = {
        "status": "completed",
        "processed_at": datetime.now(),
        "schema_render": {"type": "form"},
    }

    # Execute
    response = test_client.get(
        f"/v1/activities/{activity_id}/processing-status",
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "completed"
    assert "processed_at" in response.json()["data"]
    assert "schema_render" in response.json()["data"]
    mock_activity_service.get_processing_status.assert_called_once_with(
        activity_id, sample_user.id
    )


@pytest.mark.asyncio
async def test_get_processing_status_not_found(
    test_client,
    mock_activity_service,
    auth_headers,
    sample_user,
):
    """Test get processing status for non-existent activity."""
    # Setup
    activity_id = 999
    error = ActivityNotFoundError(
        message="Activity not found",
        code="ACTIVITY_NOT_FOUND",
    )
    mock_activity_service.get_processing_status.side_effect = (
        error
    )

    # Execute
    response = test_client.get(
        f"/v1/activities/{activity_id}/processing-status",
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == 404
    mock_activity_service.get_processing_status.assert_called_once_with(
        activity_id, sample_user.id
    )


@pytest.mark.asyncio
async def test_retry_processing_success(
    test_client,
    mock_activity_service,
    auth_headers,
    sample_user,
):
    """Test retry processing for a failed activity."""
    # Setup
    activity_id = 1
    mock_activity_service.retry_processing.return_value = (
        "job-123"
    )

    # Execute
    response = test_client.post(
        f"/v1/activities/{activity_id}/retry-processing",
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["data"]["job_id"] == "job-123"
    mock_activity_service.retry_processing.assert_called_once_with(
        activity_id, sample_user.id
    )


@pytest.mark.asyncio
async def test_retry_processing_not_failed(
    test_client,
    mock_activity_service,
    auth_headers,
    sample_user,
):
    """Test retry processing for non-failed activity."""
    # Setup
    activity_id = 1
    error = ActivityServiceError(
        message="Activity is not in FAILED state",
        code="INVALID_ACTIVITY_STATE",
    )
    mock_activity_service.retry_processing.side_effect = (
        error
    )

    # Execute
    response = test_client.post(
        f"/v1/activities/{activity_id}/retry-processing",
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == 400
    mock_activity_service.retry_processing.assert_called_once_with(
        activity_id, sample_user.id
    )
