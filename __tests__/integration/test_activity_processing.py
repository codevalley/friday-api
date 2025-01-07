"""Integration tests for activity processing."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from orm.ActivityModel import Activity
from services.ActivityService import ActivityService
from domain.ports.QueueService import QueueService
from domain.activity import ActivityData
from domain.exceptions import ActivityValidationError

@pytest.fixture
def activity_service(db_session: Session, queue_service: QueueService) -> ActivityService:
    """Fixture for ActivityService with database session and queue service."""
    return ActivityService(db=db_session, queue_service=queue_service)

def test_create_and_process_activity(activity_service: ActivityService, db_session: Session):
    """Test end-to-end activity creation and processing."""
    activity_data = ActivityData(
        name="Test Activity",
        description="Test Description",
        activity_schema={
            "type": "object",
            "properties": {
                "field1": {"type": "string"},
                "field2": {"type": "number"},
            },
            "required": ["field1"],
        },
        icon="📝",
        color="#FF0000",
        user_id="test-user-id",
    )

    # Create activity
    created_activity = activity_service.create_activity(activity_data, user_id="test-user-id")
    assert created_activity is not None
    assert created_activity.name == "Test Activity"
    assert created_activity.processing_status == "PENDING"

    # Simulate processing
    activity = db_session.query(Activity).filter(Activity.id == created_activity.id).first()
    assert activity is not None
    activity.processing_status = "COMPLETED"
    activity.schema_render = {"rendered": "schema"}
    activity.processed_at = datetime(2023, 1, 1, tzinfo=timezone.utc)
    db_session.commit()

    # Verify processed activity
    processed_activity = activity_service.get_activity(activity.id, user_id="test-user-id")
    assert processed_activity is not None
    assert processed_activity.processing_status == "COMPLETED"
    assert processed_activity.schema_render == {"rendered": "schema"}
    assert processed_activity.processed_at == datetime(2023, 1, 1, tzinfo=timezone.utc)

def test_activity_processing_error_handling(activity_service: ActivityService, db_session: Session):
    """Test error handling during activity processing."""
    activity_data = ActivityData(
        name="Invalid Activity",
        description="Invalid Description",
        activity_schema="invalid schema",  # Invalid schema
        icon="📝",
        color="#FF0000",
        user_id="test-user-id",
    )

    with pytest.raises(ActivityValidationError):
        activity_service.create_activity(activity_data, user_id="test-user-id")

    # Verify no activity was created
    activities = db_session.query(Activity).filter(Activity.user_id == "test-user-id").all()
    assert len(activities) == 0
