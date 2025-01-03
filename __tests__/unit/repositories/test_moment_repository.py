import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import uuid4

from repositories.MomentRepository import MomentRepository
from repositories.ActivityRepository import (
    ActivityRepository,
)
from repositories.UserRepository import UserRepository
from orm.MomentModel import Moment as MomentModel
from orm.ActivityModel import Activity as ActivityModel
from orm.UserModel import User as UserModel


@pytest.fixture
def user_repo(test_db_session: Session) -> UserRepository:
    return UserRepository(test_db_session)


@pytest.fixture
def activity_repo(
    test_db_session: Session,
) -> ActivityRepository:
    return ActivityRepository(test_db_session)


@pytest.fixture
def moment_repo(
    test_db_session: Session,
) -> MomentRepository:
    return MomentRepository(test_db_session)


@pytest.fixture
def test_user(user_repo: UserRepository) -> UserModel:
    user = UserModel(
        id="test-user-1",
        username="testuser1",
        key_id=str(uuid4()),
        user_secret="test-secret-1",
    )
    return user_repo.create(user)


@pytest.fixture
def another_user(user_repo: UserRepository) -> UserModel:
    user = UserModel(
        id="test-user-2",
        username="testuser2",
        key_id=str(uuid4()),
        user_secret="test-secret-2",
    )
    return user_repo.create(user)


@pytest.fixture
def test_activity(
    activity_repo: ActivityRepository, test_user: UserModel
) -> ActivityModel:
    activity = ActivityModel(
        name="Test Activity",
        description="Test activity description",
        user_id=test_user.id,
        icon="📝",
        color="#FF0000",
        activity_schema={
            "type": "object",
            "properties": {"note": {"type": "string"}},
            "required": ["note"],
        },
    )
    return activity_repo.create(activity)


@pytest.fixture
def another_activity(
    activity_repo: ActivityRepository, test_user: UserModel
) -> ActivityModel:
    activity = ActivityModel(
        name="Another Activity",
        description="Another activity description",
        user_id=test_user.id,
        icon="🎯",
        color="#00FF00",
        activity_schema={
            "type": "object",
            "properties": {"note": {"type": "string"}},
            "required": ["note"],
        },
    )
    return activity_repo.create(activity)


@pytest.fixture
def test_moment(
    moment_repo: MomentRepository,
    test_activity: ActivityModel,
    test_user: UserModel,
) -> MomentModel:
    moment = MomentModel(
        user_id=test_user.id,
        activity_id=test_activity.id,
        data={"note": "Test note"},
        timestamp=datetime.now(timezone.utc),
    )
    return moment_repo.create(moment)


def test_create_moment(
    moment_repo: MomentRepository,
    test_activity: ActivityModel,
    test_user: UserModel,
):
    """Test creating a moment"""
    data = {"note": "Test note"}
    moment = MomentModel(
        user_id=test_user.id,
        activity_id=test_activity.id,
        data=data,
        timestamp=datetime.now(timezone.utc),
    )

    created = moment_repo.create(moment)
    assert created.id is not None
    assert created.user_id == test_user.id
    assert created.activity_id == test_activity.id
    assert created.data == data


def test_create_moment_with_invalid_data(
    moment_repo: MomentRepository,
    test_activity: ActivityModel,
    test_user: UserModel,
):
    """Test creating a moment with invalid data"""
    data = {
        "invalid": "data"
    }  # Missing required "note" field
    moment = MomentModel(
        user_id=test_user.id,
        activity_id=test_activity.id,
        data=data,
        timestamp=datetime.now(timezone.utc),
    )

    with pytest.raises(
        ValueError, match="Invalid moment data"
    ):
        moment_repo.create(moment)


def test_create_moment_with_invalid_activity(
    moment_repo: MomentRepository, test_user: UserModel
):
    """Test creating a moment with non-existent activity"""
    data = {"note": "Test note"}
    moment = MomentModel(
        user_id=test_user.id,
        activity_id=999,  # Non-existent activity ID
        data=data,
        timestamp=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError):
        moment_repo.create(moment)


def test_create_moment_with_invalid_user(
    moment_repo: MomentRepository,
    test_activity: ActivityModel,
):
    """Test creating a moment with non-existent user"""
    data = {"note": "Test note"}
    moment = MomentModel(
        user_id="non-existent-user",
        activity_id=test_activity.id,
        data=data,
        timestamp=datetime.now(timezone.utc),
    )

    with pytest.raises(HTTPException) as exc_info:
        moment_repo.create(moment)
    assert exc_info.value.status_code == 409
    assert "foreign key constraint fails" in str(
        exc_info.value.detail
    )


def test_get_recent_by_user(
    moment_repo: MomentRepository,
    test_activity: ActivityModel,
    test_user: UserModel,
):
    """Test getting recent moments for a user"""
    # Create multiple moments with different timestamps
    base_time = datetime.now(timezone.utc)
    moments = []
    for i in range(3):
        moment = MomentModel(
            user_id=test_user.id,
            activity_id=test_activity.id,
            data={"note": f"Test note {i}"},
            timestamp=base_time - timedelta(minutes=i),
        )
        moments.append(moment_repo.create(moment))

    # Get recent moments
    recent_moments = moment_repo.get_recent_by_user(
        test_user.id, limit=2
    )

    # Should return 2 most recent moments in descending order
    assert len(recent_moments) == 2
    assert (
        recent_moments[0].id == moments[0].id
    )  # Most recent
    assert (
        recent_moments[1].id == moments[1].id
    )  # Second most recent


