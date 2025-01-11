"""Tests for worker runner."""

import pytest
from unittest.mock import Mock, patch

from infrastructure.queue.run_worker import run_worker


@pytest.fixture
def mock_redis_conn():
    """Mock Redis connection."""
    return Mock()


def test_worker_initialization():
    """Test worker initialization with multiple queues."""
    with patch(
        "infrastructure.queue.run_worker.get_redis_connection"
    ) as mock_get_conn, patch(
        "infrastructure.queue.run_worker.Queue"
    ) as mock_queue, patch(
        "infrastructure.queue.run_worker.Worker"
    ) as mock_worker:
        # Setup mocks
        mock_get_conn.return_value = Mock()
        mock_queue_instances = [
            Mock(name="note_enrichment"),
            Mock(name="activity_schema"),
        ]
        mock_queue.side_effect = (
            lambda name, connection: mock_queue_instances[
                [
                    "note_enrichment",
                    "activity_schema",
                ].index(name)
            ]
        )
        mock_worker_instance = Mock()
        mock_worker.return_value = mock_worker_instance
        mock_worker_instance.work.side_effect = (
            KeyboardInterrupt()
        )

        # Run worker
        with pytest.raises(SystemExit) as exc_info:
            run_worker()

        # Verify worker was initialized with both queues
        mock_worker.assert_called_once_with(
            mock_queue_instances,
            connection=mock_get_conn.return_value,
        )
        assert exc_info.value.code == 0


def test_worker_graceful_shutdown():
    """Test worker handles shutdown signal gracefully."""
    with patch(
        "infrastructure.queue.run_worker.get_redis_connection"
    ) as mock_get_conn, patch(
        "infrastructure.queue.run_worker.Queue"
    ) as mock_queue, patch(
        "infrastructure.queue.run_worker.Worker"
    ) as mock_worker:
        # Setup mocks
        mock_get_conn.return_value = Mock()
        mock_queue_instances = [
            Mock(name="note_enrichment"),
            Mock(name="activity_schema"),
        ]
        mock_queue.side_effect = (
            lambda name, connection: mock_queue_instances[
                [
                    "note_enrichment",
                    "activity_schema",
                ].index(name)
            ]
        )
        mock_worker_instance = Mock()
        mock_worker.return_value = mock_worker_instance
        mock_worker_instance.work.side_effect = (
            KeyboardInterrupt()
        )

        # Run worker and verify clean exit
        with pytest.raises(SystemExit) as exc_info:
            run_worker()
        assert exc_info.value.code == 0
