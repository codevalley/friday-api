"""Test NoteRepository class."""

from repositories.NoteRepository import NoteRepository
from domain.values import AttachmentType


def test_create_note(test_db_session, sample_user):
    """Test creating a note."""
    repo = NoteRepository(test_db_session)
    note = repo.create(
        content="Test Note Content",
        user_id=sample_user.id,
    )

    assert note.id is not None
    assert note.content == "Test Note Content"
    assert note.user_id == sample_user.id
    assert note.attachment_url is None
    assert note.attachment_type is None


def test_create_note_with_attachment(
    test_db_session, sample_user
):
    """Test creating a note with attachment."""
    repo = NoteRepository(test_db_session)
    note = repo.create(
        content="Test Note with Attachment",
        user_id=sample_user.id,
        attachments=[{
            "url": "https://example.com/photo.jpg",
            "type": AttachmentType.IMAGE,
        }],
    )

    assert note.id is not None
    assert note.content == "Test Note with Attachment"
    assert note.attachments[0]["url"] == "https://example.com/photo.jpg"
    assert note.attachments[0]["type"] == AttachmentType.IMAGE


def test_list_notes(test_db_session, sample_user):
    """Test listing notes for a user."""
    repo = NoteRepository(test_db_session)

    # Create multiple notes
    for i in range(3):
        repo.create(
            content=f"Test Note {i}",
            user_id=sample_user.id,
        )

    notes = repo.list_notes(
        user_id=sample_user.id, skip=0, limit=10
    )
    assert len(notes) == 3
    for i, note in enumerate(notes):
        assert note.content == f"Test Note {i}"
        assert note.user_id == sample_user.id


def test_get_by_user(test_db_session, sample_user):
    """Test getting a note by ID and user ID."""
    repo = NoteRepository(test_db_session)
    note = repo.create(
        content="Test Note",
        user_id=sample_user.id,
    )

    # Get note by correct user
    found = repo.get_by_user(note.id, sample_user.id)
    assert found is not None
    assert found.id == note.id

    # Try to get note with wrong user
    not_found = repo.get_by_user(
        note.id, "wrong-user-id"
    )
    assert not_found is None


def test_count_user_notes(test_db_session, sample_user):
    """Test counting user's notes."""
    repo = NoteRepository(test_db_session)

    # Create multiple notes
    for i in range(3):
        repo.create(
            content=f"Test Note {i}",
            user_id=sample_user.id,
        )

    count = repo.count_user_notes(sample_user.id)
    assert count == 3
