"""Configure pytest for the project."""

import os
import sys
from typing import Generator
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from orm.BaseModel import Base

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    # Use SQLite in-memory database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(
    test_engine,
) -> Generator[Session, None, None]:
    """Create a new database session for a test.

    The session is rolled back after each test.
    """
    # Create a new session for each test
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        # Roll back any changes and close the session
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Store original environment
    original_env = dict(os.environ)

    # Set test environment variables
    os.environ.update(
        {
            "ENV": "test",
            "API_VERSION": "v1",
            "APP_NAME": "friday-api-test",
            "DEBUG_MODE": "true",
            # Database config
            "DATABASE_DIALECT": "sqlite",
            "DATABASE_DRIVER": "",
            "DATABASE_HOSTNAME": ":memory:",
            "DATABASE_NAME": "test_db",
            "DATABASE_PASSWORD": "test",
            "DATABASE_PORT": "0",
            "DATABASE_USERNAME": "test",
            # Robo config
            "ROBO_API_KEY": "test-key",
            "ROBO_MODEL_NAME": "test-model",
            "ROBO_MAX_RETRIES": "3",
            "ROBO_TIMEOUT_SECONDS": "30",
            "ROBO_TEMPERATURE": "0.7",
            "ROBO_MAX_TOKENS": "150",
            # Prompt config
            "ROBO_NOTE_ENRICHMENT_PROMPT": "note_enrichment.txt",
            "ROBO_ACTIVITY_SCHEMA_PROMPT": "activity_schema.txt",
            "ROBO_TASK_ENRICHMENT_PROMPT": "task_enrichment.txt",
            # Redis config
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_DB": "0",
            "REDIS_PASSWORD": "",
            "REDIS_SSL": "false",
            "REDIS_TIMEOUT": "10",
            "QUEUE_JOB_TIMEOUT": "600",
            "QUEUE_JOB_TTL": "3600",
        }
    )

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
