"""Test ActivityModel class."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from models.ActivityModel import Activity
from models.MomentModel import Moment
from models.UserModel import User


@pytest.fixture
def sample_user(test_db_session) -> User:
    """Create a sample user for testing."""
    user = User(
        username="testuser",
        key_id=str(uuid.uuid4()),
        user_secret="test-secret-hash",
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


def test_activity_model_initialization(
    sample_user: User,
) -> None:
    """Test that an activity can be created with valid data."""
    activity = Activity(
        name="Test Activity",
        description="Test Description",
        user_id=sample_user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
        },
        icon="📝",
        color="#FF0000",
    )

    assert activity.name == "Test Activity"
    assert activity.description == "Test Description"
    assert activity.user_id == sample_user.id
    assert activity.activity_schema == {
        "type": "object",
        "properties": {"notes": {"type": "string"}},
    }
    assert activity.icon == "📝"
    assert activity.color == "#FF0000"


def test_activity_model_db_persistence(
    test_db_session, sample_user: User
) -> None:
    """Test that an activity can be persisted to the database."""
    activity = Activity(
        name="Test Activity",
        description="Test Description",
        user_id=sample_user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity)
    test_db_session.commit()
    test_db_session.refresh(activity)

    saved_activity = (
        test_db_session.query(Activity)
        .filter(Activity.name == "Test Activity")
        .first()
    )

    assert saved_activity is not None
    assert saved_activity.name == "Test Activity"
    assert saved_activity.description == "Test Description"
    assert saved_activity.user_id == sample_user.id


def test_activity_moment_relationship(
    test_db_session, sample_user: User
) -> None:
    """Test the relationship between Activity and Moment models."""
    activity = Activity(
        name="Test Activity",
        description="Test Description",
        user_id=sample_user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity)
    test_db_session.commit()
    test_db_session.refresh(activity)

    moment = Moment(
        activity_id=activity.id,
        user_id=sample_user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)
    test_db_session.commit()
    test_db_session.refresh(moment)

    assert moment in activity.moments
    assert activity == moment.activity


def test_activity_name_unique_constraint(
    test_db_session, sample_user: User
) -> None:
    """Test that activity names must be unique per user."""
    activity1 = Activity(
        name="Test Activity",
        description="Test Description",
        user_id=sample_user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity1)
    test_db_session.commit()

    activity2 = Activity(
        name="Test Activity",  # Same name as activity1
        description="Another Description",
        user_id=sample_user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
        },
        icon="📝",
        color="#00FF00",
    )
    test_db_session.add(activity2)

    with pytest.raises(IntegrityError):
        test_db_session.commit()


def test_activity_required_fields(
    test_db_session, sample_user: User
) -> None:
    """Test that required fields raise appropriate errors when missing."""
    activity = Activity(
        description="Test Description",  # Missing name
        user_id=sample_user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity)

    with pytest.raises(IntegrityError):
        test_db_session.commit()


def test_activity_schema_validation(
    sample_user: User,
) -> None:
    """Test that activity_schema must be a valid JSON object."""
    with pytest.raises(ValueError):
        Activity(
            name="Test Activity",
            description="Test Description",
            user_id=sample_user.id,
            activity_schema="invalid json",  # Invalid schema
            icon="📝",
            color="#FF0000",
        )