def test_get_recent_activities(
    moment_repo: MomentRepository,
    activity_repo: ActivityRepository,
    test_user: UserModel,
):
    """Test getting recently used activities"""
    # Create multiple activities with controlled timestamps
    activities = []
    base_time = datetime.now(timezone.utc)

    for i in range(3):
        activity = ActivityModel(
            name=f"Test Activity {i}",
            description=f"Description for activity {i}",
            user_id=test_user.id,
            icon="📝",
            color="#FF0000",
            activity_schema={
                "type": "object",
                "properties": {"note": {"type": "string"}},
                "required": ["note"],
            },
        )
        activities.append(activity_repo.create(activity))

    # Create moments for each activity with increasing timestamps
    for i, activity in enumerate(activities):
        moment = MomentModel(
            user_id=test_user.id,
            activity_id=activity.id,
            data={"note": "Test note"},
            # Use controlled timestamps to ensure deterministic ordering
            timestamp=datetime.fromtimestamp(
                base_time.timestamp() + i, timezone.utc
            ),
        )
        moment_repo.create(moment)

    # Get recent activities
    recent = moment_repo.get_recent_activities(limit=2)
    assert len(recent) == 2
    assert (
        recent[0].id == activities[2].id
    )  # Most recent first
    assert recent[1].id == activities[1].id


def test_get_activity_moments_count(
    moment_repo: MomentRepository,
    test_activity: ActivityModel,
    test_user: UserModel,
):
    """Test getting count of moments for an activity"""
    # Create multiple moments
    for i in range(3):
        moment = MomentModel(
            user_id=test_user.id,
            activity_id=test_activity.id,
            data={"note": f"Test note {i}"},
            timestamp=datetime.now(timezone.utc),
        )
        moment_repo.create(moment)

    count = moment_repo.get_activity_moments_count(
        test_activity.id
    )
    assert count == 3


def test_list_moments_with_filters(
    moment_repo: MomentRepository,
    test_activity: ActivityModel,
    test_user: UserModel,
):
    """Test listing moments with various filters"""
    # Create multiple moments with controlled timestamps
    start_time = datetime.now(timezone.utc)
    moments = []

    # Create moments with 1 second intervals to ensure deterministic ordering
    for i in range(3):
        moment = MomentModel(
            user_id=test_user.id,
            activity_id=test_activity.id,
            data={"note": f"Test note {i}"},
            timestamp=start_time,
        )
        moments.append(moment_repo.create(moment))
        start_time = datetime.fromtimestamp(
            start_time.timestamp() + 1, timezone.utc
        )

    end_time = (
        start_time  # Use the last timestamp as end_time
    )

    # Test various filters
    result = moment_repo.list_moments(
        page=1,
        size=10,
        activity_id=test_activity.id,
        start_time=moments[
            0
        ].timestamp,  # Use first moment's timestamp
        end_time=end_time,
        user_id=test_user.id,
    )

    # Verify pagination metadata
    assert result.total == 3, "Expected 3 moments in total"
    assert (
        len(result.items) == 3
    ), "Expected 3 moments in items"
    assert result.page == 1
    assert result.size == 10
    assert result.pages == 1

    # Verify ordering (should be newest first)
    assert (
        result.items[0].timestamp
        > result.items[1].timestamp
    ), "Moments should be ordered by timestamp descending"
    assert (
        result.items[1].timestamp
        > result.items[2].timestamp
    ), "Moments should be ordered by timestamp descending"

    # Test with narrower time window
    narrow_result = moment_repo.list_moments(
        page=1,
        size=10,
        activity_id=test_activity.id,
        start_time=moments[
            1
        ].timestamp,  # Start from second moment
        end_time=end_time,
        user_id=test_user.id,
    )

    assert (
        narrow_result.total == 2
    ), "Expected 2 moments in narrower time window"
    assert (
        len(narrow_result.items) == 2
    ), "Expected 2 moments in items for narrower time window"


def test_update_moment(
    moment_repo: MomentRepository, test_moment: MomentModel
):
    """Test updating a moment"""
    new_data = {"note": "Updated note"}
    updated = moment_repo.update_moment(
        test_moment.id, {"data": new_data}
    )

    assert updated is not None
    assert updated.data == new_data


def test_update_moment_invalid_data(
    moment_repo: MomentRepository, test_moment: MomentModel
):
    """Test updating a moment with invalid data"""
    invalid_data = {
        "invalid": "data"
    }  # Missing required "note" field

    with pytest.raises(ValueError):
        moment_repo.update_moment(
            test_moment.id, {"data": invalid_data}
        )


def test_delete_moment(
    moment_repo: MomentRepository, test_moment: MomentModel
):
    """Test deleting a moment"""
    assert moment_repo.delete_moment(test_moment.id) is True
    assert moment_repo.get(test_moment.id) is None


def test_delete_nonexistent_moment(
    moment_repo: MomentRepository,
):
    """Test deleting a non-existent moment"""
    assert moment_repo.delete_moment(999) is False


def test_validate_existence(
    moment_repo: MomentRepository, test_moment: MomentModel
):
    """Test validating moment existence"""
    moment = moment_repo.validate_existence(test_moment.id)
    assert moment.id == test_moment.id


def test_validate_existence_nonexistent(
    moment_repo: MomentRepository,
):
    """Test validating non-existent moment"""
    with pytest.raises(HTTPException) as exc:
        moment_repo.validate_existence(999)
    assert exc.value.status_code == 404
