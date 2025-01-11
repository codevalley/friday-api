"""Unit tests for ActivityService."""

import pytest
from unittest.mock import Mock
from services.ActivityService import ActivityService
from domain.activity import ActivityData
from domain.activity import ProcessingStatus
from datetime import datetime, UTC


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
        processing_status="not_processed",
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
    mock_repository, mock_queue_service
):
    """Test activity creation with queue failure."""
    # Setup
    mock_activity = Mock()
    mock_activity.id = 1
    mock_activity.name = "Test Activity"
    mock_activity.description = "Test Description"
    mock_activity.activity_schema = {
        "type": "object",
        "properties": {"test": {"type": "string"}},
    }
    mock_activity.icon = "📝"
    mock_activity.color = "#FF0000"
    mock_activity.user_id = "user123"
    mock_activity.processing_status = (
        ProcessingStatus.PENDING.value
    )
    mock_activity.moments = []
    mock_activity.moment_count = 0
    mock_activity.created_at = datetime.now(UTC)
    mock_activity.updated_at = datetime.now(UTC)
    mock_activity.processed_at = None
    mock_activity.__str__ = Mock(
        return_value="Test Activity"
    )
    mock_activity.to_domain.return_value = mock_activity

    mock_repository.create.return_value = mock_activity

    # Create a new mock for the updated activity
    updated_activity = Mock()
    updated_activity.id = 1
    updated_activity.name = "Test Activity"
    updated_activity.description = "Test Description"
    updated_activity.activity_schema = {
        "type": "object",
        "properties": {"test": {"type": "string"}},
    }
    updated_activity.icon = "📝"
    updated_activity.color = "#FF0000"
    updated_activity.user_id = "user123"
    updated_activity.processing_status = (
        ProcessingStatus.FAILED.value
    )
    updated_activity.moments = []
    updated_activity.moment_count = 0
    updated_activity.created_at = datetime.now(UTC)
    updated_activity.updated_at = datetime.now(UTC)
    updated_activity.processed_at = None
    updated_activity.__str__ = Mock(
        return_value="Test Activity"
    )

    mock_repository.update.return_value = updated_activity
    mock_queue_service.enqueue_activity.return_value = None

    # Execute
    service = ActivityService(
        mock_repository, mock_queue_service
    )
    result = service.create_activity(
        mock_activity, "user123"
    )

    # Assert
    mock_repository.update.assert_called_once_with(
        1,
        {
            "processing_status": ProcessingStatus.FAILED.value
        },
    )
    assert result.name == mock_activity.name
    assert result.description == mock_activity.description
    assert (
        result.activity_schema
        == mock_activity.activity_schema
    )
    assert result.icon == mock_activity.icon
    assert result.color == mock_activity.color
    assert result.user_id == mock_activity.user_id
    assert (
        result.processing_status
        == ProcessingStatus.FAILED.value
    )


def test_get_processing_status(
    mock_repository, mock_queue_service, sample_user_id
):
    """Test get processing status."""
    # Setup
    mock_activity = Mock()
    mock_activity.processing_status = "COMPLETED"
    mock_repository.get_by_id.return_value = mock_activity

    # Execute
    service = ActivityService(
        mock_repository, mock_queue_service
    )
    status = service.get_processing_status(
        1, sample_user_id
    )

    # Verify
    assert status["status"] == "COMPLETED"
    mock_repository.get_by_id.assert_called_once_with(
        1, sample_user_id
    )


def test_retry_processing_success(
    mock_repository, mock_queue_service, sample_user_id
):
    """Test retry processing success."""
    # Setup
    mock_activity = Mock()
    mock_activity.processing_status = "FAILED"
    mock_repository.get_by_id.return_value = mock_activity
    mock_queue_service.enqueue_activity.return_value = (
        "job123"
    )

    # Execute
    service = ActivityService(
        mock_repository, mock_queue_service
    )
    result = service.retry_processing(1, sample_user_id)

    # Verify
    assert result == "job123"
    mock_repository.get_by_id.assert_called_once_with(
        1, sample_user_id
    )
    mock_repository.update.assert_called_once_with(
        1, {"processing_status": "PENDING"}
    )
    mock_queue_service.enqueue_activity.assert_called_once_with(
        1
    )
