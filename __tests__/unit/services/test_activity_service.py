"""Tests for ActivityService."""

import pytest
from unittest.mock import Mock
from datetime import datetime, UTC

from domain.activity import ActivityData
from domain.exceptions import ActivityServiceError
from services.ActivityService import ActivityService


@pytest.fixture
def mock_repository():
    """Create mock activity repository."""
    return Mock()


@pytest.fixture
def mock_queue_service():
    """Create mock queue service."""
    return Mock()


@pytest.fixture
def service(mock_repository, mock_queue_service):
    """Create ActivityService instance with mocks."""
    return ActivityService(
        repository=mock_repository,
        queue_service=mock_queue_service,
    )


@pytest.fixture
def sample_user_id():
    """Get sample user ID for tests."""
    return "test-user-id"


@pytest.fixture
def sample_activity_data():
    """Get sample activity data for tests."""
    return ActivityData(
        name="Test Activity",
        description="Test Description",
        activity_schema={
            "type": "object",
            "properties": {},
        },
        icon="test-icon",
        color="#000000",
        user_id="test-user-id",
    )


def test_create_activity_success(
    service,
    mock_repository,
    mock_queue_service,
    sample_activity_data,
    sample_user_id,
):
    """Test successful activity creation."""
    # Setup
    mock_repository.create.return_value = (
        sample_activity_data
    )
    mock_queue_service.enqueue_activity.return_value = (
        "job-123"
    )

    # Execute
    result = service.create_activity(
        sample_activity_data,
        user_id=sample_user_id,
    )

    # Assert
    assert result == sample_activity_data
    mock_repository.create.assert_called_once()
    mock_queue_service.enqueue_activity.assert_called_once()


def test_create_activity_queue_failure(
    service,
    mock_repository,
    mock_queue_service,
    sample_activity_data,
    sample_user_id,
):
    """Test activity creation with queue failure."""
    # Setup
    mock_repository.create.return_value = (
        sample_activity_data
    )
    mock_queue_service.enqueue_activity.return_value = None

    # Execute and Assert
    with pytest.raises(ActivityServiceError) as exc_info:
        service.create_activity(
            sample_activity_data,
            user_id=sample_user_id,
        )

    assert "Failed to queue activity" in str(exc_info.value)
    mock_repository.create.assert_called_once()
    mock_queue_service.enqueue_activity.assert_called_once()


def test_get_processing_status(service, mock_repository):
    """Test getting activity processing status."""
    # Setup
    activity = ActivityData(
        name="Test Activity",
        description="Test Description",
        activity_schema={"type": "object"},
        icon="📝",
        color="#FF0000",
        user_id="test-user",
        processing_status="COMPLETED",
        processed_at=datetime.now(UTC),
        schema_render={"render_type": "form"},
    )
    mock_repository.get_by_id.return_value = activity

    # Execute
    status = service.get_processing_status(1)

    # Verify
    assert status["status"] == "COMPLETED"
    assert status["schema_render"] == {
        "render_type": "form"
    }
    assert status["processed_at"] == activity.processed_at


def test_retry_processing_success(
    service, mock_repository, mock_queue_service
):
    """Test successful retry of failed processing."""
    # Setup
    activity = ActivityData(
        name="Test Activity",
        description="Test Description",
        activity_schema={"type": "object"},
        icon="📝",
        color="#FF0000",
        user_id="test-user",
        processing_status="FAILED",
    )
    mock_repository.get_by_id.return_value = activity
    mock_queue_service.enqueue_activity.return_value = (
        "job-123"
    )

    # Execute
    job_id = service.retry_processing(1)

    # Verify
    assert job_id == "job-123"
    assert activity.processing_status == "PENDING"
    mock_repository.update.assert_called_once()
    mock_queue_service.enqueue_activity.assert_called_once_with(
        1
    )
