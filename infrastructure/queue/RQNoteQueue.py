"""RQ implementation of the queue service."""

import logging
from datetime import datetime, UTC
from typing import Optional, Dict, Any

from rq import Queue
from rq.job import Job
from rq.worker import Worker

from domain.ports.QueueService import QueueService
from services.robo import get_robo_service
from infrastructure.queue.activity_worker import (
    process_activity_job,
)
from infrastructure.queue.note_worker import (
    process_note_job,
)

logger = logging.getLogger(__name__)


class RQNoteQueue(QueueService):
    """Redis Queue implementation for note processing."""

    def __init__(self, queue: Queue):
        """Initialize the RQ note queue.

        Args:
            queue: RQ Queue instance for note processing
        """
        logger.debug("Initializing RQNoteQueue")
        self.note_queue = queue
        # Get activity queue from same connection
        logger.debug("Creating activity_schema queue")
        self.activity_queue = Queue(
            "activity_schema",
            connection=queue.connection,
        )
        # Initialize robo_service in parent process
        logger.debug("Initializing robo_service")
        self.robo_service = get_robo_service()

    def enqueue_note(self, note_id: int) -> Optional[str]:
        """Enqueue a note for processing.

        Args:
            note_id: ID of the note to process

        Returns:
            Optional[str]: Job ID if enqueued successfully, None otherwise
        """
        try:
            job = self.note_queue.enqueue(
                process_note_job,
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
            # Try both queues
            for queue in [
                self.note_queue,
                self.activity_queue,
            ]:
                try:
                    job = Job.fetch(
                        job_id, connection=queue.connection
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
                except (Exception,):
                    continue
            return {"status": "not_found"}
        except Exception:
            return {"status": "not_found"}

    def get_queue_health(self) -> Dict[str, Any]:
        """Get health metrics for both queues."""
        note_queue_health = {
            "total_jobs": self.note_queue.count,
            "is_empty": self.note_queue.is_empty,
            "worker_count": len(
                Worker.all(queue=self.note_queue)
            ),
        }
        activity_queue_health = {
            "total_jobs": self.activity_queue.count,
            "is_empty": self.activity_queue.is_empty,
            "worker_count": len(
                Worker.all(queue=self.activity_queue)
            ),
        }
        return {
            "note_enrichment": note_queue_health,
            "activity_schema": activity_queue_health,
        }

    def enqueue_activity(
        self, activity_id: int
    ) -> Optional[str]:
        """Enqueue an activity for schema render processing."""
        try:
            logger.debug(
                f"Attempting to enqueue activity {activity_id}"
            )
            logger.debug(
                f"Queue connection status: "
                f"{self.activity_queue.connection.ping()}"
            )
            logger.debug(
                f"Current queue size: {len(self.activity_queue)}"
            )

            # Don't pass robo_service directly,
            # let worker create its own instance
            job = self.activity_queue.enqueue(
                process_activity_job,
                args=(activity_id,),
                job_timeout="10m",
                result_ttl=24
                * 60
                * 60,  # Keep results for 24 hours
                meta={
                    "activity_id": activity_id,
                    "queued_at": datetime.now(
                        UTC
                    ).isoformat(),
                },
            )

            if job:
                logger.info(
                    f"Successfully enqueued activity {activity_id}"
                    f" with job ID {job.id}"
                )
                return job.id
            else:
                logger.error(
                    f"Failed to enqueue activity {activity_id}"
                    f" - job is None"
                )
                return None

        except Exception as e:
            logger.error(
                f"Error enqueueing activity {activity_id}: {str(e)}",
                exc_info=True,
            )
            return None

    def enqueue_task(self, task_id: int) -> Optional[str]:
        """Enqueue a task for processing.

        Args:
            task_id: ID of the task to process

        Returns:
            Optional[str]: Job ID if enqueued successfully, None otherwise
        """
        try:
            from infrastructure.queue.task_worker import (
                process_task_job,
            )

            logger.debug(
                f"Enqueueing task {task_id} for processing"
            )
            job = self.note_queue.enqueue(
                process_task_job,
                args=(task_id,),
                job_timeout="10m",
                result_ttl=24 * 60 * 60,  # 24 hours
                meta={"task_id": task_id},
            )
            logger.debug(
                f"Task {task_id} enqueued with job ID {job.id}"
            )
            return job.id
        except Exception as e:
            logger.error(
                f"Error enqueueing task {task_id}: {str(e)}"
            )
            return None
