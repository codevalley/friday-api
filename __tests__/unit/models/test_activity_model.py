"""Test ActivityModel class."""

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


@pytest.mark.asyncio
async def test_activity_model_initialization(
    sample_user: User,
) -> None:
    """Test that an activity can be created with valid data."""
    user = await sample_user
    activity = Activity(
        name="Test Activity",
        description="Test Description",
        user_id=user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
        },
        icon="📝",
        color="#FF0000",
    )

    assert activity.name == "Test Activity"
    assert activity.description == "Test Description"
    assert activity.user_id == user.id
    assert activity.activity_schema == {
        "type": "object",
        "properties": {"notes": {"type": "string"}},
    }
    assert activity.icon == "📝"
    assert activity.color == "#FF0000"


@pytest.mark.asyncio
async def test_activity_model_db_persistence(
    test_db_session: AsyncSession,
    sample_user: User,
) -> None:
    """Test that an activity can be persisted to the database."""
    user = await sample_user
    activity = Activity(
        name="Test Activity",
        description="Test Description",
        user_id=user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity)
    await test_db_session.commit()
    await test_db_session.refresh(activity)

    result = await test_db_session.execute(
        Activity.__table__.select().where(
            Activity.name == "Test Activity"
        )
    )
    saved_activity = result.scalar_one()

    assert saved_activity is not None
    assert saved_activity.name == "Test Activity"
    assert saved_activity.description == "Test Description"
    assert saved_activity.user_id == user.id


@pytest.mark.asyncio
async def test_activity_moment_relationship(
    test_db_session: AsyncSession,
    sample_user: User,
) -> None:
    """Test the relationship between Activity and Moment models."""
    user = await sample_user
    activity = Activity(
        name="Test Activity",
        description="Test Description",
        user_id=user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity)
    await test_db_session.commit()
    await test_db_session.refresh(activity)

    moment = Moment(
        activity_id=activity.id,
        user_id=user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)
    await test_db_session.commit()
    await test_db_session.refresh(moment)

    assert len(activity.moments) == 1
    assert activity.moments[0].data == {
        "notes": "Test moment"
    }


@pytest.mark.asyncio
async def test_activity_name_unique_constraint(
    test_db_session: AsyncSession,
    sample_user: User,
) -> None:
    """Test that activity names must be unique per user."""
    user = await sample_user
    activity1 = Activity(
        name="Test Activity",
        description="Test Description",
        user_id=user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity1)
    await test_db_session.commit()
    await test_db_session.refresh(activity1)

    # Try to create another activity with the same name for the same user
    activity2 = Activity(
        name="Test Activity",  # Same name
        description="Another Description",
        user_id=user.id,  # Same user
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
        },
        icon="📝",
        color="#00FF00",
    )
    test_db_session.add(activity2)

    with pytest.raises(IntegrityError) as exc_info:
        await test_db_session.commit()
    assert "UNIQUE constraint failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_activity_required_fields(
    test_db_session: AsyncSession,
    sample_user: User,
) -> None:
    """Test that required fields raise appropriate errors when missing."""
    user = await sample_user
    activity = Activity(
        description="Test Description",  # Missing name
        user_id=user.id,
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
        },
        icon="📝",
        color="#FF0000",
    )
    test_db_session.add(activity)

    with pytest.raises(IntegrityError) as exc_info:
        await test_db_session.commit()
    assert "NOT NULL constraint failed" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_activity_schema_validation(
    sample_user: User,
) -> None:
    """Test that activity_schema must be a valid JSON object."""
    user = await sample_user
    with pytest.raises(ValueError, match="Invalid schema"):
        Activity(
            name="Test Activity",
            description="Test Description",
            user_id=user.id,
            activity_schema="invalid",  # Not a JSON object
            icon="📝",
            color="#FF0000",
        )
