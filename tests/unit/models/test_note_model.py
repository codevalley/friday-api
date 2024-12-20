"""Test NoteModel class."""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from orm.NoteModel import Note
from orm.UserModel import User
from domain.note import AttachmentType


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
def test_note(
    test_db_session: Session, test_user: User
) -> Note:
    """Create a test note."""
    note = Note(
        user_id=test_user.id,
        content="Test Note Content",
        attachment_url=None,
        attachment_type=None,
    )
    test_db_session.add(note)
    test_db_session.commit()
    return note


def test_note_initialization():
    """Test basic note model initialization."""
    # Test note without attachment
    note = Note(
        user_id="test-user-id",
        content="Test Note Content",
    )
    assert note.content == "Test Note Content"
    assert note.attachment_url is None
    assert note.attachment_type is None

    # Test note with attachment
    note_with_attachment = Note(
        user_id="test-user-id",
        content="Test Note with Attachment",
        attachment_url="https://example.com/photo.jpg",
        attachment_type=AttachmentType.PHOTO,
    )
    assert (
        note_with_attachment.content
        == "Test Note with Attachment"
    )
    assert (
        note_with_attachment.attachment_url
        == "https://example.com/photo.jpg"
    )
    assert (
        note_with_attachment.attachment_type
        == AttachmentType.PHOTO
    )


def test_note_database_persistence(
    test_db_session: Session, test_user: User
):
    """Test note persistence in database."""
    note = Note(
        user_id=test_user.id,
        content="Test Note Content",
        attachment_url="https://example.com/voice.mp3",
        attachment_type=AttachmentType.VOICE,
    )
    test_db_session.add(note)
    test_db_session.commit()
    test_db_session.refresh(note)

    saved_note = (
        test_db_session.query(Note)
        .filter(Note.id == note.id)
        .first()
    )
    assert saved_note is not None
    assert saved_note.content == "Test Note Content"
    assert saved_note.user_id == test_user.id
    assert (
        saved_note.attachment_url
        == "https://example.com/voice.mp3"
    )
    assert (
        saved_note.attachment_type == AttachmentType.VOICE
    )
    assert isinstance(saved_note.created_at, datetime)
    assert saved_note.updated_at is None


def test_note_relationships(
    test_db_session: Session, test_note: Note
):
    """Test note relationships with user."""
    assert test_note.user is not None
    assert test_note.user.username == "testuser"


def test_note_content_required(
    test_db_session: Session, test_user: User
):
    """Test that note content is required."""
    with pytest.raises(IntegrityError):
        note = Note(
            user_id=test_user.id,
            content=None,
        )
        test_db_session.add(note)
        test_db_session.commit()


def test_attachment_type_validation(
    test_db_session: Session, test_user: User
):
    """Test attachment type validation."""
    # Test valid attachment types
    valid_types = [
        (
            AttachmentType.PHOTO,
            "https://example.com/photo.jpg",
        ),
        (
            AttachmentType.VIDEO,
            "https://example.com/video.mp4",
        ),
        (
            AttachmentType.VOICE,
            "https://example.com/voice.mp3",
        ),
        (
            AttachmentType.FILE,
            "https://example.com/document.pdf",
        ),
    ]

    for attachment_type, url in valid_types:
        note = Note(
            user_id=test_user.id,
            content=f"Test Note with {attachment_type.value}",
            attachment_url=url,
            attachment_type=attachment_type,
        )
        test_db_session.add(note)
        test_db_session.commit()
        assert note.attachment_type == attachment_type
        assert note.attachment_url == url

    # Test invalid attachment type
    with pytest.raises(ValueError):
        Note(
            user_id=test_user.id,
            content="Test Note with Invalid Type",
            attachment_url="https://example.com/file",
            attachment_type="INVALID_TYPE",
        )


def test_attachment_url_validation(
    test_db_session: Session, test_user: User
):
    """Test attachment URL validation."""
    # Test that attachment_url is required when attachment_type is set
    with pytest.raises(ValueError):
        note = Note(
            user_id=test_user.id,
            content="Test Note",
            attachment_type=AttachmentType.PHOTO,
            attachment_url=None,
        )
        test_db_session.add(note)
        test_db_session.commit()

    # Test that attachment_type is required when attachment_url is set
    with pytest.raises(ValueError):
        note = Note(
            user_id=test_user.id,
            content="Test Note",
            attachment_url="https://example.com/photo.jpg",
            attachment_type=None,
        )
        test_db_session.add(note)
        test_db_session.commit()


def test_note_update(
    test_db_session: Session, test_note: Note
):
    """Test note update functionality."""
    # Update content only
    test_note.content = "Updated content"
    test_db_session.commit()
    test_db_session.refresh(test_note)
    assert test_note.content == "Updated content"
    assert isinstance(test_note.updated_at, datetime)

    # Update with attachment
    test_note.attachment_url = (
        "https://example.com/photo.jpg"
    )
    test_note.attachment_type = AttachmentType.PHOTO
    test_db_session.commit()
    test_db_session.refresh(test_note)
    assert (
        test_note.attachment_url
        == "https://example.com/photo.jpg"
    )
    assert test_note.attachment_type == AttachmentType.PHOTO


def test_user_notes_relationship(
    test_db_session: Session, test_user: User
):
    """Test relationship between user and notes."""
    # Create multiple notes for the user
    notes = []
    for i in range(3):
        note = Note(
            user_id=test_user.id,
            content=f"Test Note {i}",
        )
        notes.append(note)
        test_db_session.add(note)
    test_db_session.commit()

    # Verify notes are associated with the user
    user_notes = (
        test_db_session.query(Note)
        .filter(Note.user_id == test_user.id)
        .all()
    )
    assert len(user_notes) == 3
    for i, note in enumerate(user_notes):
        assert note.content == f"Test Note {i}"
        assert note.user_id == test_user.id
