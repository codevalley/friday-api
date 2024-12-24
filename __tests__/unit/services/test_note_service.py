"""Test suite for NoteService."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock
from fastapi import HTTPException

from services.NoteService import NoteService
from schemas.pydantic.NoteSchema import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
)


@pytest.fixture
def note_service(test_db_session):
    """Create NoteService instance with test database session."""
    return NoteService(db=test_db_session)


@pytest.fixture
def valid_note_data():
    """Return valid note data for testing."""
    return {
        "content": "Test Note",
        "activity_id": None,
        "moment_id": None,
        "attachments": None,
    }


@pytest.fixture
def mock_note():
    """Create a mock note for testing."""
    note = Mock()
    note.id = 1
    note.user_id = "test_user"
    note.content = "Test content"
    note.created_at = datetime.now(timezone.utc)
    note.updated_at = None
    note.activity_id = None
    note.moment_id = None
    note.attachments = []
    return note


class TestNoteService:
    """Test suite for NoteService."""

    def test_create_note_success(
        self, note_service, valid_note_data, mock_note
    ):
        """Test successful note creation."""
        # Setup mocks
        note_service.note_repo.create = Mock(
            return_value=mock_note
        )

        # Create note
        note_data = NoteCreate(**valid_note_data)
        result = note_service.create_note(
            note_data, "test_user"
        )

        assert isinstance(result, NoteResponse)
        assert result.id == mock_note.id
        assert result.content == mock_note.content

    def test_create_note_invalid_content(
        self, note_service, valid_note_data
    ):
        """Test note creation with invalid content."""
        # Setup mocks with a Mock object that has side_effect
        mock_create = Mock()
        mock_create.side_effect = HTTPException(
            status_code=400,
            detail="Note content cannot be empty",
        )
        note_service.note_repo.create = mock_create

        # Create note with invalid content
        note_data = NoteCreate(**valid_note_data)
        with pytest.raises(HTTPException) as exc:
            note_service.create_note(note_data, "test_user")
        assert exc.value.status_code == 400
        assert "content" in str(exc.value.detail)

    def test_get_note_success(
        self, note_service, mock_note
    ):
        """Test successful note retrieval."""
        # Setup mocks
        note_service.note_repo.get_by_user = Mock(
            return_value=mock_note
        )

        result = note_service.get_note(1, "test_user")
        assert isinstance(result, NoteResponse)
        assert result.id == mock_note.id
        note_service.note_repo.get_by_user.assert_called_once_with(
            1, "test_user"
        )

    def test_get_note_not_found(self, note_service):
        """Test note retrieval when not found."""
        note_service.note_repo.get = Mock(return_value=None)

        with pytest.raises(HTTPException) as exc:
            note_service.get_note(1, "test_user")
        assert exc.value.status_code == 404
        assert "Note not found" in exc.value.detail

    def test_update_note_success(
        self, note_service, mock_note
    ):
        """Test successful note update."""
        note_service.note_repo.get_by_user = Mock(
            return_value=mock_note
        )
        note_service.note_repo.update = Mock(
            return_value=mock_note
        )

        update_data = NoteUpdate(content="Updated content")
        result = note_service.update_note(
            1, "test_user", update_data
        )

        assert isinstance(result, NoteResponse)
        assert result.id == mock_note.id

    def test_update_note_unauthorized(
        self, note_service, mock_note
    ):
        """Test updating note without authorization."""
        note_service.note_repo.get_by_user = Mock(
            return_value=None
        )

        update_data = NoteUpdate(content="Updated content")
        with pytest.raises(HTTPException) as exc:
            note_service.update_note(
                1, "wrong_user", update_data
            )
        assert exc.value.status_code == 404
        assert "Note not found" in exc.value.detail

    def test_delete_note_success(
        self, note_service, mock_note
    ):
        """Test successful note deletion."""
        note_service.note_repo.get_by_user = Mock(
            return_value=mock_note
        )
        note_service.note_repo.delete = Mock(
            return_value=True
        )

        result = note_service.delete_note(1, "test_user")
        assert result is True

    def test_delete_note_unauthorized(self, note_service):
        """Test deleting note without authorization."""
        note_service.note_repo.get_by_user = Mock(
            return_value=None
        )

        with pytest.raises(HTTPException) as exc:
            note_service.delete_note(1, "wrong_user")
        assert exc.value.status_code == 404
        assert "Note not found" in exc.value.detail
