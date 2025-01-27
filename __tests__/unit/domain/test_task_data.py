"""Test suite for TaskData domain model.

This test suite verifies the functionality of the TaskData domain model,
including validation, conversion, and error handling. It ensures that the
model maintains data integrity and follows business rules.
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from domain.task import TaskData
from domain.values import (
    TaskStatus,
    TaskPriority,
    ProcessingStatus,
)
from domain.exceptions import (
    TaskValidationError,
    TaskContentError,
    TaskStatusError,
)


@pytest.fixture
def valid_task_dict() -> Dict[str, Any]:
    """Create a valid task dictionary for testing.

    This fixture provides a baseline valid task data dictionary
    that can be modified for specific test cases.
    """
    now = datetime.now(timezone.utc)
    return {
        "content": "Test task content with details",
        "user_id": "test-user",
        "status": TaskStatus.TODO,
        "priority": TaskPriority.MEDIUM,
        "due_date": now + timedelta(days=1),
        "tags": ["test", "example"],
        "parent_id": None,
        "note_id": None,
        "topic_id": None,
        "processing_status": ProcessingStatus.NOT_PROCESSED,
        "enrichment_data": None,
        "processed_at": None,
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


@pytest.fixture
def enriched_task_dict(valid_task_dict) -> Dict[str, Any]:
    """Create a task dictionary with enrichment data."""
    now = datetime.now(timezone.utc)
    return {
        **valid_task_dict,
        "processing_status": ProcessingStatus.COMPLETED,
        "enrichment_data": {
            "title": "Test Task",
            "formatted": "# Test Task\n\nTest task content with details",
            "tokens_used": 100,
            "model_name": "gpt-3.5-turbo",
            "created_at": now,
            "metadata": {
                "due_date": now + timedelta(days=1),
                "priority": "medium",
                "tags": ["test", "example"],
            },
        },
        "processed_at": now,
    }


class TestTaskDataValidation:
    """Test validation methods of TaskData."""

    def test_valid_task_data(self, valid_task_data):
        """Test that valid task data passes validation."""
        # Should not raise any exceptions
        valid_task_data.validate()

    def test_invalid_content_empty(self, valid_task_dict):
        """Test validation with empty content."""
        valid_task_dict["content"] = ""
        with pytest.raises(TaskContentError) as exc:
            TaskData(**valid_task_dict)
        assert str(exc.value) == "content cannot be empty"

    def test_invalid_content_type(self, valid_task_dict):
        """Test validation with invalid content type."""
        valid_task_dict["content"] = 123
        with pytest.raises(TaskContentError) as exc:
            TaskData(**valid_task_dict)
        assert str(exc.value) == "content must be a string"

    def test_content_too_long(self, valid_task_dict):
        """Test validation with content exceeding max length."""
        valid_task_dict["content"] = "x" * 513  # Max is 512
        with pytest.raises(TaskContentError) as exc:
            TaskData(**valid_task_dict)
        assert (
            str(exc.value)
            == "content cannot exceed 512 characters"
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
        assert "Invalid task status" in str(exc.value)

    def test_invalid_processing_status(
        self, valid_task_dict
    ):
        """Test validation with invalid processing status."""
        valid_task_dict["processing_status"] = "invalid"
        with pytest.raises(TaskValidationError) as exc:
            TaskData(**valid_task_dict)
        assert "Invalid processing status" in str(exc.value)

    def test_enrichment_data_without_processed_at(
        self, valid_task_dict
    ):
        """Test validation when enrichment data exists without processed_at."""
        valid_task_dict["enrichment_data"] = {
            "some": "data"
        }
        valid_task_dict["processed_at"] = None
        with pytest.raises(TaskValidationError) as exc:
            TaskData(**valid_task_dict)
        assert (
            "processed_at required with enrichment_data"
            in str(exc.value)
        )

    def test_processed_at_without_enrichment_data(
        self, valid_task_dict
    ):
        """Test validation when processed_at exists without enrichment data."""
        valid_task_dict["enrichment_data"] = None
        valid_task_dict["processed_at"] = datetime.now(
            timezone.utc
        )
        with pytest.raises(TaskValidationError) as exc:
            TaskData(**valid_task_dict)
        assert (
            "enrichment_data required with processed_at"
            in str(exc.value)
        )


class TestTaskDataEnrichment:
    """Test enrichment-related functionality of TaskData."""

    def test_enriched_task_data(self, enriched_task_dict):
        """Test that enriched task data passes validation."""
        task = TaskData(**enriched_task_dict)
        task.validate()
        assert (
            task.processing_status
            == ProcessingStatus.COMPLETED
        )
        assert task.enrichment_data is not None
        assert task.processed_at is not None

    def test_update_processing_status(
        self, valid_task_data
    ):
        """Test updating processing status."""
        valid_task_data.update_processing_status(
            ProcessingStatus.PENDING
        )
        assert (
            valid_task_data.processing_status
            == ProcessingStatus.PENDING
        )
        assert valid_task_data.enrichment_data is None
        assert valid_task_data.processed_at is None

    def test_update_processing_status_with_data(
        self, valid_task_data
    ):
        """Test updating processing status with enrichment data."""
        now = datetime.now(timezone.utc)
        enrichment_data = {
            "title": "Test Task",
            "formatted": "# Test Task\n\nTest content",
            "tokens_used": 50,
            "model_name": "gpt-3.5-turbo",
            "created_at": now,
            "metadata": {},
        }

        # Follow proper state transitions
        valid_task_data.update_processing_status(
            ProcessingStatus.PENDING
        )
        valid_task_data.update_processing_status(
            ProcessingStatus.PROCESSING
        )
        valid_task_data.update_processing_status(
            ProcessingStatus.COMPLETED,
            enrichment_data=enrichment_data,
        )

        assert (
            valid_task_data.processing_status
            == ProcessingStatus.COMPLETED
        )
        assert (
            valid_task_data.enrichment_data
            == enrichment_data
        )
        assert valid_task_data.processed_at is not None

    def test_invalid_enrichment_data_structure(
        self, valid_task_data
    ):
        """Test validation with invalid enrichment data structure."""
        with pytest.raises(TaskValidationError) as exc:
            valid_task_data.update_processing_status(
                ProcessingStatus.COMPLETED,
                enrichment_data={"invalid": "structure"},
            )
        assert "Invalid enrichment data structure" in str(
            exc.value
        )


class TestTaskDataConversion:
    """Test conversion methods of TaskData."""

    def test_to_dict(self, valid_task_data):
        """Test conversion to dictionary."""
        result = valid_task_data.to_dict()
        assert result["content"] == valid_task_data.content
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
        assert (
            result["topic_id"] == valid_task_data.topic_id
        )
        assert (
            result["processing_status"]
            == valid_task_data.processing_status.value
        )
        assert (
            result["enrichment_data"]
            == valid_task_data.enrichment_data
        )
        assert (
            result["processed_at"]
            == valid_task_data.processed_at
        )
        assert (
            result["created_at"]
            == valid_task_data.created_at
        )
        assert (
            result["updated_at"]
            == valid_task_data.updated_at
        )

    def test_from_dict_snake_case(self, valid_task_dict):
        """Test creation from snake_case dictionary."""
        task = TaskData.from_dict(valid_task_dict)
        assert task.content == valid_task_dict["content"]
        assert task.user_id == valid_task_dict["user_id"]
        assert task.status == valid_task_dict["status"]
        assert task.priority == valid_task_dict["priority"]
        assert task.due_date == valid_task_dict["due_date"]
        assert task.tags == valid_task_dict["tags"]
        assert (
            task.parent_id == valid_task_dict["parent_id"]
        )
        assert task.note_id == valid_task_dict["note_id"]
        assert task.topic_id == valid_task_dict["topic_id"]
        assert (
            task.processing_status
            == valid_task_dict["processing_status"]
        )
        assert (
            task.enrichment_data
            == valid_task_dict["enrichment_data"]
        )
        assert (
            task.processed_at
            == valid_task_dict["processed_at"]
        )
        assert (
            task.created_at == valid_task_dict["created_at"]
        )
        assert (
            task.updated_at == valid_task_dict["updated_at"]
        )

    def test_from_dict_camel_case(self):
        """Test creation from camelCase dictionary."""
        now = datetime.now(timezone.utc)
        camel_dict = {
            "content": "Test task content with details",
            "userId": "test-user",
            "status": TaskStatus.TODO.value,
            "priority": TaskPriority.MEDIUM.value,
            "dueDate": now + timedelta(days=1),
            "tags": ["test", "example"],
            "parentId": None,
            "noteId": None,
            "topicId": None,
            "processingStatus": ProcessingStatus.NOT_PROCESSED.value,
            "enrichmentData": None,
            "processedAt": None,
            "createdAt": now,
            "updatedAt": now,
        }
        task = TaskData.from_dict(camel_dict)
        assert task.content == camel_dict["content"]
        assert task.user_id == camel_dict["userId"]
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM
        assert task.due_date == camel_dict["dueDate"]
        assert task.tags == camel_dict["tags"]
        assert task.parent_id == camel_dict["parentId"]
        assert task.note_id == camel_dict["noteId"]
        assert task.topic_id == camel_dict["topicId"]
        assert (
            task.processing_status
            == ProcessingStatus.NOT_PROCESSED
        )
        assert (
            task.enrichment_data
            == camel_dict["enrichmentData"]
        )
        assert (
            task.processed_at == camel_dict["processedAt"]
        )
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
        valid_task_dict["content"] = 123
        with pytest.raises(TaskContentError) as exc:
            TaskData(**valid_task_dict)
        assert str(exc.value) == "content must be a string"


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
            "content": "Test task content with details",
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
