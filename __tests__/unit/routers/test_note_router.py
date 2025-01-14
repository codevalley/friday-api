"""Test NoteRouter class."""

import pytest
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from unittest.mock import Mock
from sqlalchemy.orm import Session

from dependencies import get_current_user
from orm.UserModel import User
from routers.v1.NoteRouter import router as note_router
from schemas.pydantic.NoteSchema import (
    NoteResponse,
)
from services.NoteService import NoteService


@pytest.fixture
def mock_note_service():
    """Create mock NoteService."""
    service = Mock(spec=NoteService)

    # Mock the create_note method to return a proper response
    def mock_create_note(note_data, user_id):
        current_time = datetime.now(timezone.utc)
        return NoteResponse(
            id=1,
            content=note_data.content,
            user_id=user_id,
            created_at=current_time,
            updated_at=None,
            activity_id=None,
            moment_id=None,
            attachments=[],
        )

    # Set up the mock methods
    service.create_note = Mock(side_effect=mock_create_note)
    service.delete_note = (
        Mock()
    )  # Will be configured per test
    return service


@pytest.fixture
def mock_current_user():
    """Create mock current user."""
    return User(
        id="test_user",
        username="test_user",
        key_id="test-key-id",
        user_secret="test-secret-hash",
    )


@pytest.fixture
def mock_auth_credentials():
    """Create mock auth credentials."""
    return HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="test-token"
    )


@pytest.fixture
def valid_note_data():
    """Create valid note data."""
    return {
        "content": "Test Note",
        "activity_id": None,
        "moment_id": None,
        "attachments": [],
    }


@pytest.fixture
def app(mock_current_user, mock_note_service):
    """Create FastAPI test application with mocked dependencies."""
    app = FastAPI()

    async def mock_get_current_user():
        return mock_current_user

    app.dependency_overrides[
        get_current_user
    ] = mock_get_current_user
    app.dependency_overrides[
        NoteService
    ] = lambda: mock_note_service
    app.include_router(note_router, prefix="/api")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_user(test_db_session: Session):
    """Create a real user in the test database."""
    user = User(
        id="test_user",  # Match the ID we use in mock_current_user
        username="test_user",
        key_id="test-key-id",
        user_secret="test-secret-hash",
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


class TestNoteRouter:
    """Test cases for NoteRouter."""

    def test_create_note_success(
        self,
        client,
        mock_note_service,
        mock_current_user,
        mock_auth_credentials,
        valid_note_data,
        sample_user,
    ):
        """Test creating a note successfully."""
        mock_note_service.create_note.return_value = (
            valid_note_data
        )

        # Create note data
        note_data = {
            "content": "Test Note Content",
            "attachments": [],
        }

        response = client.post(
            "/api/v1/notes",
            json=note_data,
            headers={
                "Authorization": f"Bearer {mock_auth_credentials.credentials}"
            },
        )

        assert response.status_code == 201
        assert (
            response.json()["data"]["content"]
            == "Test Note Content"
        )
        mock_note_service.create_note.assert_called_once()

    def test_delete_note_success(
        self,
        client,
        mock_note_service,
        mock_current_user,
        mock_auth_credentials,
    ):
        """Test successful note deletion."""
        note_id = 1
        mock_note_service.delete_note.return_value = True

        response = client.delete(
            f"/api/v1/notes/{note_id}",
            headers={
                "Authorization": "Bearer "
                + mock_auth_credentials.credentials
            },
        )

        assert response.status_code == 200
        assert (
            response.json()["message"]
            == "Note deleted successfully"
        )
        mock_note_service.delete_note.assert_called_once_with(
            note_id, mock_current_user.id
        )

    def test_delete_note_not_found(
        self,
        client,
        mock_note_service,
        mock_current_user,
        mock_auth_credentials,
    ):
        """Test deleting a non-existent note."""
        note_id = 999
        error_message = "Note not found"

        # Use the exact error message from the service
        mock_note_service.delete_note.side_effect = (
            HTTPException(
                status_code=404, detail=error_message
            )
        )

        response = client.delete(
            f"/api/v1/notes/{note_id}",
            headers={
                "Authorization": "Bearer "
                + mock_auth_credentials.credentials
            },
        )

        assert response.status_code == 404
        # Split assertion to fix line length
        assert response.json()["detail"] == error_message
        mock_note_service.delete_note.assert_called_once_with(
            note_id, mock_current_user.id
        )

    def test_create_note_unauthenticated(
        self,
        client,
        mock_note_service,
        valid_note_data,
    ):
        """Test note creation without authentication."""
        response = client.post(
            "/api/v1/notes",
            json=valid_note_data,
        )

        assert response.status_code == 401
        response_data = response.json()
        assert (
            response_data["detail"]["code"]
            == "UNAUTHORIZED"
        )
        assert (
            "Invalid or missing authentication token"
            in response_data["detail"]["message"]
        )
        assert (
            response_data["detail"]["type"]
            == "AuthenticationError"
        )

    # ... more test cases following the same pattern ...
