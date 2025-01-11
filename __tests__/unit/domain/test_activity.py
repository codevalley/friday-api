"""Tests for Activity domain model."""

import pytest
from datetime import datetime, UTC
from domain.activity import ActivityData
from domain.exceptions import ActivityValidationError


def test_activity_data_with_processing_fields():
    """Test ActivityData with processing status fields."""
    now = datetime.now(UTC)
    activity = ActivityData(
        name="Test Activity",
        description="Test Description",
        activity_schema={
            "type": "object",
            "properties": {},
        },
        icon="📝",
        color="#FF0000",
        user_id="test-user",
        processing_status="completed",
        schema_render={"render_type": "form"},
        processed_at=now,
    )

    assert activity.processing_status == "completed"
    assert activity.schema_render == {"render_type": "form"}
    assert activity.processed_at == now


def test_activity_data_default_processing_status():
    """Test default processing status."""
    activity = ActivityData(
        name="Test Activity",
        description="Test Description",
        activity_schema={
            "type": "object",
            "properties": {},
        },
        icon="📝",
        color="#FF0000",
        user_id="test-user",
    )

    assert activity.processing_status == "not_processed"
    assert activity.schema_render is None
    assert activity.processed_at is None


def test_activity_data_invalid_processing_status():
    """Test invalid processing status validation."""
    with pytest.raises(ActivityValidationError) as exc:
        ActivityData(
            name="Test Activity",
            description="Test Description",
            activity_schema={
                "type": "object",
                "properties": {},
            },
            icon="📝",
            color="#FF0000",
            user_id="test-user",
            processing_status="invalid_status",
        )

    assert "processing_status must be one of" in str(
        exc.value
    )


def test_activity_data_completed_without_render():
    """Test completed status requires schema_render."""
    with pytest.raises(ActivityValidationError) as exc:
        ActivityData(
            name="Test Activity",
            description="Test Description",
            activity_schema={
                "type": "object",
                "properties": {},
            },
            icon="📝",
            color="#FF0000",
            user_id="test-user",
            processing_status="completed",
            processed_at=datetime.now(UTC),
        )

    assert (
        "schema_render must be set when status is COMPLETED"
        in str(exc.value)
    )


def test_activity_data_completed_without_processed_at():
    """Test completed status requires processed_at."""
    with pytest.raises(ActivityValidationError) as exc:
        ActivityData(
            name="Test Activity",
            description="Test Description",
            activity_schema={
                "type": "object",
                "properties": {},
            },
            icon="📝",
            color="#FF0000",
            user_id="test-user",
            processing_status="completed",
            schema_render={"render_type": "form"},
        )

    assert (
        "processed_at must be set when status is COMPLETED"
        in str(exc.value)
    )


def test_activity_data_serialization():
    """Test serialization with processing fields."""
    now = datetime.now(UTC)
    activity = ActivityData(
        name="Test Activity",
        description="Test Description",
        activity_schema={
            "type": "object",
            "properties": {},
        },
        icon="📝",
        color="#FF0000",
        user_id="test-user",
        processing_status="completed",
        schema_render={"render_type": "form"},
        processed_at=now,
    )

    data = activity.to_dict()
    assert data["processing_status"] == "completed"
    assert data["schema_render"] == {"render_type": "form"}
    assert data["processed_at"] == now

    # Test deserialization
    new_activity = ActivityData.from_dict(data)
    assert (
        new_activity.processing_status
        == activity.processing_status
    )
    assert (
        new_activity.schema_render == activity.schema_render
    )
    assert (
        new_activity.processed_at == activity.processed_at
    )
