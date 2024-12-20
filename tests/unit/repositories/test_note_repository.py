"""Test NoteRepository class."""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from domain.note import NoteData, AttachmentType
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
def note_repository(
    test_db_session: Session,
) -> NoteRepository:
    """Create a note repository instance."""
    return NoteRepository(test_db_session)


def test_create_note(
    note_repository: NoteRepository, test_user: User
):
    """Test creating a note."""
    note_data = NoteData(
        content="Test Note Content",
        user_id=test_user.id,
    )
    created_note = note_repository.create(note_data)

    assert created_note.id is not None
    assert created_note.content == "Test Note Content"
    assert created_note.user_id == test_user.id
    assert created_note.attachment_url is None
    assert created_note.attachment_type is None


def test_create_note_with_attachment(
    note_repository: NoteRepository, test_user: User
):
    """Test creating a note with attachment."""
    note_data = NoteData(
        content="Test Note with Photo",
        user_id=test_user.id,
        attachment_url="https://example.com/photo.jpg",
        attachment_type=AttachmentType.PHOTO,
    )
    created_note = note_repository.create(note_data)

    assert created_note.id is not None
    assert created_note.content == "Test Note with Photo"
    assert (
        created_note.attachment_url
        == "https://example.com/photo.jpg"
    )
    assert (
        created_note.attachment_type == AttachmentType.PHOTO
    )


def test_get_note(
    note_repository: NoteRepository, test_user: User
):
    """Test retrieving a note."""
    # Create a note first
    note_data = NoteData(
        content="Test Note Content",
        user_id=test_user.id,
    )
    created_note = note_repository.create(note_data)

    # Retrieve the note
    retrieved_note = note_repository.get(created_note.id)
    assert retrieved_note is not None
    assert retrieved_note.id == created_note.id
    assert retrieved_note.content == "Test Note Content"


def test_get_nonexistent_note(
    note_repository: NoteRepository,
):
    """Test retrieving a non-existent note."""
    retrieved_note = note_repository.get(999)
    assert retrieved_note is None


def test_list_notes(
    note_repository: NoteRepository, test_user: User
):
    """Test listing notes."""
    # Create multiple notes
    for i in range(3):
        note_data = NoteData(
            content=f"Test Note {i}",
            user_id=test_user.id,
        )
        note_repository.create(note_data)

    # List notes
    notes = note_repository.list(user_id=test_user.id)
    assert len(notes) == 3
    for i, note in enumerate(notes):
        assert note.content == f"Test Note {i}"
        assert note.user_id == test_user.id


def test_list_notes_with_pagination(
    note_repository: NoteRepository, test_user: User
):
    """Test listing notes with pagination."""
    # Create multiple notes
    for i in range(5):
        note_data = NoteData(
            content=f"Test Note {i}",
            user_id=test_user.id,
        )
        note_repository.create(note_data)

    # Test first page
    page1 = note_repository.list(
        user_id=test_user.id, page=1, size=2
    )
    assert len(page1) == 2
    assert page1[0].content == "Test Note 0"
    assert page1[1].content == "Test Note 1"

    # Test second page
    page2 = note_repository.list(
        user_id=test_user.id, page=2, size=2
    )
    assert len(page2) == 2
    assert page2[0].content == "Test Note 2"
    assert page2[1].content == "Test Note 3"

    # Test last page
    page3 = note_repository.list(
        user_id=test_user.id, page=3, size=2
    )
    assert len(page3) == 1
    assert page3[0].content == "Test Note 4"


def test_update_note(
    note_repository: NoteRepository, test_user: User
):
    """Test updating a note."""
    # Create a note first
    note_data = NoteData(
        content="Original Content",
        user_id=test_user.id,
    )
    created_note = note_repository.create(note_data)

    # Update the note
    updated_data = NoteData(
        id=created_note.id,
        content="Updated Content",
        user_id=test_user.id,
        attachment_url="https://example.com/photo.jpg",
        attachment_type=AttachmentType.PHOTO,
    )
    updated_note = note_repository.update(updated_data)

    assert updated_note.id == created_note.id
    assert updated_note.content == "Updated Content"
    assert (
        updated_note.attachment_url
        == "https://example.com/photo.jpg"
    )
    assert (
        updated_note.attachment_type == AttachmentType.PHOTO
    )
    assert isinstance(updated_note.updated_at, datetime)


def test_delete_note(
    note_repository: NoteRepository, test_user: User
):
    """Test deleting a note."""
    # Create a note first
    note_data = NoteData(
        content="Test Note to Delete",
        user_id=test_user.id,
    )
    created_note = note_repository.create(note_data)

    # Delete the note
    note_repository.delete(created_note.id)

    # Verify note is deleted
    deleted_note = note_repository.get(created_note.id)
    assert deleted_note is None


def test_list_notes_by_user(
    note_repository: NoteRepository, test_user: User
):
    """Test listing notes for a specific user."""
    # Create another user
    other_user = User(
        username="otheruser",
        key_id="other-key-id",
        user_secret="other-secret",
    )
    note_repository.session.add(other_user)
    note_repository.session.commit()

    # Create notes for both users
    for i in range(2):
        # Notes for test_user
        note_data = NoteData(
            content=f"Test User Note {i}",
            user_id=test_user.id,
        )
        note_repository.create(note_data)

        # Notes for other_user
        note_data = NoteData(
            content=f"Other User Note {i}",
            user_id=other_user.id,
        )
        note_repository.create(note_data)

    # List notes for test_user
    test_user_notes = note_repository.list(
        user_id=test_user.id
    )
    assert len(test_user_notes) == 2
    for note in test_user_notes:
        assert note.user_id == test_user.id
        assert "Test User Note" in note.content

    # List notes for other_user
    other_user_notes = note_repository.list(
        user_id=other_user.id
    )
    assert len(other_user_notes) == 2
    for note in other_user_notes:
        assert note.user_id == other_user.id
        assert "Other User Note" in note.content
