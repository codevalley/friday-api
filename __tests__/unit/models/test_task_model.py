"""Test TaskModel class."""

from datetime import datetime, UTC
import pytest

from orm.TaskModel import Task
from orm.NoteModel import Note
from domain.values import TaskStatus, TaskPriority


@pytest.fixture
def sample_note(test_db_session, sample_user) -> Note:
    """Create a sample note for testing."""
    note = Note(
        content="Test Note Content",
        user_id=sample_user.id,
        attachments=[],
    )
    test_db_session.add(note)
    test_db_session.commit()
    test_db_session.refresh(note)
    return note


@pytest.fixture
def sample_task(test_db_session, sample_user) -> Task:
    """Create a sample task for testing."""
    task = Task(
        title="Test Task",
        description="Test Description",
        user_id=sample_user.id,
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
    )
    test_db_session.add(task)
    test_db_session.commit()
    test_db_session.refresh(task)
    return task


def test_task_initialization(sample_user):
    """Test basic task model initialization."""
    task = Task(
        title="Test Task",
        description="Test Description",
        user_id=sample_user.id,
    )

    assert task.title == "Test Task"
    assert task.description == "Test Description"
    assert task.user_id == sample_user.id
    assert task.status == TaskStatus.TODO  # Default value
    assert (
        task.priority == TaskPriority.MEDIUM
    )  # Default value
    assert task.note_id is None
    assert task.note is None


def test_task_with_note(
    test_db_session, sample_user, sample_note
):
    """Test task creation with an associated note."""
    task = Task(
        title="Test Task",
        description="Test Description",
        user_id=sample_user.id,
        note_id=sample_note.id,
    )
    test_db_session.add(task)
    test_db_session.commit()
    test_db_session.refresh(task)

    assert task.note_id == sample_note.id
    assert task.note == sample_note


def test_task_note_relationship_optional(
    test_db_session, sample_user, sample_note
):
    """Test that note relationship is optional and can be modified."""
    # Create task without note
    task = Task(
        title="Test Task",
        description="Test Description",
        user_id=sample_user.id,
    )
    test_db_session.add(task)
    test_db_session.commit()

    # Verify no note
    assert task.note_id is None
    assert task.note is None

    # Add note
    task.note_id = sample_note.id
    test_db_session.commit()
    test_db_session.refresh(task)

    # Verify note was added
    assert task.note_id == sample_note.id
    assert task.note == sample_note

    # Remove note
    task.note_id = None
    test_db_session.commit()
    test_db_session.refresh(task)

    # Verify note was removed
    assert task.note_id is None
    assert task.note is None


def test_task_note_set_null_on_delete(
    test_db_session, sample_user, sample_note
):
    """Test that note_id is set to NULL when note is deleted."""
    task = Task(
        title="Test Task",
        description="Test Description",
        user_id=sample_user.id,
        note_id=sample_note.id,
    )
    test_db_session.add(task)
    test_db_session.commit()
    test_db_session.refresh(task)

    # Delete note
    test_db_session.delete(sample_note)
    test_db_session.commit()
    test_db_session.refresh(task)

    # Verify task still exists but note_id is NULL
    assert task.note_id is None
    assert task.note is None


def test_task_hierarchy(test_db_session, sample_user):
    """Test task parent-child relationships."""
    # Create parent task
    parent_task = Task(
        title="Parent Task",
        description="Parent Description",
        user_id=sample_user.id,
    )
    test_db_session.add(parent_task)
    test_db_session.commit()

    # Create child task
    child_task = Task(
        title="Child Task",
        description="Child Description",
        user_id=sample_user.id,
        parent_id=parent_task.id,
    )
    test_db_session.add(child_task)
    test_db_session.commit()
    test_db_session.refresh(parent_task)

    # Test relationships
    assert child_task.parent == parent_task
    assert child_task in parent_task.subtasks
    assert len(parent_task.subtasks) == 1


def test_task_cascade_delete(test_db_session, sample_user):
    """Test that deleting a parent task cascades to child tasks."""
    # Create parent task
    parent_task = Task(
        title="Parent Task",
        description="Parent Description",
        user_id=sample_user.id,
    )
    test_db_session.add(parent_task)
    test_db_session.commit()

    # Create child task
    child_task = Task(
        title="Child Task",
        description="Child Description",
        user_id=sample_user.id,
        parent_id=parent_task.id,
    )
    test_db_session.add(child_task)
    test_db_session.commit()

    # Delete parent task
    test_db_session.delete(parent_task)
    test_db_session.commit()

    # Verify both tasks are deleted
    assert (
        test_db_session.query(Task)
        .filter_by(id=parent_task.id)
        .first()
        is None
    )
    assert (
        test_db_session.query(Task)
        .filter_by(id=child_task.id)
        .first()
        is None
    )


def test_task_to_dict(sample_user, sample_note):
    """Test task to_dict method."""
    task = Task(
        title="Test Task",
        description="Test Description",
        user_id=sample_user.id,
        note_id=sample_note.id,
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH,
        due_date=datetime.now(UTC),
        tags=["test", "important"],
    )

    task_dict = task.to_dict()
    assert task_dict["title"] == "Test Task"
    assert task_dict["description"] == "Test Description"
    assert task_dict["user_id"] == sample_user.id
    assert task_dict["note_id"] == sample_note.id
    assert task_dict["status"] == TaskStatus.IN_PROGRESS
    assert task_dict["priority"] == TaskPriority.HIGH
    assert isinstance(task_dict["due_date"], datetime)
    assert task_dict["tags"] == ["test", "important"]


def test_task_update(
    test_db_session, sample_user, sample_note
):
    """Test task update functionality."""
    task = Task(
        title="Original Title",
        description="Original Description",
        user_id=sample_user.id,
    )
    test_db_session.add(task)
    test_db_session.commit()

    # Update task
    task.update(
        {
            "title": "Updated Title",
            "description": "Updated Description",
            "note_id": sample_note.id,
            "status": TaskStatus.IN_PROGRESS,
            "priority": TaskPriority.HIGH,
        }
    )
    test_db_session.commit()

    # Verify updates
    saved_task = (
        test_db_session.query(Task)
        .filter_by(id=task.id)
        .first()
    )
    assert saved_task.title == "Updated Title"
    assert saved_task.description == "Updated Description"
    assert saved_task.note_id == sample_note.id
    assert saved_task.status == TaskStatus.IN_PROGRESS
    assert saved_task.priority == TaskPriority.HIGH
