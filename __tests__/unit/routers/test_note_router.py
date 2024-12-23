"""Test NoteRouter class."""

import pytest
from unittest.mock import Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime

from routers.v1.NoteRouter import router as note_router
from services.NoteService import NoteService
from schemas.pydantic.NoteSchema import NoteResponse
from dependencies import get_current_user
from orm.UserModel import User


@pytest.fixture
def mock_note_service():
    """Create a mock note service."""
    return Mock(spec=NoteService)


@pytest.fixture
def test_user(test_db_session):
    """Create a test user."""
    user = User(
        username="testuser",
        key_id="test-key-id",
        user_secret="test-secret",
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def test_app(mock_note_service, test_user):
    """Create a test FastAPI application."""
    app = FastAPI()
    app.include_router(note_router)

    # Override dependencies
    def get_note_service():
        return mock_note_service

    def mock_current_user():
        return test_user

    app.dependency_overrides[NoteService] = get_note_service
    app.dependency_overrides[get_current_user] = mock_current_user
    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client."""
    return TestClient(test_app)


def test_create_note(test_client, mock_note_service, test_user):
    """Test creating a note."""
    # Setup mock
    created_at = datetime.utcnow()
    mock_note_service.create_note.return_value = NoteResponse(
        id=1,
        content="Test Note",
        user_id=test_user.id,
        created_at=created_at,
        updated_at=None,
        attachment_url=None,
        attachment_type=None,
        attachments=None,
    )

    # Create note
    response = test_client.post(
        "/v1/notes",
        json={"content": "Test Note"},
        headers={"Authorization": "Bearer test-token"},
    )

    # Verify
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["id"] == 1
    assert data["content"] == "Test Note"
    assert data["user_id"] == test_user.id


def test_create_note_with_attachment(test_client, mock_note_service):
    """Test creating a note with attachment."""
    # Setup mock
    created_at = datetime.utcnow()
    mock_note_service.create_note.return_value = NoteResponse(
        id=1,
        content="Test Note",
        user_id="test-user-id",
        created_at=created_at,
        updated_at=None,
        activity_id=None,
        moment_id=None,
        attachments=[{
            "url": "https://example.com/photo.jpg",
            "type": "image",
        }],
    )

    # Create note
    response = test_client.post(
        "/v1/notes",
        json={
            "content": "Test Note",
            "attachments": [{
                "url": "https://example.com/photo.jpg",
                "type": "image",
            }],
        },
        headers={"Authorization": "Bearer test-token"},
    )

    # Verify
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["id"] == 1
    assert data["content"] == "Test Note"
    assert data["attachments"][0]["url"] == (
        "https://example.com/photo.jpg"
    )


def test_get_note(test_client, mock_note_service, test_user):
    """Test getting a note."""
    # Setup mock
    created_at = datetime.utcnow()
    mock_note_service.get_note.return_value = NoteResponse(
        id=1,
        content="Test Note",
        user_id=test_user.id,
        created_at=created_at,
        updated_at=None,
    )

    # Get note
    response = test_client.get(
        "/v1/notes/1",
        headers={"Authorization": "Bearer test-token"},
    )

    # Verify
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == 1
    assert data["content"] == "Test Note"


def test_list_notes(test_client, mock_note_service):
    """Test listing notes."""
    # Setup mock
    mock_note_service.list_notes.return_value = {
        "items": [
            {
                "id": 1,
                "content": "Test Note 1",
                "user_id": "test-user-id",
            },
            {
                "id": 2,
                "content": "Test Note 2",
                "user_id": "test-user-id",
            },
        ],
        "total": 2,
    }

    # List notes
    response = test_client.get(
        "/v1/notes",
        headers={"Authorization": "Bearer test-token"},
    )

    # Verify
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    assert len(data["items"]) == 2
