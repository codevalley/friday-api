"""Test configuration and fixtures."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from configs.Database import get_db_connection
from main import app
from models.ActivityModel import Activity
from models.BaseModel import Base
from models.MomentModel import Moment
from models.UserModel import User
from utils.security import hash_user_secret


# Use test MySQL database
TEST_SQLALCHEMY_DATABASE_URL = (
    "mysql+pymysql://"
    "root:1234567890@localhost:3306/"
    "test_fridaystore"
)


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_SQLALCHEMY_DATABASE_URL,
        echo=True,  # Enable SQL logging for debugging
        pool_pre_ping=True,  # Enable connection health checks
        pool_recycle=3600,  # Recycle connections after 1 hour
    )
    return engine


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create test session factory."""
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
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
def test_db_session(test_engine, test_session_factory):
    """Create a fresh database session for a test."""
    # Drop and recreate tables before running any tests
    connection = test_engine.connect()
    transaction = connection.begin()

    try:
        # Drop all tables in a transaction
        Base.metadata.drop_all(bind=connection)
        # Create all tables in the same transaction
        Base.metadata.create_all(bind=connection)
        transaction.commit()
    except Exception as e:
        transaction.rollback()
        raise e
    finally:
        connection.close()

    # Create session for the test
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session):
    """Create a new FastAPI TestClient.

    Uses the test_db_session fixture to override the get_db dependency.
    """

    def override_get_db():
        try:
            yield test_db_session
        finally:
            test_db_session.close()

    app.dependency_overrides[
        get_db_connection
    ] = override_get_db
    return TestClient(app)


@pytest.fixture(scope="function")
def sample_user(test_db_session):
    """Create a sample user for testing with a unique username."""
    unique_id = str(uuid.uuid4())[:8]
    username = f"testuser_{unique_id}"
    password = "test-password"
    hashed_password = hash_user_secret(password)

    user = User(
        username=username,
        key_id=str(uuid.uuid4()),
        user_secret=hashed_password,
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def another_user(test_db_session):
    """Create another user for testing user isolation."""
    unique_id = str(uuid.uuid4())[:8]
    username = f"another_user_{unique_id}"
    password = "test-password"
    hashed_password = hash_user_secret(password)

    user = User(
        username=username,
        key_id=str(uuid.uuid4()),
        user_secret=hashed_password,
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def sample_activity(test_db_session, sample_user):
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
    test_db_session.commit()
    test_db_session.refresh(activity)
    return activity


@pytest.fixture(scope="function")
def sample_moment(
    test_db_session, sample_activity, sample_user
):
    """Create a sample moment for testing."""
    moment = Moment(
        activity_id=sample_activity.id,
        user_id=sample_user.id,
        data={"notes": "Test moment"},
        timestamp=datetime.now(timezone.utc),
    )
    test_db_session.add(moment)
    test_db_session.commit()
    test_db_session.refresh(moment)
    return moment
