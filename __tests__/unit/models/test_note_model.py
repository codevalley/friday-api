"""Test NoteModel class."""

import uuid
from datetime import datetime

import pytest

from orm.NoteModel import Note
from orm.UserModel import User
from orm.TaskModel import Task
from domain.values import (
    ProcessingStatus,
    TaskStatus,
    TaskPriority,
)


@pytest.fixture
def sample_user(test_db_session) -> User:
    """Create a sample user for testing."""
    user = User(
        username=f"testuser_{uuid.uuid4().hex[:8]}",  # Make username unique
        key_id=str(uuid.uuid4()),
        user_secret="test-secret-hash",
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


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


def test_note_processing_status_update(
    test_db_session, sample_user
):
    """Test updating note processing status."""
    note = Note(
        user_id=sample_user.id,
        content="Test Note Content",
        attachments=[],
    )
    test_db_session.add(note)
    test_db_session.commit()

    # Verify initial status
    assert (
        note.processing_status == ProcessingStatus.PENDING
    )

    # Update status
    note.processing_status = ProcessingStatus.PROCESSING
    test_db_session.commit()
    test_db_session.refresh(note)

    assert (
        note.processing_status
        == ProcessingStatus.PROCESSING
    )

    # Update to completed
    note.processing_status = ProcessingStatus.COMPLETED
    test_db_session.commit()
    test_db_session.refresh(note)

    assert (
        note.processing_status == ProcessingStatus.COMPLETED
    )


def test_note_timestamps(test_db_session, sample_user):
    """Test note timestamp handling."""
    note = Note(
        user_id=sample_user.id,
        content="Test Note Content",
        attachments=[],
    )
    test_db_session.add(note)
    test_db_session.commit()

    # Verify created_at is set
    assert note.created_at is not None
    assert isinstance(note.created_at, datetime)

    # Initially updated_at should be None
    assert note.updated_at is None

    # Update note
    original_content = note.content
    note.content = "Updated content"
    test_db_session.commit()
    test_db_session.refresh(note)

    # Verify updated_at is set
    assert note.updated_at is not None
    assert isinstance(note.updated_at, datetime)
    assert note.content != original_content


def test_note_user_relationship(
    test_db_session, sample_user
):
    """Test relationship between Note and User models."""
    note = Note(
        user_id=sample_user.id,
        content="Test Note Content",
        attachments=[],
    )
    test_db_session.add(note)
    test_db_session.commit()
    test_db_session.refresh(note)

    # Verify relationship
    assert note.user == sample_user
    assert note in sample_user.notes


def test_note_cascade_delete(test_db_session, sample_user):
    """Test that notes are deleted when user is deleted."""
    note = Note(
        user_id=sample_user.id,
        content="Test Note Content",
        attachments=[],
    )
    test_db_session.add(note)
    test_db_session.commit()
    test_db_session.refresh(note)

    # Delete user
    test_db_session.delete(sample_user)
    test_db_session.commit()

    # Verify note is deleted
    saved_note = (
        test_db_session.query(Note)
        .filter_by(id=note.id)
        .first()
    )
    assert saved_note is None


def test_note_tasks_relationship(
    test_db_session, sample_user
):
    """Test back-population relationship between Note and Task models."""
    # Create a note
    note = Note(
        user_id=sample_user.id,
        content="Test Note Content",
        attachments=[],
    )
    test_db_session.add(note)
    test_db_session.commit()
    test_db_session.refresh(note)

    # Create tasks associated with the note
    task1 = Task(
        title="Task 1",
        description="First task",
        user_id=sample_user.id,
        note_id=note.id,
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
    )
    task2 = Task(
        title="Task 2",
        description="Second task",
        user_id=sample_user.id,
        note_id=note.id,
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
    )

    test_db_session.add(task1)
    test_db_session.add(task2)
    test_db_session.commit()
    test_db_session.refresh(note)

    # Verify tasks relationship
    assert len(note.tasks) == 2
    assert task1 in note.tasks
    assert task2 in note.tasks

    # Verify task attributes
    tasks = sorted(note.tasks, key=lambda t: t.title)
    assert tasks[0].title == "Task 1"
    assert tasks[1].title == "Task 2"

    # Remove a task's association
    task1.note_id = None
    test_db_session.commit()
    test_db_session.refresh(note)

    # Verify task was removed from relationship
    assert len(note.tasks) == 1
    assert task1 not in note.tasks
    assert task2 in note.tasks
