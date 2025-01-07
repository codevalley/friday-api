"""Tests for RQ note queue implementation."""

from datetime import datetime, UTC
from unittest.mock import Mock, patch

import pytest

from infrastructure.queue.RQNoteQueue import RQNoteQueue


@pytest.fixture
def mock_job():
    """Create a mock job."""
    job = Mock()
    job.id = "test_job_id"
    job.get_status.return_value = "finished"
    job.created_at = datetime.now(UTC)
    job.ended_at = datetime.now(UTC)
    job.exc_info = None
    job.meta = {"note_id": 123}
    return job


@pytest.fixture
def queue_service():
    """Create a queue service with mocked queue."""
    mock_queue = Mock()
    mock_queue.connection = Mock()
    return RQNoteQueue(queue=mock_queue)


def test_enqueue_note_success(queue_service):
    """Test successful note enqueueing."""
    # Setup
    mock_job = Mock()
    mock_job.id = "test_job_id"
    queue_service.queue.enqueue.return_value = mock_job

    # Execute
    job_id = queue_service.enqueue_note(123)

    # Verify
    assert job_id == "test_job_id"
    queue_service.queue.enqueue.assert_called_once()
    call_args = queue_service.queue.enqueue.call_args
    assert (
        call_args.args[0]
        == "infrastructure.queue.note_worker.process_note_job"
    )
    assert call_args.kwargs["args"] == (123,)
    assert call_args.kwargs["job_timeout"] == "10m"
    assert call_args.kwargs["result_ttl"] == 24 * 60 * 60
    assert call_args.kwargs["meta"]["note_id"] == 123
    assert "queued_at" in call_args.kwargs["meta"]


def test_enqueue_note_failure(queue_service):
    """Test failed note enqueueing."""
    # Setup
    queue_service.queue.enqueue.side_effect = Exception(
        "Queue error"
    )

    # Execute
    job_id = queue_service.enqueue_note(123)

    # Verify
    assert job_id is None


def test_enqueue_activity_success(queue_service):
    """Test successful activity enqueueing."""
    # Setup
    mock_job = Mock()
    mock_job.id = "test_job_id"
    queue_service.queue.enqueue.return_value = mock_job

    # Execute
    job_id = queue_service.enqueue_activity(456)

    # Verify
    assert job_id == "test_job_id"
    queue_service.queue.enqueue.assert_called_once()
    call_args = queue_service.queue.enqueue.call_args
    assert (
        call_args.args[0]
        == "infrastructure.queue.activity_worker.process_activity_job"
    )
    assert call_args.kwargs["args"] == (456,)
    assert call_args.kwargs["job_timeout"] == "10m"
    assert call_args.kwargs["result_ttl"] == 24 * 60 * 60
    assert call_args.kwargs["meta"]["activity_id"] == 456
    assert "queued_at" in call_args.kwargs["meta"]


def test_enqueue_activity_failure(queue_service):
    """Test failed activity enqueueing."""
    # Setup
    queue_service.queue.enqueue.side_effect = Exception(
        "Queue error"
    )

    # Execute
    job_id = queue_service.enqueue_activity(456)

    # Verify
    assert job_id is None


def test_get_job_status_found(queue_service, mock_job):
    """Test getting status of existing job."""
    # Setup
    with patch("rq.job.Job.fetch", return_value=mock_job):
        # Execute
        status = queue_service.get_job_status("job123")

    # Verify
    assert status["status"] == "finished"
    assert "created_at" in status
    assert "ended_at" in status
    assert status["exc_info"] is None
    assert status["meta"] == {"note_id": 123}


def test_get_job_status_not_found(queue_service):
    """Test getting status of non-existent job."""
    # Setup
    with patch(
        "rq.job.Job.fetch",
        side_effect=Exception("Job not found"),
    ):
        # Execute
        status = queue_service.get_job_status("job123")

    # Verify
    assert status["status"] == "not_found"


def test_get_queue_health(queue_service):
    """Test getting queue health metrics."""
    # Setup
    queue_service.queue.is_empty = False
    queue_service.queue.__len__ = Mock(return_value=5)
    queue_service.queue.workers.__len__ = Mock(
        return_value=2
    )

    # Execute
    health = queue_service.get_queue_health()

    # Verify
    assert health["jobs_total"] == 5
    assert health["workers"] == 2
    assert health["is_empty"] is False
