"""Test configuration and fixtures."""

import asyncio
import sys
import uuid
import warnings
import pytest

# Standard library imports
from datetime import datetime, timezone
from typing import Generator
from unittest.mock import Mock

# Third-party imports
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Local imports
from configs.Database import get_db_connection
from configs.Environment import get_environment_variables
from configs.Logging import configure_logging
from main import app
from orm.ActivityModel import Activity
from orm.BaseModel import Base
from orm.MomentModel import Moment
from orm.NoteModel import Note
from orm.UserModel import User
from repositories.NoteRepository import NoteRepository
from services.NoteService import NoteService
from utils.security import hash_user_secret

# Set test environment before any imports
import os

os.environ["ENV"] = "test"


# Add project root to Python path
project_root = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
sys.path.insert(0, project_root)

# Get environment variables
env = get_environment_variables()

# Construct test database URL from environment variables
TEST_SQLALCHEMY_DATABASE_URL = (
    f"{env.DATABASE_DIALECT}{env.DATABASE_DRIVER}"
    f"://{env.DATABASE_USERNAME}:{env.DATABASE_PASSWORD}"
    f"@{env.DATABASE_HOSTNAME}:{env.DATABASE_PORT}"
    f"/{env.DATABASE_NAME}"
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
    """Create a new FastAPI TestClient."""

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


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Configure logging for all tests."""
    configure_logging(is_test=True)
    yield


# Suppress specific warnings if needed
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module="sqlalchemy.*",
)


@pytest.fixture(autouse=True)
async def setup_teardown() -> Generator:
    """Setup and teardown for all tests."""
    # Setup
    yield
    # Teardown
    await asyncio.gather(*asyncio.all_tasks())


@pytest.fixture(scope="function")
def mock_note_repository():
    """Create a mock note repository for testing."""
    return Mock(spec=NoteRepository)


@pytest.fixture(scope="function")
def note_service(mock_note_repository):
    """Create a note service instance with mocked repository."""
    return NoteService(mock_note_repository)


@pytest.fixture(scope="function")
def sample_note(test_db_session, sample_user):
    """Create a sample note for testing."""
    note = Note(
        user_id=sample_user.id,
        content="Test Note Content",
        attachment_url=None,
        attachment_type=None,
    )
    test_db_session.add(note)
    test_db_session.commit()
    test_db_session.refresh(note)
    return note


@pytest.fixture
def mock_db():
    return Mock(spec=Session)


@pytest.fixture
def mock_user():
    return Mock(id="test-user-id")
