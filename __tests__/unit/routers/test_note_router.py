"""Test NoteRouter class."""

import pytest
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from unittest.mock import Mock

from configs.Database import get_db_connection
from dependencies import get_current_user
from orm.UserModel import User
from routers.v1.NoteRouter import router as note_router
from schemas.pydantic.NoteSchema import NoteCreate
from services.NoteService import NoteService


@pytest.fixture
def mock_note_service(mock_db_connection):
    """Create mock NoteService."""
    service = Mock(spec=NoteService)
    # Ensure create_note is properly mocked
    service.create_note = Mock()
    # Initialize with mock db
    service.db = mock_db_connection
    return service


@pytest.fixture
def test_user(test_db_session):
    """Create a test user in the database."""
    user = User(
        id="test-user",
        username="testuser",
        key_id="test-key-id",
        user_secret="test-secret-hash",
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def mock_current_user(test_user):
    """Create mock current user."""
    user = Mock(spec=User)
    user.id = test_user.id
    user.username = test_user.username
    user.key_id = test_user.key_id
    user.user_secret = test_user.user_secret
    return user


@pytest.fixture
def mock_auth_credentials():
    """Create mock auth credentials."""
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="test-token"
    )


@pytest.fixture
def mock_db_connection():
    """Create mock database connection."""
    return Mock()


@pytest.fixture
def app(mock_current_user, mock_note_service, mock_db_connection):
    """Create FastAPI test application with mocked dependencies."""
    app = FastAPI()

    async def mock_get_current_user():
        return mock_current_user

    # Override all dependencies
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_db_connection] = lambda: mock_db_connection
    app.dependency_overrides[NoteService] = lambda: mock_note_service

    app.include_router(
        note_router,
        prefix="/api"
    )
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_note_data():
    """Create valid note data."""
    return {
        "content": "Test Note",
        "activity_id": None,
        "moment_id": None,
        "attachments": None
    }


class TestNoteRouter:
    """Test cases for NoteRouter."""

    def test_create_note_success(
        self,
        client,
        mock_note_service,
        mock_current_user,
        mock_auth_credentials,
        valid_note_data,
        mock_db_connection,
    ):
        """Test successful note creation."""
        # Create a fixed datetime for testing
        current_time = datetime.now(timezone.utc)

        # Create a mock Note object that will be returned by the service
        mock_db_note = Mock()
        mock_db_note.id = 1
        mock_db_note.content = valid_note_data["content"]
        mock_db_note.user_id = mock_current_user.id
        mock_db_note.created_at = current_time
        mock_db_note.updated_at = None
        mock_db_note.activity_id = None
        mock_db_note.moment_id = None
        mock_db_note.attachments = []

        # Set up mock service to return the mock Note object
        mock_note_service.create_note.return_value = mock_db_note

        # Make request
        api_response = client.post(
            "/api/v1/notes",
            json=valid_note_data,
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        # Assertions
        assert api_response.status_code == 201
        response_data = api_response.json()["data"]
        assert response_data["id"] == mock_db_note.id
        assert response_data["content"] == mock_db_note.content
        assert response_data["user_id"] == mock_db_note.user_id
        assert "created_at" in response_data

        # Verify service call
        mock_note_service.create_note.assert_called_once()
        args = mock_note_service.create_note.call_args[0]
        assert isinstance(args[0], NoteCreate)
        assert args[0].content == valid_note_data["content"]
        assert args[1] == mock_current_user.id

    def test_delete_note_not_found(
        self,
        client,
        mock_note_service,
        mock_current_user,
        mock_auth_credentials,
    ):
        """Test deleting a non-existent note."""
        note_id = 999
        mock_note_service.delete_note.side_effect = HTTPException(
            status_code=404,
            detail="Note not found"  # Match this exact message
        )

        response = client.delete(
            f"/api/v1/notes/{note_id}",
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 404
        assert "Note not found" in response.json()["detail"]
        mock_note_service.delete_note.assert_called_once_with(
            note_id, mock_current_user.id
        )

    # ... more test cases following the same pattern ...
