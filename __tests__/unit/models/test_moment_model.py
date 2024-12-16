"""Test MomentModel class."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.ActivityModel import Activity
from models.MomentModel import Moment
from models.UserModel import User


@pytest.fixture
async def sample_user(
    test_db_session: AsyncSession,
) -> User:
    """Create a sample user for testing."""
    user = User(
        username="testuser",
        key_id=str(uuid.uuid4()),
        user_secret="test-secret-hash",
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture
async def sample_activity(
    test_db_session: AsyncSession,
    sample_user: User,
) -> Activity:
    """Create a sample activity for testing."""
    activity = Activity(
        name="Test Activity",
        description="Test Description",
        user_id=sample_user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
            "required": ["notes"],
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity)
    await test_db_session.commit()
    await test_db_session.refresh(activity)
    return activity


@pytest.mark.asyncio
async def test_moment_model_initialization(
    sample_activity: Activity,
    sample_user: User,
) -> None:
    """Test that a moment can be created with valid data."""
    activity = await sample_activity
    user = await sample_user
    moment = Moment(
        activity_id=activity.id,
        user_id=user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
    )

    assert moment.activity_id == activity.id
    assert moment.user_id == user.id
    assert moment.data == {"notes": "Test moment"}


@pytest.mark.asyncio
async def test_moment_model_db_persistence(
    test_db_session: AsyncSession,
    sample_activity: Activity,
    sample_user: User,
) -> None:
    """Test that a moment can be persisted to the database."""
    activity = await sample_activity
    user = await sample_user
    moment = Moment(
        activity_id=activity.id,
        user_id=user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)
    await test_db_session.commit()
    await test_db_session.refresh(moment)

    result = await test_db_session.execute(
        Moment.__table__.select().where(
            Moment.activity_id == activity.id
        )
    )
    saved_moment = result.scalar_one()

    assert saved_moment is not None
    assert saved_moment.activity_id == activity.id
    assert saved_moment.data == {"notes": "Test moment"}


@pytest.mark.asyncio
async def test_moment_activity_relationship(
    test_db_session: AsyncSession,
    sample_activity: Activity,
    sample_user: User,
) -> None:
    """Test the relationship between Moment and Activity models."""
    activity = await sample_activity
    user = await sample_user
    moment = Moment(
        activity_id=activity.id,
        user_id=user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)
    await test_db_session.commit()
    await test_db_session.refresh(moment)

    assert moment.activity == activity
    assert len(activity.moments) == 1
    assert activity.moments[0] == moment


@pytest.mark.asyncio
async def test_moment_cascade_delete(
    test_db_session: AsyncSession,
    sample_activity: Activity,
    sample_user: User,
) -> None:
    """Test that moments are deleted when their activity is deleted."""
    activity = await sample_activity
    user = await sample_user
    moment = Moment(
        activity_id=activity.id,
        user_id=user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)
    await test_db_session.commit()
    await test_db_session.refresh(moment)

    moment_id = moment.id
    test_db_session.delete(activity)
    await test_db_session.commit()

    result = await test_db_session.execute(
        Moment.__table__.select().where(
            Moment.id == moment_id
        )
    )
    deleted_moment = result.scalar_one_or_none()
    assert deleted_moment is None


@pytest.mark.asyncio
async def test_moment_data_validation(
    test_db_session: AsyncSession,
    sample_activity: Activity,
    sample_user: User,
) -> None:
    """Test that moment data is validated against activity schema."""
    activity = await sample_activity
    user = await sample_user
    # Try to create a moment with invalid data (missing required field)
    moment = Moment(
        activity_id=activity.id,
        user_id=user.id,
        data={},  # Missing required 'notes' field
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)

    with pytest.raises(ValueError) as exc_info:
        await test_db_session.commit()
    assert (
        "data failed validation"
        in str(exc_info.value).lower()
    )


@pytest.mark.asyncio
async def test_moment_required_fields(
    test_db_session: AsyncSession,
    sample_activity: Activity,
    sample_user: User,
) -> None:
    """Test that required fields raise appropriate errors when missing."""
    user = await sample_user
    # Missing activity_id
    moment = Moment(
        user_id=user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)

    with pytest.raises(IntegrityError) as exc_info:
        await test_db_session.commit()
    assert "NOT NULL constraint failed" in str(
        exc_info.value
    )
