"""Queue service interface for note processing."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class QueueService(ABC):
    """Interface for queue operations."""

    @abstractmethod
    def enqueue_note(self, note_id: int) -> Optional[str]:
        """Enqueue a note for processing.

        Args:
            note_id: ID of the note to process

        Returns:
            Optional[str]: Job ID if enqueued successfully, None otherwise
        """
        pass

    @abstractmethod
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a job.

        Args:
            job_id: ID of the job to check

        Returns:
            Dict containing job status information
        """
        pass

    @abstractmethod
    def get_queue_health(self) -> Dict[str, Any]:
        """Get health metrics for the queue.

        Returns:
            Dict containing queue health metrics
        """
        pass
