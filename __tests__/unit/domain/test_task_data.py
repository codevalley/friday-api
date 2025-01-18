"""Test suite for TaskData domain model.

This test suite verifies the functionality of the TaskData domain model,
including validation, conversion, and error handling. It ensures that the
model maintains data integrity and follows business rules.
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from domain.task import TaskData
from domain.values import TaskStatus, TaskPriority
from domain.exceptions import (
    TaskValidationError,
    TaskContentError,
    TaskDateError,
    TaskPriorityError,
    TaskStatusError,
    TaskParentError,
)


@pytest.fixture
def valid_task_dict() -> Dict[str, Any]:
    """Create a valid task dictionary for testing.

    This fixture provides a baseline valid task data dictionary
    that can be modified for specific test cases.
    """
    now = datetime.now(timezone.utc)
    return {
        "title": "Test Task",
        "description": "Test task description",
        "user_id": "test-user",
        "status": TaskStatus.TODO,
        "priority": TaskPriority.MEDIUM,
        "due_date": now
        + timedelta(
            days=1
        ),  # Due date is 1 day in the future
        "tags": ["test", "example"],
        "parent_id": None,
        "note_id": None,  # Optional note reference
        "created_at": now,
        "updated_at": now,
    }


@pytest.fixture
def valid_task_data(valid_task_dict) -> TaskData:
    """Create a valid TaskData instance for testing.

    This fixture provides a baseline valid TaskData instance
    that can be used directly in tests.
    """
    return TaskData(**valid_task_dict)


class TestTaskDataValidation:
    """Test validation methods of TaskData."""

    def test_valid_task_data(self, valid_task_data):
        """Test that valid task data passes validation."""
        # Should not raise any exceptions
        valid_task_data.validate()

    def test_invalid_title(self, valid_task_dict):
        """Test validation with invalid title."""
        valid_task_dict["title"] = ""
        with pytest.raises(TaskContentError) as exc:
            TaskData(**valid_task_dict)
        assert (
            str(exc.value)
            == "title must be a non-empty string"
        )

    def test_invalid_description_type(
        self, valid_task_dict
    ):
        """Test validation with invalid description type."""
        valid_task_dict["description"] = 123
        with pytest.raises(TaskContentError) as exc:
            TaskData(**valid_task_dict)
        assert (
            str(exc.value) == "description must be a string"
        )

    def test_invalid_user_id(self, valid_task_dict):
        """Test validation with invalid user_id."""
        valid_task_dict["user_id"] = ""
        with pytest.raises(TaskValidationError) as exc:
            TaskData(**valid_task_dict)
        assert (
            str(exc.value)
            == "user_id must be a non-empty string"
        )

    def test_invalid_status(self, valid_task_dict):
        """Test validation with invalid status."""
        valid_task_dict["status"] = "invalid"
        with pytest.raises(TaskStatusError) as exc:
            TaskData(**valid_task_dict)
        assert "status must be one of" in str(exc.value)

    def test_invalid_priority(self, valid_task_dict):
        """Test validation with invalid priority."""
        valid_task_dict["priority"] = "invalid"
        with pytest.raises(TaskPriorityError) as exc:
            TaskData(**valid_task_dict)
        assert "priority must be one of" in str(exc.value)

    def test_invalid_due_date_type(self, valid_task_dict):
        """Test validation with invalid due_date type."""
        valid_task_dict["due_date"] = "not a datetime"
        with pytest.raises(TaskDateError) as exc:
            TaskData(**valid_task_dict)
        assert (
            str(exc.value)
            == "due_date must be a datetime object"
        )

    def test_invalid_tags_type(self, valid_task_dict):
        """Test validation with invalid tags type."""
        valid_task_dict["tags"] = "not a list"
        with pytest.raises(TaskValidationError) as exc:
            TaskData(**valid_task_dict)
        assert str(exc.value) == "tags must be a list"

    def test_invalid_tag_type(self, valid_task_dict):
        """Test validation with invalid tag type."""
        valid_task_dict["tags"] = [123]
        with pytest.raises(TaskValidationError) as exc:
            TaskData(**valid_task_dict)
        assert str(exc.value) == "tags must be strings"

    def test_valid_parent_id(self, valid_task_dict):
        """Test validation with valid parent_id."""
        valid_task_dict["parent_id"] = 1
        task = TaskData(**valid_task_dict)
        task.validate()  # Should not raise

    def test_invalid_parent_id_type(self, valid_task_dict):
        """Test validation with invalid parent_id type."""
        valid_task_dict["parent_id"] = "not an int"
        with pytest.raises(TaskParentError) as exc:
            TaskData(**valid_task_dict)
        assert (
            str(exc.value)
            == "parent_id must be a positive integer"
        )

    def test_invalid_parent_id_value(self, valid_task_dict):
        """Test validation with invalid parent_id value."""
        valid_task_dict["parent_id"] = 0
        with pytest.raises(TaskParentError) as exc:
            TaskData(**valid_task_dict)
        assert (
            str(exc.value)
            == "parent_id must be a positive integer"
        )

    def test_valid_note_id(self, valid_task_dict):
        """Test validation with valid note_id."""
        valid_task_dict["note_id"] = 1
        task = TaskData(**valid_task_dict)
        task.validate()  # Should not raise

    def test_invalid_note_id_type(self, valid_task_dict):
        """Test validation with invalid note_id type."""
        valid_task_dict["note_id"] = "not an int"
        with pytest.raises(TaskValidationError) as exc:
            TaskData(**valid_task_dict)
        assert (
            str(exc.value)
            == "note_id must be a positive integer"
        )

    def test_invalid_note_id_value(self, valid_task_dict):
        """Test validation with invalid note_id value."""
        valid_task_dict["note_id"] = 0
        with pytest.raises(TaskValidationError) as exc:
            TaskData(**valid_task_dict)
        assert (
            str(exc.value)
            == "note_id must be a positive integer"
        )


class TestTaskDataConversion:
    """Test conversion methods of TaskData."""

    def test_to_dict(self, valid_task_data):
        """Test conversion to dictionary."""
        result = valid_task_data.to_dict()
        assert result["title"] == valid_task_data.title
        assert (
            result["description"]
            == valid_task_data.description
        )
        assert result["user_id"] == valid_task_data.user_id
        assert (
            result["status"] == valid_task_data.status.value
        )
        assert (
            result["priority"]
            == valid_task_data.priority.value
        )
        assert (
            result["due_date"] == valid_task_data.due_date
        )
        assert result["tags"] == valid_task_data.tags
        assert (
            result["parent_id"] == valid_task_data.parent_id
        )
        assert result["note_id"] == valid_task_data.note_id

    def test_from_dict_snake_case(self, valid_task_dict):
        """Test creation from snake_case dictionary."""
        task = TaskData.from_dict(valid_task_dict)
        assert task.title == valid_task_dict["title"]
        assert (
            task.description
            == valid_task_dict["description"]
        )
        assert task.user_id == valid_task_dict["user_id"]
        assert task.status == valid_task_dict["status"]
        assert task.priority == valid_task_dict["priority"]
        assert task.due_date == valid_task_dict["due_date"]
        assert task.tags == valid_task_dict["tags"]
        assert (
            task.parent_id == valid_task_dict["parent_id"]
        )
        assert task.note_id == valid_task_dict["note_id"]

    def test_from_dict_camel_case(self):
        """Test creation from camelCase dictionary."""
        now = datetime.now(timezone.utc)
        camel_dict = {
            "title": "Test Task",
            "description": "Test task description",
            "userId": "test-user",
            "status": TaskStatus.TODO.value,
            "priority": TaskPriority.MEDIUM.value,
            "dueDate": now
            + timedelta(
                days=1
            ),  # Due date is 1 day in the future
            "tags": ["test", "example"],
            "parentId": 1,
            "noteId": None,
            "topicId": 123,
            "createdAt": now,
            "updatedAt": now,
        }
        task = TaskData.from_dict(camel_dict)
        assert task.title == camel_dict["title"]
        assert task.description == camel_dict["description"]
        assert task.user_id == camel_dict["userId"]
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM
        assert task.due_date == camel_dict["dueDate"]
        assert task.tags == camel_dict["tags"]
        assert task.parent_id == camel_dict["parentId"]
        assert task.note_id == camel_dict["noteId"]
        assert task.topic_id == camel_dict["topicId"]
        assert task.created_at == camel_dict["createdAt"]
        assert task.updated_at == camel_dict["updatedAt"]


class TestTaskDataErrorHandling:
    """Test error handling of TaskData."""

    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        with pytest.raises(TypeError):
            TaskData()  # type: ignore

    def test_type_mismatches(self, valid_task_dict):
        """Test handling of type mismatches."""
        valid_task_dict["title"] = 123
        with pytest.raises(TaskContentError) as exc:
            TaskData(**valid_task_dict)
        assert (
            str(exc.value)
            == "title must be a non-empty string"
        )


class TestTaskDataTopicValidation:
    """Test topic-related validation in TaskData."""

    def test_valid_topic_id(self, valid_task_dict):
        """Test validation with valid topic_id."""
        valid_task_dict["topic_id"] = 1
        task = TaskData(**valid_task_dict)
        task.validate()  # Should not raise

    def test_invalid_topic_id_type(self, valid_task_dict):
        """Test validation with invalid topic_id type."""
        valid_task_dict["topic_id"] = "not an int"
        with pytest.raises(TaskValidationError) as exc:
            TaskData(**valid_task_dict)
        assert (
            str(exc.value)
            == "topic_id must be a positive integer"
        )

    def test_invalid_topic_id_value(self, valid_task_dict):
        """Test validation with invalid topic_id value."""
        valid_task_dict["topic_id"] = 0
        with pytest.raises(TaskValidationError) as exc:
            TaskData(**valid_task_dict)
        assert (
            str(exc.value)
            == "topic_id must be a positive integer"
        )

    def test_topic_id_none(self, valid_task_dict):
        """Test validation with topic_id set to None."""
        valid_task_dict["topic_id"] = None
        task = TaskData(**valid_task_dict)
        task.validate()  # Should not raise

    def test_topic_id_in_dict_conversion(
        self, valid_task_dict
    ):
        """Test topic_id is properly included in dictionary conversion."""
        valid_task_dict["topic_id"] = 123
        task = TaskData(**valid_task_dict)
        result = task.to_dict()
        assert result["topic_id"] == 123

    def test_topic_id_from_dict_snake_case(self):
        """Test topic_id handling in from_dict with snake_case."""
        now = datetime.now(timezone.utc)
        data = {
            "title": "Test Task",
            "description": "Test Description",
            "user_id": "test-user",
            "status": TaskStatus.TODO,
            "priority": TaskPriority.MEDIUM,
            "topic_id": 123,
            "created_at": now,
            "updated_at": now,
        }
        task = TaskData.from_dict(data)
        assert task.topic_id == 123


class TestTaskDataTopicOwnership:
    """Test topic ownership validation in TaskData."""

    @pytest.fixture
    def task_with_topic(self, valid_task_dict):
        """Create a task with a topic for testing."""
        valid_task_dict["topic_id"] = 1
        return TaskData(**valid_task_dict)

    def test_validate_topic_ownership_same_user(
        self, task_with_topic
    ):
        """Test validation when topic belongs to same user."""
        # Mock topic owner validation by passing same user_id
        task_with_topic.validate_topic_ownership(
            task_with_topic.user_id
        )
        # Should not raise any exception

    def test_validate_topic_ownership_different_user(
        self, task_with_topic
    ):
        """Test validation when topic belongs to different user."""
        with pytest.raises(TaskValidationError) as exc:
            task_with_topic.validate_topic_ownership(
                "different-user"
            )
        assert (
            str(exc.value)
            == "Topic must belong to the same user as the task"
        )

    def test_validate_topic_ownership_no_topic(
        self, valid_task_dict
    ):
        """Test validation when task has no topic."""
        task = TaskData(
            **valid_task_dict
        )  # No topic_id set
        # Should not raise any exception
        task.validate_topic_ownership("any-user")


class TestTaskDataTopicDeletion:
    """Test topic deletion handling in TaskData."""

    @pytest.fixture
    def task_with_topic(self, valid_task_dict):
        """Create a task with a topic for testing."""
        valid_task_dict["topic_id"] = 1
        return TaskData(**valid_task_dict)

    def test_handle_topic_deletion(self, task_with_topic):
        """Test handling topic deletion by setting topic_id to None."""
        task_with_topic.handle_topic_deletion()
        assert task_with_topic.topic_id is None

    def test_handle_topic_deletion_no_topic(
        self, valid_task_dict
    ):
        """Test handling topic deletion when no topic is set."""
        task = TaskData(
            **valid_task_dict
        )  # No topic_id set
        task.handle_topic_deletion()
        assert task.topic_id is None  # Should remain None

    def test_to_dict_after_topic_deletion(
        self, task_with_topic
    ):
        """Test dictionary representation after topic deletion."""
        task_with_topic.handle_topic_deletion()
        result = task_with_topic.to_dict()
        assert result["topic_id"] is None
