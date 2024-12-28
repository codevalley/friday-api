"""RQ implementation of the queue service."""

from datetime import datetime, UTC
from typing import Optional, Dict, Any

from rq import Queue
from rq.job import Job

from domain.ports.QueueService import QueueService


class RQNoteQueue(QueueService):
    """Redis Queue implementation for note processing."""

    def __init__(self, queue: Queue):
        """Initialize the RQ note queue.

        Args:
            queue: RQ Queue instance
        """
        self.queue = queue

    def enqueue_note(self, note_id: int) -> Optional[str]:
        """Enqueue a note for processing.

        Args:
            note_id: ID of the note to process

        Returns:
            Optional[str]: Job ID if enqueued successfully, None otherwise
        """
        try:
            job = self.queue.enqueue(
                "note_worker.process_note_job",
                args=(note_id,),
                job_timeout="10m",
                result_ttl=24
                * 60
                * 60,  # Keep results for 24 hours
                meta={
                    "note_id": note_id,
                    "queued_at": datetime.now(
                        UTC
                    ).isoformat(),
                },
            )
            return job.id if job else None
        except Exception:
            return None

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a job.

        Args:
            job_id: ID of the job to check

        Returns:
            Dict containing job status information
        """
        try:
            job = Job.fetch(
                job_id, connection=self.queue.connection
            )
            return {
                "status": job.get_status(),
                "created_at": (
                    job.created_at.isoformat()
                    if job.created_at
                    else None
                ),
                "ended_at": (
                    job.ended_at.isoformat()
                    if job.ended_at
                    else None
                ),
                "exc_info": job.exc_info,
                "meta": job.meta,
            }
        except Exception:
            return {"status": "not_found"}

    def get_queue_health(self) -> Dict[str, Any]:
        """Get health metrics for the queue.

        Returns:
            Dict containing queue health metrics
        """
        try:
            return {
                "jobs_total": len(self.queue),
                "workers": len(self.queue.workers),
                "is_empty": self.queue.is_empty,
            }
        except Exception:
            return {
                "jobs_total": 0,
                "workers": 0,
                "is_empty": True,
                "error": "Failed to get queue metrics",
            }
