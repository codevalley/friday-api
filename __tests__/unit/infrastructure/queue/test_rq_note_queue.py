"""Tests for RQ note queue implementation."""

from datetime import datetime, UTC
from unittest.mock import Mock, patch
from unittest.mock import call

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
    queue_service.note_queue.enqueue.return_value = mock_job

    # Execute
    job_id = queue_service.enqueue_note(123)

    # Verify
    assert job_id == "test_job_id"
    queue_service.note_queue.enqueue.assert_called_once()
    call_args = queue_service.note_queue.enqueue.call_args
    assert (
        call_args.args[0].__module__
        + "."
        + call_args.args[0].__name__
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
    queue_service.note_queue.enqueue.side_effect = (
        Exception("Queue error")
    )

    # Execute
    job_id = queue_service.enqueue_note(123)

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


@patch("infrastructure.queue.RQNoteQueue.Worker")
def test_get_queue_health(mock_worker, queue_service):
    """Test getting queue health metrics."""
    # Setup
    mock_note_queue = Mock()
    mock_note_queue.is_empty = False
    mock_note_queue.count = 5
    queue_service.note_queue = mock_note_queue

    mock_activity_queue = Mock()
    mock_activity_queue.is_empty = True
    mock_activity_queue.count = 0
    queue_service.activity_queue = mock_activity_queue

    mock_task_queue = Mock()
    mock_task_queue.is_empty = True
    mock_task_queue.count = 0
    queue_service.task_queue = mock_task_queue

    mock_worker.all.side_effect = [
        [Mock(), Mock()],  # 2 workers for note queue
        [Mock()],  # 1 worker for activity queue
        [Mock()],  # 1 worker for task queue
    ]

    # Execute
    health = queue_service.get_queue_health()

    # Verify
    assert health["note_enrichment"]["total_jobs"] == 5
    assert health["note_enrichment"]["is_empty"] is False
    assert health["note_enrichment"]["worker_count"] == 2

    assert health["activity_schema"]["total_jobs"] == 0
    assert health["activity_schema"]["is_empty"] is True
    assert health["activity_schema"]["worker_count"] == 1

    assert health["task_enrichment"]["total_jobs"] == 0
    assert health["task_enrichment"]["is_empty"] is True
    assert health["task_enrichment"]["worker_count"] == 1

    # Verify Worker.all was called correctly
    mock_worker.all.assert_has_calls(
        [
            call(queue=mock_note_queue),
            call(queue=mock_activity_queue),
            call(queue=mock_task_queue),
        ]
    )
