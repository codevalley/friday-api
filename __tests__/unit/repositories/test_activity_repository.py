from orm.ActivityModel import Activity
from orm.UserModel import User
from repositories.ActivityRepository import (
    ActivityRepository,
)
import sys
import os
import pytest
from fastapi import HTTPException

sys.path.append(
    os.path.join(os.path.dirname(__file__), "../..")
)


@pytest.fixture
def activity_repository(test_db_session):
    """Create ActivityRepository instance with test database"""
    return ActivityRepository(test_db_session)


@pytest.fixture
def test_user(test_db_session):
    """Create a test user for activity tests"""
    user = User(
        username="testuser",
        key_id="test-key",
        user_secret="test-secret",
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def sample_activity_data(test_user):
    """Sample activity data for testing"""
    return {
        "name": "Test Activity",
        "description": "Test Description",
        "activity_schema": {"type": "test"},
        "icon": "test-icon",
        "color": "#000000",
        "user_id": test_user.id,
    }


def test_create_with_instance(
    activity_repository, sample_activity_data
):
    """Test creating activity with Activity instance"""
    activity = Activity(**sample_activity_data)
    created = activity_repository.create(activity)
    assert created.id is not None
    assert created.name == sample_activity_data["name"]
    assert (
        created.user_id == sample_activity_data["user_id"]
    )


def test_create_with_fields(
    activity_repository, sample_activity_data
):
    """Test creating activity with individual fields"""
    created = activity_repository.create(
        sample_activity_data["name"],
        description=sample_activity_data["description"],
        activity_schema=sample_activity_data[
            "activity_schema"
        ],
        icon=sample_activity_data["icon"],
        color=sample_activity_data["color"],
        user_id=sample_activity_data["user_id"],
    )
    assert created.id is not None
    assert created.name == sample_activity_data["name"]
    assert (
        created.user_id == sample_activity_data["user_id"]
    )


def test_create_missing_user_id(activity_repository):
    """Test error when creating activity without user_id"""
    with pytest.raises(ValueError) as exc_info:
        activity_repository.create("Test Activity")
    assert "user_id is required" in str(exc_info.value)


def test_create_invalid_color(
    activity_repository, sample_activity_data
):
    """Test error when creating activity with invalid color format"""
    invalid_data = sample_activity_data.copy()
    invalid_data["color"] = "invalid-color"
    with pytest.raises(ValueError) as exc_info:
        activity_repository.create(Activity(**invalid_data))
    assert "Color must be a valid hex code" in str(
        exc_info.value
    )


def test_create_invalid_schema(
    activity_repository, sample_activity_data
):
    """Test error when creating activity with invalid schema"""
    invalid_data = sample_activity_data.copy()
    invalid_data["activity_schema"] = "not-a-dict"
    with pytest.raises(ValueError):
        activity_repository.create(Activity(**invalid_data))


def test_get_by_user_existing(
    activity_repository, sample_activity_data
):
    """Test getting activity by ID with correct user"""
    created = activity_repository.create(
        sample_activity_data["name"],
        user_id=sample_activity_data["user_id"],
    )
    retrieved = activity_repository.get_by_user(
        created.id, sample_activity_data["user_id"]
    )
    assert retrieved is not None
    assert retrieved.id == created.id


def test_get_by_user_wrong_user(
    activity_repository, sample_activity_data
):
    """Test getting activity by ID with wrong user"""
    created = activity_repository.create(
        sample_activity_data["name"],
        user_id=sample_activity_data["user_id"],
    )
    retrieved = activity_repository.get_by_user(
        created.id, "wrong-user"
    )
    assert retrieved is None


def test_get_by_user_nonexistent(activity_repository):
    """Test getting non-existent activity by ID"""
    retrieved = activity_repository.get_by_user(
        999, "test-user"
    )
    assert retrieved is None


def test_get_by_name_existing(
    activity_repository, sample_activity_data
):
    """Test getting activity by name with correct user"""
    created = activity_repository.create(
        sample_activity_data["name"],
        user_id=sample_activity_data["user_id"],
    )
    retrieved = activity_repository.get_by_name(
        sample_activity_data["name"],
        sample_activity_data["user_id"],
    )
    assert retrieved is not None
    assert retrieved.id == created.id


def test_get_by_name_wrong_user(
    activity_repository, sample_activity_data
):
    """Test getting activity by name with wrong user"""
    activity_repository.create(
        sample_activity_data["name"],
        user_id=sample_activity_data["user_id"],
    )
    retrieved = activity_repository.get_by_name(
        sample_activity_data["name"],
        "wrong-user",
    )
    assert retrieved is None


def test_list_activities(
    activity_repository,
    sample_activity_data,
    test_db_session,
):
    """Test listing activities for a user"""
    # Create test user and other user
    other_user = User(
        username="otheruser",
        key_id="other-key",
        user_secret="other-secret",
    )
    test_db_session.add(other_user)
    test_db_session.commit()
    test_db_session.refresh(other_user)

    # Create activities for test user
    for i in range(3):
        activity_repository.create(
            f"Activity {i}",
            user_id=sample_activity_data["user_id"],
        )

    # Create activity for different user
    activity_repository.create(
        "Other Activity", user_id=other_user.id
    )

    # List activities for test user
    activities = activity_repository.list_activities(
        sample_activity_data["user_id"]
    )
    assert len(activities) == 3
    for activity in activities:
        assert (
            activity.user_id
            == sample_activity_data["user_id"]
        )

    # List activities for other user
    other_activities = activity_repository.list_activities(
        other_user.id
    )
    assert len(other_activities) == 1
    assert other_activities[0].name == "Other Activity"


def test_update_activity_success(
    activity_repository, sample_activity_data
):
    """Test updating activity with correct user"""
    created = activity_repository.create(
        sample_activity_data["name"],
        user_id=sample_activity_data["user_id"],
    )
    updated = activity_repository.update_activity(
        created.id,
        sample_activity_data["user_id"],
        {"name": "Updated Activity"},
    )
    assert updated is not None
    assert updated.name == "Updated Activity"


def test_update_activity_wrong_user(
    activity_repository, sample_activity_data
):
    """Test updating activity with wrong user"""
    created = activity_repository.create(
        sample_activity_data["name"],
        user_id=sample_activity_data["user_id"],
    )
    updated = activity_repository.update_activity(
        created.id,
        "wrong-user",
        {"name": "Updated Activity"},
    )
    assert updated is None


def test_update_activity_nonexistent(activity_repository):
    """Test updating non-existent activity"""
    updated = activity_repository.update_activity(
        999, "test-user", {"name": "Updated Activity"}
    )
    assert updated is None


def test_update_activity_invalid_color(
    activity_repository, sample_activity_data
):
    """Test updating activity with invalid color"""
    created = activity_repository.create(
        sample_activity_data["name"],
        user_id=sample_activity_data["user_id"],
    )
    with pytest.raises(ValueError) as exc_info:
        activity_repository.update_activity(
            created.id,
            sample_activity_data["user_id"],
            {"color": "invalid-color"},
        )
    assert "Color must be a valid hex code" in str(
        exc_info.value
    )


def test_delete_activity_success(
    activity_repository, sample_activity_data
):
    """Test deleting activity with correct user"""
    created = activity_repository.create(
        sample_activity_data["name"],
        user_id=sample_activity_data["user_id"],
    )
    result = activity_repository.delete_activity(
        created.id,
        sample_activity_data["user_id"],
    )
    assert result is True
    assert (
        activity_repository.get_by_user(
            created.id,
            sample_activity_data["user_id"],
        )
        is None
    )


def test_delete_activity_wrong_user(
    activity_repository, sample_activity_data
):
    """Test deleting activity with wrong user"""
    created = activity_repository.create(
        sample_activity_data["name"],
        user_id=sample_activity_data["user_id"],
    )
    result = activity_repository.delete_activity(
        created.id, "wrong-user"
    )
    assert result is False
    assert (
        activity_repository.get_by_user(
            created.id,
            sample_activity_data["user_id"],
        )
        is not None
    )


def test_delete_activity_nonexistent(activity_repository):
    """Test deleting non-existent activity"""
    result = activity_repository.delete_activity(
        999, "test-user"
    )
    assert result is False


def test_validate_existence_success(
    activity_repository, sample_activity_data
):
    """Test validating existence with correct user"""
    created = activity_repository.create(
        sample_activity_data["name"],
        user_id=sample_activity_data["user_id"],
    )
    activity = activity_repository.validate_existence(
        created.id,
        sample_activity_data["user_id"],
    )
    assert activity is not None
    assert activity.id == created.id


def test_validate_existence_wrong_user(
    activity_repository, sample_activity_data
):
    """Test validating existence with wrong user"""
    created = activity_repository.create(
        sample_activity_data["name"],
        user_id=sample_activity_data["user_id"],
    )
    with pytest.raises(HTTPException) as exc_info:
        activity_repository.validate_existence(
            created.id, "wrong-user"
        )
    assert exc_info.value.status_code == 404
    assert "Activity not found or access denied" in str(
        exc_info.value.detail
    )


def test_validate_existence_nonexistent(
    activity_repository,
):
    """Test validating existence of non-existent activity"""
    with pytest.raises(HTTPException) as exc_info:
        activity_repository.validate_existence(
            999, "test-user"
        )
    assert exc_info.value.status_code == 404
