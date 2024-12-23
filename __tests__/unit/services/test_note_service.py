"""Test NoteService class."""

import pytest
from unittest.mock import Mock
from datetime import datetime
from fastapi import HTTPException

from services.NoteService import NoteService
from schemas.pydantic.NoteSchema import NoteCreate
from domain.note import NoteData
from domain.exceptions import (
    NoteContentError,
    NoteAttachmentError,
    NoteReferenceError,
    NoteValidationError,
)


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


def test_create_note(
    note_service, mock_db_session, mock_note_repo
):
    """Test creating a note."""
    # Arrange
    note_data = NoteCreate(
        content="Test note", activity_id=1
    )
    user_id = "test-user-id"

    mock_note = NoteData(
        id=1,
        content="Test note",
        user_id=user_id,
        activity_id=1,
        created_at=datetime.utcnow(),
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
        attachments=[{"url": "test.jpg", "type": "image"}],
    )
    user_id = "test-user-id"

    mock_note = NoteData(
        id=1,
        content="Test note with attachment",
        user_id=user_id,
        activity_id=1,
        created_at=datetime.utcnow(),
        attachments=[{"url": "test.jpg", "type": "image"}],
    )

    mock_note_repo.create.return_value = mock_note

    # Act
    result = note_service.create_note(note_data, user_id)

    # Assert
    mock_note_repo.create.assert_called_once()
    assert result.content == "Test note with attachment"
    assert result.attachments[0]["url"] == "test.jpg"


def test_get_note(
    note_service, mock_db_session, mock_note_repo
):
    """Test getting a note."""
    # Arrange
    note_id = 1
    user_id = "test-user-id"

    mock_note = NoteData(
        id=note_id,
        content="Test note",
        user_id=user_id,
        created_at=datetime.utcnow(),
    )

    mock_note_repo.get_by_user.return_value = mock_note

    # Act
    result = note_service.get_note(note_id, user_id)

    # Assert
    mock_note_repo.get_by_user.assert_called_once_with(
        note_id, user_id
    )
    assert result.id == note_id
    assert result.content == "Test note"


def test_list_notes(
    note_service, mock_db_session, mock_note_repo
):
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
            created_at=datetime.utcnow(),
        ),
        NoteData(
            id=2,
            content="Note 2",
            user_id=user_id,
            created_at=datetime.utcnow(),
        ),
    ]

    mock_note_repo.list_notes.return_value = mock_notes
    mock_note_repo.count_user_notes.return_value = len(
        mock_notes
    )

    # Act
    result = note_service.list_notes(
        user_id, page=page, size=size
    )

    # Assert
    mock_note_repo.list_notes.assert_called_once()
    assert len(result["items"]) == 2
    assert result["total"] == 2
    assert result["page"] == page
    assert result["size"] == size


def test_create_note_invalid_content(
    note_service, mock_note_repo
):
    """Test creating note with invalid content."""
    # Arrange
    note_data = NoteCreate(
        content="x",  # Valid for Pydantic but will fail in service
        activity_id=1,
    )
    user_id = "test-user-id"

    mock_note_repo.create.side_effect = NoteContentError(
        "Note content is too short"
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        note_service.create_note(note_data, user_id)

    assert exc_info.value.status_code == 400
    assert "content" in str(exc_info.value.detail)


def test_create_note_invalid_attachment(
    note_service, mock_note_repo
):
    """Test creating note with invalid attachment."""
    # Arrange
    note_data = NoteCreate(
        content="Test note",
        activity_id=1,
        attachments=[
            {"url": "", "type": "invalid_type"}
        ],  # Invalid attachment
    )
    user_id = "test-user-id"

    mock_note_repo.create.side_effect = NoteAttachmentError(
        "Invalid attachment format"
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        note_service.create_note(note_data, user_id)

    assert exc_info.value.status_code == 422
    assert "attachment" in str(exc_info.value.detail)


def test_create_note_invalid_activity(
    note_service, mock_note_repo
):
    """Test creating note with invalid activity reference."""
    # Arrange
    note_data = NoteCreate(
        content="Test note",
        activity_id=999,  # Non-existent activity ID
    )
    user_id = "test-user-id"

    mock_note_repo.create.side_effect = NoteReferenceError(
        "Referenced activity does not exist"
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        note_service.create_note(note_data, user_id)

    assert exc_info.value.status_code == 400
    assert "activity" in str(exc_info.value.detail)


def test_create_note_unauthorized_user(
    note_service, mock_note_repo
):
    """Test creating note with unauthorized user."""
    # Arrange
    note_data = NoteCreate(
        content="Test note", activity_id=1
    )
    user_id = "unauthorized-user"

    mock_note_repo.create.side_effect = NoteValidationError(
        "User not authorized to create notes for this activity"
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        note_service.create_note(note_data, user_id)

    assert exc_info.value.status_code == 400
    assert "authorized" in str(exc_info.value.detail)


def test_update_note_not_found(
    note_service, mock_note_repo
):
    """Test updating a non-existent note."""
    # Arrange
    note_id = 999
    user_id = "test-user-id"
    update_data = {"content": "Updated content"}

    mock_note_repo.get_by_user.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        note_service.update_note(
            note_id, user_id, update_data
        )

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail)


def test_delete_note_not_found(
    note_service, mock_note_repo
):
    """Test deleting a non-existent note."""
    # Arrange
    note_id = 999
    user_id = "test-user-id"

    mock_note_repo.get_by_user.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        note_service.delete_note(note_id, user_id)

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail)
