"""Test activity worker module."""

import pytest
from unittest.mock import MagicMock
from domain.exceptions import RoboServiceError
from domain.values import ProcessingStatus
from infrastructure.queue.activity_worker import (
    process_activity_job,
)


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_activity():
    """Create a mock activity."""
    activity = MagicMock()
    activity.id = 1
    activity.activity_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
        },
    }
    activity.enrichment_data = {}
    activity.processing_status = ProcessingStatus.PENDING
    return activity


@pytest.fixture
def mock_robo_service():
    """Create a mock RoboService."""
    service = MagicMock()
    service.analyze_activity_schema.return_value = {
        "render_type": "form",
        "layout": {
            "sections": [
                {
                    "title": "Basic Info",
                    "fields": ["title", "description"],
                }
            ],
            "suggestions": {
                "column_count": 1,
                "responsive_breakpoints": [768, 992],
            },
        },
    }
    return service


def test_process_activity_job_success(
    mock_activity, mock_robo_service, mock_session
):
    """Test successful activity job processing."""
    # Setup mock activity query
    mock_session.query.return_value.filter.return_value.first.return_value = (
        mock_activity
    )

    # Process the activity
    process_activity_job(
        activity_id=1,
        session=mock_session,
        robo_service=mock_robo_service,
    )

    # Verify activity was processed
    mock_robo_service.analyze_activity_schema.assert_called_once_with(
        mock_activity.activity_schema
    )
    assert (
        mock_activity.processing_status
        == ProcessingStatus.COMPLETED
    )


def test_process_activity_job_not_found(
    mock_robo_service, mock_session
):
    """Test activity job processing when activity not found."""
    # Setup mock to return None for activity query
    mock_session.query.return_value.filter.return_value.first.return_value = (
        None
    )

    # Process should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        process_activity_job(
            activity_id=1,
            session=mock_session,
            robo_service=mock_robo_service,
        )
    assert "Failed to process activity 1" in str(
        exc_info.value
    )


def test_process_activity_job_processing_error(
    mock_activity, mock_robo_service, mock_session
):
    """Test activity job processing with processing error."""
    # Setup mock activity query
    mock_session.query.return_value.filter.return_value.first.return_value = (
        mock_activity
    )

    # Setup mock to raise error
    mock_robo_service.analyze_activity_schema.side_effect = RoboServiceError(
        "Processing failed"
    )

    # Process should raise RoboServiceError
    with pytest.raises(RoboServiceError):
        process_activity_job(
            activity_id=1,
            session=mock_session,
            robo_service=mock_robo_service,
        )

    # Verify activity status was updated
    assert (
        mock_activity.processing_status
        == ProcessingStatus.FAILED
    )


def test_process_activity_job_retries(
    mock_activity, mock_robo_service, mock_session
):
    """Test activity job processing with retries."""
    # Setup mock activity query
    mock_session.query.return_value.filter.return_value.first.return_value = (
        mock_activity
    )

    # Setup mock to fail twice then succeed
    mock_robo_service.analyze_activity_schema.side_effect = [
        RoboServiceError("First failure"),
        RoboServiceError("Second failure"),
        {
            "render_type": "form",
            "layout": {"sections": []},
        },
    ]

    # Process the activity
    process_activity_job(
        activity_id=1,
        session=mock_session,
        robo_service=mock_robo_service,
        max_retries=3,
    )

    # Verify activity was processed after retries
    assert (
        mock_robo_service.analyze_activity_schema.call_count
        == 3
    )
    assert (
        mock_activity.processing_status
        == ProcessingStatus.COMPLETED
    )
