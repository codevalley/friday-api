"""Test configuration and fixtures."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from configs.Database import get_db_connection
from main import app
from models.ActivityModel import Activity
from models.BaseModel import Base
from models.MomentModel import Moment
from models.UserModel import User


# Create in-memory test database
TEST_SQLALCHEMY_DATABASE_URL = (
    "sqlite+aiosqlite:///:memory:"
)
SYNC_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create async engine for async operations
async_engine = create_async_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=True,  # Enable SQL logging for debugging
)

# Create sync engine for sync operations
sync_engine = create_engine(
    SYNC_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create async session factory
AsyncTestingSessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    expire_on_commit=False,  # Prevent expired objects after commit
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db_session() -> (
    AsyncGenerator[AsyncSession, None]
):
    """Create a fresh database session for a test."""
    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    session = AsyncTestingSessionLocal()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()

    # Clean up
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def async_client(
    test_db_session: AsyncSession,
) -> AsyncClient:
    """Create a new FastAPI AsyncClient.

    Uses the test_db_session fixture to override the get_db dependency.
    """

    async def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db_connection] = (
        override_get_db
    )
    client = AsyncClient(app=app, base_url="http://test")
    yield client
    await client.aclose()
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def sample_user(
    test_db_session: AsyncSession,
) -> User:
    """Create a sample user for testing with a unique username."""
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"testuser_{unique_id}",
        key_id=str(uuid.uuid4()),
        user_secret="test-secret-hash",
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def another_user(
    test_db_session: AsyncSession,
) -> User:
    """Create another user for testing user isolation."""
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"another_user_{unique_id}",
        key_id=str(uuid.uuid4()),
        user_secret="another-test-secret-hash",
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def sample_activity(
    test_db_session: AsyncSession,
    sample_user: User,
) -> Activity:
    """Create a sample activity for testing."""
    activity = Activity(
        name="test_activity",
        description="Test activity description",
        activity_schema={
            "type": "object",
            "properties": {"notes": {"type": "string"}},
            "required": ["notes"],
        },
        icon="📝",
        color="#000000",
        user_id=sample_user.id,
    )
    test_db_session.add(activity)
    await test_db_session.commit()
    await test_db_session.refresh(activity)
    return activity


@pytest.fixture(scope="function")
async def sample_moment(
    test_db_session: AsyncSession,
    sample_activity: Activity,
    sample_user: User,
) -> Moment:
    """Create a sample moment for testing."""
    moment = Moment(
        activity_id=sample_activity.id,
        user_id=sample_user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)
    await test_db_session.commit()
    await test_db_session.refresh(moment)
    return moment
