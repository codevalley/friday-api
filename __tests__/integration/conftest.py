"""Test fixtures for integration tests."""

import pytest
from sqlalchemy.orm import Session
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from fastapi.security import HTTPAuthorizationCredentials

from repositories.DocumentRepository import (
    DocumentRepository,
)
from services.DocumentService import DocumentService
from infrastructure.storage.mock_sync import (
    MockStorageService,
)
from domain.storage import IStorageService
from configs.Database import get_db_connection
from dependencies import get_current_user
from orm.UserModel import User


@pytest.fixture
def storage_service() -> IStorageService:
    """Create a mock storage service."""
    return MockStorageService()


@pytest.fixture
def document_service(
    storage_service: IStorageService,
    test_db_session: Session,
) -> DocumentService:
    """Create a document service with mocked dependencies."""
    repository = DocumentRepository(test_db_session)
    return DocumentService(
        repository=repository, storage=storage_service
    )


@pytest.fixture
def mock_current_user():
    """Create mock current user."""
    return User(
        id=1,
        username="testuser",
        key_id="test-key-id",
        user_secret="test-secret-hash",
    )


@pytest.fixture
def mock_auth_credentials():
    """Create mock auth credentials."""
    return HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="test-token"
    )


@pytest_asyncio.fixture
async def async_client(
    fastapi_app, test_db_session, mock_current_user
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""

    def override_get_db():
        try:
            yield test_db_session
        finally:
            test_db_session.close()

    async def mock_get_current_user():
        return mock_current_user

    fastapi_app.dependency_overrides[
        get_db_connection
    ] = override_get_db
    fastapi_app.dependency_overrides[
        get_current_user
    ] = mock_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def sample_timeline_events(
    test_db_session, mock_current_user
):
    """Create sample timeline events for testing."""
    from orm.TimelineModel import Timeline
    from domain.timeline import TimelineEventType
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    events = [
        Timeline(
            event_type=TimelineEventType.TASK_CREATED,
            user_id=mock_current_user.id,
            timestamp=now - timedelta(minutes=2),
            event_metadata={
                "task_id": "1",
                "task_title": "Test Task 1",
            },
        ),
        Timeline(
            event_type=TimelineEventType.NOTE_CREATED,
            user_id=mock_current_user.id,
            timestamp=now - timedelta(minutes=1),
            event_metadata={
                "note_id": "1",
                "note_title": "Test Note 1",
            },
        ),
        Timeline(
            event_type=TimelineEventType.TASK_COMPLETED,
            user_id=mock_current_user.id,
            timestamp=now,
            event_metadata={
                "task_id": "1",
                "task_title": "Test Task 1",
            },
        ),
    ]

    # Add all events to the session
    for event in events:
        test_db_session.add(event)

    # Commit the transaction
    test_db_session.commit()

    # Refresh all events to ensure they're bound to the session
    for event in events:
        test_db_session.refresh(event)

    yield events

    # Cleanup after tests
    for event in events:
        test_db_session.delete(event)
    test_db_session.commit()
