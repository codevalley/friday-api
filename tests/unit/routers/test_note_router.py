"""Test NoteRouter class."""

import pytest
from datetime import datetime
from unittest.mock import Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.note import NoteData, AttachmentType
from routers.v1.NoteRouter import router as note_router
from services.NoteService import NoteService


@pytest.fixture
def mock_note_service():
    """Create a mock note service."""
    return Mock(spec=NoteService)


@pytest.fixture
def test_app(mock_note_service):
    """Create a test FastAPI application."""
    app = FastAPI()
    app.include_router(note_router)

    # Override note service dependency
    def get_note_service():
        return mock_note_service

    app.dependency_overrides[NoteService] = get_note_service
    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client."""
    return TestClient(test_app)


def test_create_note(test_client, mock_note_service):
    """Test creating a note."""
    # Mock service create_note method
    mock_note_service.create_note.return_value = NoteData(
        id=1,
        content="Test Note Content",
        user_id="test-user-id",
        created_at=datetime.utcnow(),
    )

    response = test_client.post(
        "/v1/notes",
        json={
            "content": "Test Note Content",
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == 1
    assert data["content"] == "Test Note Content"
    assert data["user_id"] == "test-user-id"
    assert data["attachment_url"] is None
    assert data["attachment_type"] is None


def test_create_note_with_attachment(
    test_client, mock_note_service
):
    """Test creating a note with attachment."""
    # Mock service create_note method
    mock_note_service.create_note.return_value = NoteData(
        id=1,
        content="Test Note with Photo",
        user_id="test-user-id",
        attachment_url="https://example.com/photo.jpg",
        attachment_type=AttachmentType.PHOTO,
        created_at=datetime.utcnow(),
    )

    response = test_client.post(
        "/v1/notes",
        json={
            "content": "Test Note with Photo",
            "attachment_url": "https://example.com/photo.jpg",
            "attachment_type": "PHOTO",
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == 1
    assert data["content"] == "Test Note with Photo"
    assert (
        data["attachment_url"]
        == "https://example.com/photo.jpg"
    )
    assert data["attachment_type"] == "PHOTO"


def test_get_note(test_client, mock_note_service):
    """Test retrieving a note."""
    # Mock service get_note method
    mock_note_service.get_note.return_value = NoteData(
        id=1,
        content="Test Note Content",
        user_id="test-user-id",
        created_at=datetime.utcnow(),
    )

    response = test_client.get(
        "/v1/notes/1",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == 1
    assert data["content"] == "Test Note Content"
    assert data["user_id"] == "test-user-id"


def test_get_nonexistent_note(
    test_client, mock_note_service
):
    """Test retrieving a non-existent note."""
    # Mock service get_note method to return None
    mock_note_service.get_note.return_value = None

    response = test_client.get(
        "/v1/notes/999",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"


def test_list_notes(test_client, mock_note_service):
    """Test listing notes."""
    # Mock service list_notes method
    mock_notes = [
        NoteData(
            id=i,
            content=f"Test Note {i}",
            user_id="test-user-id",
            created_at=datetime.utcnow(),
        )
        for i in range(3)
    ]
    mock_note_service.list_notes.return_value = mock_notes

    response = test_client.get(
        "/v1/notes",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3
    for i, note in enumerate(data):
        assert note["id"] == i
        assert note["content"] == f"Test Note {i}"
        assert note["user_id"] == "test-user-id"


def test_list_notes_with_pagination(
    test_client, mock_note_service
):
    """Test listing notes with pagination."""
    # Mock service list_notes method
    mock_notes = [
        NoteData(
            id=i,
            content=f"Test Note {i}",
            user_id="test-user-id",
            created_at=datetime.utcnow(),
        )
        for i in range(2)
    ]
    mock_note_service.list_notes.return_value = mock_notes

    response = test_client.get(
        "/v1/notes?page=2&size=2",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    mock_note_service.list_notes.assert_called_once_with(
        user_id="test-user-id", page=2, size=2
    )


def test_update_note(test_client, mock_note_service):
    """Test updating a note."""
    # Mock service update_note method
    mock_note_service.update_note.return_value = NoteData(
        id=1,
        content="Updated Content",
        user_id="test-user-id",
        attachment_url="https://example.com/photo.jpg",
        attachment_type=AttachmentType.PHOTO,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    response = test_client.put(
        "/v1/notes/1",
        json={
            "content": "Updated Content",
            "attachment_url": "https://example.com/photo.jpg",
            "attachment_type": "PHOTO",
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == 1
    assert data["content"] == "Updated Content"
    assert (
        data["attachment_url"]
        == "https://example.com/photo.jpg"
    )
    assert data["attachment_type"] == "PHOTO"


def test_update_nonexistent_note(
    test_client, mock_note_service
):
    """Test updating a non-existent note."""
    # Mock service update_note method to raise ValueError
    mock_note_service.update_note.side_effect = ValueError(
        "Note not found"
    )

    response = test_client.put(
        "/v1/notes/999",
        json={"content": "Updated Content"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"


def test_delete_note(test_client, mock_note_service):
    """Test deleting a note."""
    response = test_client.delete(
        "/v1/notes/1",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert (
        response.json()["data"]["message"]
        == "Note deleted successfully"
    )
    mock_note_service.delete_note.assert_called_once_with(1)


def test_delete_nonexistent_note(
    test_client, mock_note_service
):
    """Test deleting a non-existent note."""
    # Mock service delete_note method to raise ValueError
    mock_note_service.delete_note.side_effect = ValueError(
        "Note not found"
    )

    response = test_client.delete(
        "/v1/notes/999",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"


def test_unauthorized_access(test_client):
    """Test accessing endpoints without authorization."""
    endpoints = [
        ("GET", "/v1/notes"),
        ("POST", "/v1/notes"),
        ("GET", "/v1/notes/1"),
        ("PUT", "/v1/notes/1"),
        ("DELETE", "/v1/notes/1"),
    ]

    for method, endpoint in endpoints:
        response = test_client.request(method, endpoint)
        assert response.status_code == 401
        assert (
            "Not authenticated" in response.json()["detail"]
        )
