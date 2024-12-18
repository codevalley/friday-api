"""Test UserModel class."""

import uuid
from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from orm.UserModel import User
from orm.ActivityModel import Activity
from orm.MomentModel import Moment


def test_user_model_initialization() -> None:
    """Test that a user can be created with valid data."""
    user = User(
        username="testuser",
        key_id=str(uuid.uuid4()),
        user_secret="test-secret-hash",
    )

    assert user.username == "testuser"
    assert user.key_id is not None
    assert user.user_secret == "test-secret-hash"
    assert (
        user.id is not None
    )  # UUID should be auto-generated


def test_user_model_db_persistence(test_db_session) -> None:
    """Test that a user can be persisted to the database."""
    user = User(
        username="testuser",
        key_id=str(uuid.uuid4()),
        user_secret="test-secret-hash",
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    saved_user = (
        test_db_session.query(User)
        .filter(User.username == "testuser")
        .first()
    )

    assert saved_user is not None
    assert saved_user.username == "testuser"
    assert saved_user.key_id == user.key_id
    assert saved_user.user_secret == "test-secret-hash"
    assert isinstance(saved_user.created_at, datetime)
    assert isinstance(saved_user.updated_at, datetime)


def test_user_username_validation() -> None:
    """Test username validation rules."""
    # Test valid usernames
    valid_usernames = [
        "user123",
        "test_user",
        "test-user",
        "TestUser",
        "user_123_test",
    ]
    for username in valid_usernames:
        User.validate_username(username)

    # Test invalid usernames
    invalid_usernames = [
        None,  # None value
        "ab",  # Too short
        "user@123",  # Invalid character @
        "user 123",  # Space not allowed
        "user#123",  # Special character not allowed
        "user.123",  # Dot not allowed
    ]
    for username in invalid_usernames:
        with pytest.raises(ValueError):
            User.validate_username(username)


def test_user_unique_constraints(test_db_session) -> None:
    """Test that username and key_id must be unique."""
    # Create first user
    user1 = User(
        username="testuser1",
        key_id="key1",
        user_secret="secret1",
    )
    test_db_session.add(user1)
    test_db_session.commit()

    # Try to create user with same username
    with pytest.raises(IntegrityError):
        user2 = User(
            username="testuser1",  # Same username
            key_id="key2",
            user_secret="secret2",
        )
        test_db_session.add(user2)
        test_db_session.commit()

    test_db_session.rollback()

    # Try to create user with same key_id
    with pytest.raises(IntegrityError):
        user3 = User(
            username="testuser2",
            key_id="key1",  # Same key_id
            user_secret="secret3",
        )
        test_db_session.add(user3)
        test_db_session.commit()


def test_user_required_fields(test_db_session) -> None:
    """Test that required fields raise appropriate errors when missing."""
    # Test missing username
    with pytest.raises(ValueError):
        User(
            key_id=str(uuid.uuid4()),
            user_secret="test-secret",
        )

    # Test missing key_id
    with pytest.raises(IntegrityError):
        user = User(
            username="testuser",
            user_secret="test-secret",
        )
        test_db_session.add(user)
        test_db_session.commit()

    test_db_session.rollback()

    # Test missing user_secret
    with pytest.raises(IntegrityError):
        user = User(
            username="testuser",
            key_id=str(uuid.uuid4()),
        )
        test_db_session.add(user)
        test_db_session.commit()


def test_user_relationships(test_db_session) -> None:
    """Test relationships between User, Activity, and Moment models."""
    # Create user
    user = User(
        username="testuser",
        key_id=str(uuid.uuid4()),
        user_secret="test-secret-hash",
    )
    test_db_session.add(user)
    test_db_session.commit()

    # Create activity
    activity = Activity(
        name="Test Activity",
        description="Test Description",
        user_id=user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
            "required": ["notes"],
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity)
    test_db_session.commit()

    # Create moment
    moment = Moment(
        activity_id=activity.id,
        user_id=user.id,
        data={"notes": "Test moment"},
    )
    test_db_session.add(moment)
    test_db_session.commit()

    # Test relationships
    assert activity in user.activities
    assert moment in user.moments
    assert user.activity_count() == 1
    assert user.moment_count() == 1

    # Test cascade delete
    test_db_session.delete(user)
    test_db_session.commit()

    # Verify everything is deleted
    assert (
        test_db_session.query(Activity)
        .filter(Activity.id == activity.id)
        .first()
        is None
    )
    assert (
        test_db_session.query(Moment)
        .filter(Moment.id == moment.id)
        .first()
        is None
    )


def test_user_string_representation() -> None:
    """Test the string representation of the User model."""
    user = User(
        username="testuser",
        key_id=str(uuid.uuid4()),
        user_secret="test-secret-hash",
    )
    assert str(user) == f"<User {user.id} (testuser)>"
