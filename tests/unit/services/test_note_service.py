"""Test NoteService class."""

import pytest
from datetime import datetime
from unittest.mock import Mock
from sqlalchemy.orm import Session

from domain.note import NoteData, AttachmentType
from services.NoteService import NoteService
from repositories.NoteRepository import NoteRepository
from orm.UserModel import User


@pytest.fixture
def test_user(test_db_session: Session) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        key_id="test-key-id",
        user_secret="test-secret",
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def mock_note_repository():
    """Create a mock note repository."""
    return Mock(spec=NoteRepository)


@pytest.fixture
def note_service(mock_note_repository):
    """Create a note service instance with mocked repository."""
    return NoteService(mock_note_repository)


def test_create_note(
    note_service, mock_note_repository, test_user
):
    """Test creating a note."""
    note_data = NoteData(
        content="Test Note Content",
        user_id=test_user.id,
    )

    # Mock repository create method
    mock_note_repository.create.return_value = NoteData(
        id=1,
        content="Test Note Content",
        user_id=test_user.id,
        created_at=datetime.utcnow(),
    )

    created_note = note_service.create_note(note_data)

    assert created_note.id == 1
    assert created_note.content == "Test Note Content"
    assert created_note.user_id == test_user.id
    mock_note_repository.create.assert_called_once_with(
        note_data
    )


def test_create_note_with_attachment(
    note_service, mock_note_repository, test_user
):
    """Test creating a note with attachment."""
    note_data = NoteData(
        content="Test Note with Photo",
        user_id=test_user.id,
        attachment_url="https://example.com/photo.jpg",
        attachment_type=AttachmentType.PHOTO,
    )

    # Mock repository create method
    mock_note_repository.create.return_value = NoteData(
        id=1,
        content="Test Note with Photo",
        user_id=test_user.id,
        attachment_url="https://example.com/photo.jpg",
        attachment_type=AttachmentType.PHOTO,
        created_at=datetime.utcnow(),
    )

    created_note = note_service.create_note(note_data)

    assert created_note.id == 1
    assert created_note.content == "Test Note with Photo"
    assert (
        created_note.attachment_url
        == "https://example.com/photo.jpg"
    )
    assert (
        created_note.attachment_type == AttachmentType.PHOTO
    )
    mock_note_repository.create.assert_called_once_with(
        note_data
    )


def test_get_note(
    note_service, mock_note_repository, test_user
):
    """Test retrieving a note."""
    # Mock repository get method
    mock_note_repository.get.return_value = NoteData(
        id=1,
        content="Test Note Content",
        user_id=test_user.id,
        created_at=datetime.utcnow(),
    )

    note = note_service.get_note(1)

    assert note.id == 1
    assert note.content == "Test Note Content"
    assert note.user_id == test_user.id
    mock_note_repository.get.assert_called_once_with(1)


def test_get_nonexistent_note(
    note_service, mock_note_repository
):
    """Test retrieving a non-existent note."""
    # Mock repository get method to return None
    mock_note_repository.get.return_value = None

    note = note_service.get_note(999)
    assert note is None
    mock_note_repository.get.assert_called_once_with(999)


def test_list_notes(
    note_service, mock_note_repository, test_user
):
    """Test listing notes."""
    # Mock repository list method
    mock_notes = [
        NoteData(
            id=i,
            content=f"Test Note {i}",
            user_id=test_user.id,
            created_at=datetime.utcnow(),
        )
        for i in range(3)
    ]
    mock_note_repository.list.return_value = mock_notes

    notes = note_service.list_notes(user_id=test_user.id)

    assert len(notes) == 3
    for i, note in enumerate(notes):
        assert note.id == i
        assert note.content == f"Test Note {i}"
        assert note.user_id == test_user.id
    mock_note_repository.list.assert_called_once_with(
        user_id=test_user.id, page=1, size=50
    )


def test_list_notes_with_pagination(
    note_service, mock_note_repository, test_user
):
    """Test listing notes with pagination."""
    # Mock repository list method
    mock_notes = [
        NoteData(
            id=i,
            content=f"Test Note {i}",
            user_id=test_user.id,
            created_at=datetime.utcnow(),
        )
        for i in range(2)
    ]
    mock_note_repository.list.return_value = mock_notes

    notes = note_service.list_notes(
        user_id=test_user.id, page=2, size=2
    )

    assert len(notes) == 2
    mock_note_repository.list.assert_called_once_with(
        user_id=test_user.id, page=2, size=2
    )


def test_update_note(
    note_service, mock_note_repository, test_user
):
    """Test updating a note."""
    # Mock repository get and update methods
    mock_note_repository.get.return_value = NoteData(
        id=1,
        content="Original Content",
        user_id=test_user.id,
        created_at=datetime.utcnow(),
    )

    updated_data = NoteData(
        id=1,
        content="Updated Content",
        user_id=test_user.id,
        attachment_url="https://example.com/photo.jpg",
        attachment_type=AttachmentType.PHOTO,
    )

    mock_note_repository.update.return_value = NoteData(
        id=1,
        content="Updated Content",
        user_id=test_user.id,
        attachment_url="https://example.com/photo.jpg",
        attachment_type=AttachmentType.PHOTO,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    updated_note = note_service.update_note(1, updated_data)

    assert updated_note.id == 1
    assert updated_note.content == "Updated Content"
    assert (
        updated_note.attachment_url
        == "https://example.com/photo.jpg"
    )
    assert (
        updated_note.attachment_type == AttachmentType.PHOTO
    )
    mock_note_repository.update.assert_called_once_with(
        updated_data
    )


def test_update_nonexistent_note(
    note_service, mock_note_repository, test_user
):
    """Test updating a non-existent note."""
    # Mock repository get method to return None
    mock_note_repository.get.return_value = None

    updated_data = NoteData(
        id=999,
        content="Updated Content",
        user_id=test_user.id,
    )

    with pytest.raises(ValueError, match="Note not found"):
        note_service.update_note(999, updated_data)

    mock_note_repository.get.assert_called_once_with(999)
    mock_note_repository.update.assert_not_called()


def test_delete_note(
    note_service, mock_note_repository, test_user
):
    """Test deleting a note."""
    # Mock repository get method
    mock_note_repository.get.return_value = NoteData(
        id=1,
        content="Test Note",
        user_id=test_user.id,
        created_at=datetime.utcnow(),
    )

    note_service.delete_note(1)

    mock_note_repository.get.assert_called_once_with(1)
    mock_note_repository.delete.assert_called_once_with(1)


def test_delete_nonexistent_note(
    note_service, mock_note_repository
):
    """Test deleting a non-existent note."""
    # Mock repository get method to return None
    mock_note_repository.get.return_value = None

    with pytest.raises(ValueError, match="Note not found"):
        note_service.delete_note(999)

    mock_note_repository.get.assert_called_once_with(999)
    mock_note_repository.delete.assert_not_called()


def test_validate_note_ownership(
    note_service, mock_note_repository, test_user
):
    """Test note ownership validation."""
    # Mock repository get method
    mock_note_repository.get.return_value = NoteData(
        id=1,
        content="Test Note",
        user_id=test_user.id,
        created_at=datetime.utcnow(),
    )

    # Should not raise an exception for correct owner
    note_service.validate_note_ownership(1, test_user.id)

    # Should raise an exception for different user
    with pytest.raises(ValueError, match="Note not found"):
        note_service.validate_note_ownership(
            1, "different-user-id"
        )

    mock_note_repository.get.assert_called_with(1)
