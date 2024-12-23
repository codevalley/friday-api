"""Test NoteModel class."""

from datetime import datetime

from orm.NoteModel import Note
from domain.values import AttachmentType


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
        attachment_url=(
            "https://example.com/photo.jpg"
        ),
        attachment_type=AttachmentType.IMAGE,
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
        == AttachmentType.IMAGE
    )


def test_note_database_persistence(test_db_session, sample_user):
    """Test note persistence in database."""
    note = Note(
        user_id=sample_user.id,
        content="Test Note Content",
        attachment_url=(
            "https://example.com/doc.pdf"
        ),
        attachment_type=AttachmentType.DOCUMENT,
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
    assert saved_note.user_id == sample_user.id
    assert (
        saved_note.attachment_url
        == "https://example.com/doc.pdf"
    )
    assert (
        saved_note.attachment_type
        == AttachmentType.DOCUMENT
    )
    assert isinstance(saved_note.created_at, datetime)
    assert saved_note.updated_at is None


def test_note_relationships(test_db_session, sample_user):
    """Test note relationships with user."""
    note = Note(
        user_id=sample_user.id,
        content="Test Note Content",
    )
    test_db_session.add(note)
    test_db_session.commit()
    test_db_session.refresh(note)

    assert note.owner == sample_user
    assert note in sample_user.notes
