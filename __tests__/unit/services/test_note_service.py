"""Test NoteService class."""

import pytest
from unittest.mock import Mock
from datetime import datetime

from services.NoteService import NoteService
from schemas.pydantic.NoteSchema import (
    NoteCreate,
    NoteResponse,
)
from domain.note import NoteData


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    return session


@pytest.fixture
def mock_note_repo():
    """Create a mock note repository."""
    return Mock()


@pytest.fixture
def note_service(mock_db_session, mock_note_repo):
    """Create a note service with mocked session and repository."""
    service = NoteService()
    service.note_repo = mock_note_repo
    return service


def test_create_note(note_service, mock_db_session, mock_note_repo):
    """Test creating a note."""
    # Arrange
    note_data = NoteCreate(
        content="Test note",
        activity_id=1
    )
    user_id = "test-user-id"
    
    mock_note = NoteData(
        id=1,
        content="Test note",
        user_id=user_id,
        activity_id=1,
        created_at=datetime.utcnow()
    )
    
    mock_note_repo.create.return_value = mock_note
    
    # Act
    result = note_service.create_note(note_data, user_id)
    
    # Assert
    mock_note_repo.create.assert_called_once()
    assert result.content == "Test note"
    assert result.user_id == user_id


def test_create_note_with_attachment(
    note_service, mock_db_session, mock_note_repo
):
    """Test creating a note with attachment."""
    # Arrange
    note_data = NoteCreate(
        content="Test note with attachment",
        activity_id=1,
        attachments=[{"url": "test.jpg", "type": "image"}]
    )
    user_id = "test-user-id"
    
    mock_note = NoteData(
        id=1,
        content="Test note with attachment",
        user_id=user_id,
        activity_id=1,
        created_at=datetime.utcnow(),
        attachments=[{"url": "test.jpg", "type": "image"}]
    )
    
    mock_note_repo.create.return_value = mock_note
    
    # Act
    result = note_service.create_note(note_data, user_id)
    
    # Assert
    mock_note_repo.create.assert_called_once()
    assert result.content == "Test note with attachment"
    assert result.attachments[0]["url"] == "test.jpg"


def test_get_note(note_service, mock_db_session, mock_note_repo):
    """Test getting a note."""
    # Arrange
    note_id = 1
    user_id = "test-user-id"
    
    mock_note = NoteData(
        id=note_id,
        content="Test note",
        user_id=user_id,
        created_at=datetime.utcnow()
    )
    
    mock_note_repo.get_by_user.return_value = mock_note
    
    # Act
    result = note_service.get_note(
        note_id,
        user_id
    )
    
    # Assert
    mock_note_repo.get_by_user.assert_called_once_with(note_id, user_id)
    assert result.id == note_id
    assert result.content == "Test note"


def test_list_notes(note_service, mock_db_session, mock_note_repo):
    """Test listing notes."""
    # Arrange
    user_id = "test-user-id"
    page = 1
    size = 10
    
    mock_notes = [
        NoteData(
            id=1,
            content="Note 1",
            user_id=user_id,
            created_at=datetime.utcnow()
        ),
        NoteData(
            id=2,
            content="Note 2",
            user_id=user_id,
            created_at=datetime.utcnow()
        )
    ]
    
    mock_note_repo.list_notes.return_value = mock_notes
    mock_note_repo.count_user_notes.return_value = len(mock_notes)
    
    # Act
    result = note_service.list_notes(user_id, page=page, size=size)
    
    # Assert
    mock_note_repo.list_notes.assert_called_once()
    assert len(result["items"]) == 2
    assert result["total"] == 2
    assert result["page"] == page
    assert result["size"] == size
