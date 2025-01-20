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
from moto import mock_aws
import boto3

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
from domain.storage import IStorageService, StoredFile
from infrastructure.storage import (
    LocalStorageService,
    S3StorageService,
)
from orm.DocumentModel import Document
from services.DocumentService import DocumentService

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

# Debug prints for test database configuration
print("\n=== Test Database Configuration ===")
print(f"ENV variable: {os.getenv('ENV')}")
print(f"DATABASE_DIALECT: {env.DATABASE_DIALECT}")
print(f"DATABASE_DRIVER: {env.DATABASE_DRIVER}")

# Construct test database URL - being explicit about the format
dialect = env.DATABASE_DIALECT.split("+")[
    0
]  # Get just 'mysql' if it includes driver
driver = env.DATABASE_DRIVER.lstrip(
    "+"
)  # Remove leading + if present
TEST_SQLALCHEMY_DATABASE_URL = (
    f"{dialect}+{driver}"
    f"://{env.DATABASE_USERNAME}:{env.DATABASE_PASSWORD}"
    f"@{env.DATABASE_HOSTNAME}:{env.DATABASE_PORT}"
    f"/{env.DATABASE_NAME}"
)

print(f"Test Database URL: {TEST_SQLALCHEMY_DATABASE_URL}")
print("================================\n")


@pytest.fixture(scope="session")
def redis_connection():
    """Create a fake Redis connection for testing."""
    return fakeredis.FakeStrictRedis()


@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL)

    # Drop tables in correct order (reverse dependency order)
    for table in reversed(Base.metadata.sorted_tables):
        try:
            table.drop(engine, checkfirst=True)
        except Exception as e:
            print(
                f"Warning: Could not drop table {table}: {e}"
            )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine

    # Drop tables in correct order again during cleanup
    for table in reversed(Base.metadata.sorted_tables):
        try:
            table.drop(engine, checkfirst=True)
        except Exception as e:
            print(
                f"Warning: Could not drop table {table}: {e}"
            )


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
def robo_service(request):
    """Create a robo service for testing.

    By default, returns a mock service. For integration tests,
    use @pytest.mark.integration to get a real service.
    """
    if request.node.get_closest_marker("integration"):
        from services.OpenAIService import OpenAIService
        from configs.RoboConfig import get_robo_settings

        config = get_robo_settings()
        return OpenAIService(config)
    else:
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


@pytest.fixture(scope="function")
def activity_service(test_db_session, queue_service):
    """Create an activity service instance for testing."""
    from services.ActivityService import ActivityService
    from repositories.ActivityRepository import (
        ActivityRepository,
    )

    repository = ActivityRepository(test_db_session)
    return ActivityService(repository, queue_service)


# Storage fixtures
@pytest.fixture
def storage_service():
    """Create a mock storage service for testing."""
    mock_service = Mock(spec=IStorageService)

    async def mock_store(
        file_data: bytes,
        file_id: str,
        user_id: str,
        mime_type: str,
    ):
        return StoredFile(
            path=f"/test/{file_id}",
            mime_type=mime_type,
            size_bytes=len(file_data),
        )

    async def mock_retrieve(file_path: str):
        return b"test file content"

    async def mock_delete(file_path: str):
        return True

    mock_service.store = mock_store
    mock_service.retrieve = mock_retrieve
    mock_service.delete = mock_delete
    return mock_service


@pytest.fixture
def local_storage_service(tmp_path):
    """Create a real local storage service for integration tests."""
    return LocalStorageService(base_path=tmp_path)


@pytest.fixture
def s3_storage_service():
    """Create a mocked S3 storage service using moto."""
    with mock_aws():
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket="test-bucket")
        yield S3StorageService(
            bucket_name="test-bucket",
            endpoint_url="http://localhost:4566",
        )


# Document fixtures
@pytest.fixture
def sample_document(test_db_session, sample_user):
    """Create a sample document for testing."""
    doc = Document(
        name="Test Document",
        storage_url="/test/path",
        mime_type="text/plain",
        size_bytes=100,
        user_id=sample_user.id,
        status="ACTIVE",
    )
    test_db_session.add(doc)
    test_db_session.commit()
    return doc


@pytest.fixture
def sample_public_document(test_db_session, sample_user):
    """Create a sample public document."""
    doc = Document(
        name="Public Document",
        storage_url="/public/path",
        mime_type="text/plain",
        size_bytes=100,
        user_id=sample_user.id,
        status="ACTIVE",
        is_public=True,
        unique_name="test-doc",
    )
    test_db_session.add(doc)
    test_db_session.commit()
    return doc


@pytest.fixture
def document_service(test_db_session, storage_service):
    """Create a document service instance for testing."""
    return DocumentService(
        db=test_db_session, storage=storage_service
    )
