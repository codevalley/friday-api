"""Integration tests for activity schema rendering."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from schemas.pydantic.ActivitySchema import ActivityCreate
from repositories.ActivityRepository import (
    ActivityRepository,
)
from infrastructure.queue.activity_worker import (
    process_activity_job,
)
from domain.exceptions import RoboAPIError
from domain.values import ProcessingStatus


@pytest.fixture
def robo_service():
    """Get robo service for testing."""
    mock_service = Mock()
    mock_service.analyze_activity_schema.return_value = {
        "render_type": "form",
        "layout": {
            "sections": [
                {
                    "title": "Basic Info",
                    "fields": ["field1"],
                }
            ],
        },
        "field_groups": [
            {
                "name": "basic",
                "fields": ["field1"],
                "description": "Basic fields",
            }
        ],
    }
    return mock_service


@pytest.mark.integration
def test_activity_schema_success(
    test_db_session,
    activity_service,
    queue_service,
    sample_user,
    robo_service,
):
    """Test successful activity schema processing flow."""
    # Create activity
    activity_data = ActivityCreate(
        name="Test Activity",
        description="Test Description",
        activity_schema={
            "type": "object",
            "properties": {
                "field1": {"type": "string"},
                "field2": {"type": "number"},
            },
        },
        icon="📝",
        color="#FF0000",
    )
    activity_response = activity_service.create_activity(
        activity_data, sample_user.id
    )

    # Get the actual activity model from repository
    activity_repo = ActivityRepository(test_db_session)
    activity = activity_repo.get(activity_response.id)

    # Process activity
    process_activity_job(
        activity.id,
        session=test_db_session,
        robo_service=robo_service,
    )

    # Refresh session to see worker's changes
    test_db_session.expire_all()
    test_db_session.refresh(activity)

    # Verify final state
    assert (
        activity.processing_status
        == ProcessingStatus.COMPLETED
    )
    assert activity.schema_render is not None
    assert "render_type" in activity.schema_render
    assert "layout" in activity.schema_render
    assert "field_groups" in activity.schema_render
    assert isinstance(activity.processed_at, datetime)


@pytest.mark.integration
def test_activity_schema_failure(
    test_db_session,
    activity_service,
    queue_service,
    sample_user,
    robo_service,
):
    """Test activity schema processing failure handling."""
    # Create activity
    activity_data = ActivityCreate(
        name="Test Activity Failure",
        description="Test Description",
        activity_schema={
            "type": "object",
            "properties": {
                "field1": {"type": "string"},
            },
        },
        icon="📝",
        color="#FF0000",
    )
    activity_response = activity_service.create_activity(
        activity_data, sample_user.id
    )

    # Get the actual activity model from repository
    activity_repo = ActivityRepository(test_db_session)
    activity = activity_repo.get(activity_response.id)

    # Mock RoboService to raise an error
    robo_service.analyze_activity_schema.side_effect = (
        RoboAPIError("Test processing failure")
    )

    # Process activity
    process_activity_job(
        activity.id,
        session=test_db_session,
        robo_service=robo_service,
    )

    # Refresh session to see worker's changes
    test_db_session.expire_all()
    test_db_session.refresh(activity)

    # Verify final state
    assert (
        activity.processing_status
        == ProcessingStatus.FAILED
    )
    assert activity.schema_render is None
    assert activity.processed_at is None


@pytest.mark.integration
def test_activity_schema_retry(
    test_db_session,
    activity_service,
    queue_service,
    sample_user,
    robo_service,
):
    """Test activity schema processing retry mechanism."""
    # Create activity
    activity_data = ActivityCreate(
        name="Test Activity Retry",
        description="Test Description",
        activity_schema={
            "type": "object",
            "properties": {
                "field1": {"type": "string"},
            },
        },
        icon="📝",
        color="#FF0000",
    )
    activity_response = activity_service.create_activity(
        activity_data, sample_user.id
    )

    # Get the actual activity model from repository
    activity_repo = ActivityRepository(test_db_session)
    activity = activity_repo.get(activity_response.id)

    # Mock RoboService to fail twice then succeed
    attempts = 0

    def mock_analyze_schema(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts <= 2:
            raise RoboAPIError(
                f"Test failure attempt {attempts}"
            )
        return {
            "render_type": "form",
            "layout": {
                "sections": [
                    {
                        "title": "Basic Info",
                        "fields": ["field1"],
                    }
                ],
            },
            "field_groups": [
                {
                    "name": "basic",
                    "fields": ["field1"],
                    "description": "Basic fields",
                }
            ],
            "metadata": {
                "attempts": attempts,
            },
        }

    robo_service.analyze_activity_schema.side_effect = (
        mock_analyze_schema
    )

    # Process activity
    process_activity_job(
        activity.id,
        session=test_db_session,
        robo_service=robo_service,
    )

    # Refresh session to see worker's changes
    test_db_session.expire_all()
    test_db_session.refresh(activity)

    # Verify final state
    assert (
        activity.processing_status
        == ProcessingStatus.COMPLETED
    )
    assert activity.schema_render is not None
    assert activity.schema_render["render_type"] == "form"
    assert (
        activity.schema_render["metadata"]["attempts"] == 3
    )
    assert isinstance(activity.processed_at, datetime)
