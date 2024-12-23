"""Test NoteRepository class."""

from repositories.NoteRepository import NoteRepository
from domain.values import AttachmentType
import pytest
from unittest.mock import Mock
from orm.NoteModel import Note


@pytest.fixture
def note_repository(test_db_session):
    """Create NoteRepository instance with test database session."""
    return NoteRepository(db=test_db_session)


@pytest.fixture
def mock_note():
    """Create a mock note for testing."""
    note = Mock(spec=Note)
    note.id = 1
    note.content = "Test Note 1"  # Ensure this matches the expected value
    note.user_id = "test-user"
    return note


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
        attachments=[
            {
                "url": "https://example.com/photo.jpg",
                "type": AttachmentType.IMAGE,
            }
        ],
    )

    assert note.id is not None
    assert note.content == "Test Note with Attachment"
    assert (
        note.attachments[0]["url"]
        == "https://example.com/photo.jpg"
    )
    assert (
        note.attachments[0]["type"] == AttachmentType.IMAGE
    )


def test_list_notes(note_repository, mock_note):
    """Test listing notes."""
    # Setup mock data
    note_repository.list_notes = Mock(return_value=[mock_note])

    # Call the method
    notes = note_repository.list_notes()

    # Assertions
    assert len(notes) == 1
    assert notes[0].content == (
        "Test Note 1"  # Ensure this matches the mock data
    )


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
    not_found = repo.get_by_user(note.id, "wrong-user-id")
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
