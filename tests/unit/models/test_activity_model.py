"""Test ActivityModel class."""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from orm.ActivityModel import Activity
from orm.UserModel import User
from orm.MomentModel import Moment


@pytest.fixture
def test_user(test_db_session: Session) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        key_id="test-key-id",
        user_secret="test-secret",
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def test_activity(
    test_db_session: Session, test_user: User
) -> Activity:
    """Create a test activity."""
    activity = Activity(
        user_id=test_user.id,
        name="Test Activity",
        description="Test Description",
        activity_schema={
            "type": "object",
            "properties": {},
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity)
    test_db_session.commit()
    return activity


def test_activity_initialization():
    """Test basic activity model initialization."""
    activity = Activity(
        user_id="test-user-id",
        name="Test Activity",
        description="Test Description",
        activity_schema={
            "type": "object",
            "properties": {},
        },
        icon="📝",
        color="#FF0000",
    )

    assert activity.name == "Test Activity"
    assert activity.description == "Test Description"
    assert activity.icon == "📝"
    assert activity.color == "#FF0000"
    assert activity.activity_schema == {
        "type": "object",
        "properties": {},
    }


def test_activity_database_persistence(
    test_db_session: Session, test_user: User
):
    """Test activity persistence in database."""
    activity = Activity(
        user_id=test_user.id,
        name="Test Activity",
        description="Test Description",
        activity_schema={
            "type": "object",
            "properties": {},
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity)
    test_db_session.commit()
    test_db_session.refresh(activity)

    saved_activity = (
        test_db_session.query(Activity)
        .filter(Activity.id == activity.id)
        .first()
    )
    assert saved_activity is not None
    assert saved_activity.name == "Test Activity"
    assert saved_activity.user_id == test_user.id
    assert isinstance(saved_activity.created_at, datetime)
    assert saved_activity.updated_at is None


def test_activity_relationships(
    test_db_session: Session, test_activity: Activity
):
    """Test activity relationships with user and moments."""
    # Test user relationship
    assert test_activity.user is not None
    assert test_activity.user.username == "testuser"

    # Test moments relationship
    moment = Moment(
        user_id=test_activity.user_id,
        activity_id=test_activity.id,
        data={"test": "data"},
        timestamp=datetime.utcnow(),
    )
    test_db_session.add(moment)
    test_db_session.commit()

    assert len(test_activity.moments) == 1
    assert test_activity.moments[0].data == {"test": "data"}
    assert test_activity.moment_count == 1


def test_activity_constraints(
    test_db_session: Session, test_user: User
):
    """Test activity model constraints."""
    # Test name uniqueness per user
    activity1 = Activity(
        user_id=test_user.id,
        name="Same Name",
        description="First Activity",
        activity_schema={
            "type": "object",
            "properties": {},
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity1)
    test_db_session.commit()

    # Try to create another activity with the same name for the same user
    with pytest.raises(IntegrityError):
        activity2 = Activity(
            user_id=test_user.id,
            name="Same Name",
            description="Second Activity",
            activity_schema={
                "type": "object",
                "properties": {},
            },
            icon="📝",
            color="#00FF00",
        )
        test_db_session.add(activity2)
        test_db_session.commit()


def test_activity_schema_validation(
    test_db_session: Session, test_user: User
):
    """Test activity schema validation."""
    # Test valid schema
    valid_schema = {
        "type": "object",
        "properties": {
            "field1": {"type": "string"},
            "field2": {"type": "number"},
        },
        "required": ["field1"],
    }

    activity = Activity(
        user_id=test_user.id,
        name="Schema Test",
        description="Testing Schema",
        activity_schema=valid_schema,
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity)
    test_db_session.commit()

    assert activity.activity_schema == valid_schema


def test_color_validation(
    test_db_session: Session, test_user: User
):
    """Test color validation."""
    # Test valid colors
    valid_colors = [
        "#FF0000",
        "#00FF00",
        "#0000FF",
        "#123456",
    ]

    for color in valid_colors:
        activity = Activity(
            user_id=test_user.id,
            name=f"Color Test {color}",
            description="Testing Color",
            activity_schema={
                "type": "object",
                "properties": {},
            },
            icon="📝",
            color=color,
        )
        test_db_session.add(activity)
        test_db_session.commit()
        assert activity.color == color

    # Test invalid color format
    with pytest.raises(ValueError):
        Activity(
            user_id=test_user.id,
            name="Invalid Color",
            description="Testing Invalid Color",
            activity_schema={
                "type": "object",
                "properties": {},
            },
            icon="📝",
            color="invalid-color",
        )


def test_cascade_deletion(
    test_db_session: Session, test_activity: Activity
):
    """Test cascade deletion of moments when activity is deleted."""
    # Create some moments
    for i in range(3):
        moment = Moment(
            user_id=test_activity.user_id,
            activity_id=test_activity.id,
            data={"test": f"data{i}"},
            timestamp=datetime.utcnow(),
        )
        test_db_session.add(moment)
    test_db_session.commit()

    # Verify moments exist
    assert test_activity.moment_count == 3

    # Delete activity
    test_db_session.delete(test_activity)
    test_db_session.commit()

    # Verify moments were deleted
    moments = (
        test_db_session.query(Moment)
        .filter(Moment.activity_id == test_activity.id)
        .all()
    )
    assert len(moments) == 0
