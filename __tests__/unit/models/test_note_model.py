"""Test NoteModel class."""

from orm.NoteModel import Note
from domain.values import ProcessingStatus


def test_note_initialization():
    """Test basic note model initialization."""
    # Test note without attachments
    note = Note(
        user_id="test-user-id",
        content="Test Note Content",
        attachments=[],
    )
    assert note.content == "Test Note Content"
    assert note.attachments == []
    assert (
        note.processing_status == ProcessingStatus.PENDING
    )

    # Test note with attachments
    note_with_attachments = Note(
        user_id="test-user-id",
        content="Test Note with Attachments",
        attachments=[
            {
                "url": "https://example.com/photo.jpg",
                "type": "image",
                "name": "photo.jpg",
            }
        ],
    )
    assert (
        note_with_attachments.content
        == "Test Note with Attachments"
    )
    assert len(note_with_attachments.attachments) == 1
    assert (
        note_with_attachments.attachments[0]["url"]
        == "https://example.com/photo.jpg"
    )
    assert (
        note_with_attachments.attachments[0]["type"]
        == "image"
    )


def test_note_database_persistence(
    test_db_session, sample_user
):
    """Test note persistence in database."""
    note = Note(
        user_id=sample_user.id,
        content="Test Note Content",
        attachments=[
            {
                "url": "https://example.com/doc.pdf",
                "type": "document",
                "name": "doc.pdf",
            }
        ],
    )

    test_db_session.add(note)
    test_db_session.commit()

    # Verify note was saved
    saved_note = (
        test_db_session.query(Note)
        .filter_by(id=note.id)
        .first()
    )
    assert saved_note is not None
    assert saved_note.content == "Test Note Content"
    assert len(saved_note.attachments) == 1
    assert (
        saved_note.attachments[0]["url"]
        == "https://example.com/doc.pdf"
    )
    assert saved_note.attachments[0]["type"] == "document"


def test_note_relationships(test_db_session, sample_user):
    """Test note relationships."""
    note = Note(
        user_id=sample_user.id,
        content="Test Note Content",
        attachments=[],
    )
    test_db_session.add(note)
    test_db_session.commit()

    # Test relationship with user
    assert note.owner == sample_user
    assert note in sample_user.notes
