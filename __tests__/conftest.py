"""Test configuration and fixtures."""

import asyncio
import sys
import uuid
import warnings
import pytest
import fakeredis

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
from domain.robo import RoboProcessingResult

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
def redis_connection():
    """Create a fake Redis connection for testing."""
    return fakeredis.FakeStrictRedis()


@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a new database session for testing."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
    )
    session = TestingSessionLocal()
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
def note_service(test_db_session, queue_service):
    """Create a note service instance.

    Uses real database session and mock queue service.
    """
    return NoteService(test_db_session, queue_service)


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


@pytest.fixture(scope="function")
def queue_service():
    """Mock queue service for testing."""
    mock_queue = Mock()
    mock_queue.enqueue.return_value = None
    return mock_queue


@pytest.fixture(scope="function")
def robo_service():
    """Mock robo service for testing."""
    mock_robo = Mock()
    mock_robo.process_text.return_value = (
        RoboProcessingResult(
            content="Test Content",
            metadata={"title": "Test Title"},
            tokens_used=100,
            model_name="test-model",
        )
    )
    return mock_robo


@pytest.fixture(scope="function")
def mock_activity_service():
    """Mock activity service for testing."""
    return Mock()


@pytest.fixture(scope="function")
def mock_auth_middleware():
    """Mock authentication middleware for testing."""
    return Mock()


@pytest.fixture(scope="function")
def fastapi_app():
    """Get the FastAPI app instance."""
    return app
