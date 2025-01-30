"""Worker module for processing tasks."""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from domain.values import ProcessingStatus
from domain.exceptions import RoboServiceError
from domain.robo import RoboService
from repositories.TaskRepository import TaskRepository
from services.robo import get_robo_service
from utils.retry import calculate_backoff
from configs.Database import SessionLocal
import orm.UserModel  # noqa: F401 Required for SQLAlchemy model registry
import orm.TopicModel  # noqa: F401 Required for SQLAlchemy model registry
import orm.NoteModel  # noqa: F401 Required for SQLAlchemy model registry
import orm.MomentModel  # noqa: F401 Required for SQLAlchemy model registry
import orm.TaskModel  # noqa: F401 Required for SQLAlchemy model registry
import orm.ActivityModel  # noqa: F401 Required for SQLAlchemy model registry

logger = logging.getLogger(__name__)


def create_task(
    content: str,
    user_id: int,
    source_note_id: Optional[int] = None,
    session: Optional[Session] = None,
    max_retries: int = 3,
) -> int:
    """Create a new task and enqueue it for enrichment.

    Args:
        content: Task content
        user_id: ID of the task owner
        source_note_id: Optional ID of source note
        session: Optional database session
        max_retries: Maximum number of retries

    Returns:
        ID of the created task

    Raises:
        TaskValidationError: If task creation fails
    """
    session_provided = session is not None
    try:
        if not session:
            session = SessionLocal()

        # Create task repository
        task_repository = TaskRepository(session)

        # Create task with basic attributes
        created_at = datetime.now(timezone.utc)
        task = task_repository.create(
            {
                "content": content,
                "user_id": user_id,
                "note_id": source_note_id,
                "created_at": created_at,
                "updated_at": created_at,
                "status": "TODO",
                "priority": "MEDIUM",
                "processing_status": ProcessingStatus.PENDING,
            }
        )

        session.add(task)
        session.commit()

        # Enqueue task for enrichment
        process_task_job(
            task.id,
            session=session,
            max_retries=max_retries,
        )

        return task.id

    finally:
        if not session_provided and session:
            session.close()


def process_task_job(
    task_id: int,
    session: Optional[Session] = None,
    robo_service: Optional[RoboService] = None,
    task_repository: Optional[TaskRepository] = None,
    max_retries: int = 3,
) -> None:
    """Process a task using RoboService.

    Args:
        task_id: ID of task to process
        session: Optional database session
        robo_service: Optional RoboService instance
        task_repository: Optional task repository
        max_retries: Maximum number of retries

    Raises:
        ValueError: If task not found
        RoboServiceError: If processing fails
    """
    session_provided = session is not None
    start_time = datetime.now(timezone.utc)

    try:
        logger.info(f"Starting to process task {task_id}")

        # Create session if not provided
        if not session:
            logger.debug("Creating new database session")
            session = SessionLocal()

        # Create repository if not provided
        if not task_repository:
            logger.debug("Creating new task repository")
            task_repository = TaskRepository(session)

        # Get task
        logger.debug(
            f"Fetching task {task_id} from database"
        )
        task = task_repository.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        logger.info(
            f"Processing task {task_id} with content: {task.content[:100]}..."
        )

        # Update to PROCESSING
        logger.debug(
            f"Updating task {task_id} status to PROCESSING"
        )
        task.processing_status = ProcessingStatus.PROCESSING
        task.updated_at = datetime.now(timezone.utc)
        session.add(task)
        session.commit()

        # Create RoboService if not provided
        if not robo_service:
            logger.debug(
                "Creating new RoboService instance"
            )
            robo_service = get_robo_service()
            logger.info(
                f"Created RoboService of type: {type(robo_service).__name__}"
            )

        for attempt in range(max_retries + 1):
            try:
                # Process the task with enrichment context
                logger.info(
                    f"Attempt {attempt + 1}/{max_retries + 1} "
                    f"to process task {task_id}"
                )
                result = robo_service.process_task(
                    task.content,
                    context={
                        "type": "task_enrichment",
                        # Add any task-specific context
                        "priority": (
                            task.priority
                            if hasattr(task, "priority")
                            else None
                        ),
                        "due_date": (
                            task.due_date.isoformat()
                            if hasattr(task, "due_date")
                            and task.due_date
                            else None
                        ),
                        "parent_task": (
                            task.parent.content
                            if hasattr(task, "parent")
                            and task.parent
                            else None
                        ),
                    },
                )
                logger.info(
                    f"Successfully processed task {task_id}"
                )
                logger.debug(f"Processing result: {result}")

                task.enrichment_data = {
                    "title": result.metadata["title"],
                    "formatted": result.content,
                    "tokens_used": result.tokens_used,
                    "model_name": result.model_name,
                    "created_at": result.created_at.isoformat(),
                    "metadata": result.metadata,
                }

                # Update to COMPLETED
                logger.debug(
                    f"Updating task {task_id} status to COMPLETED"
                )
                task.processing_status = (
                    ProcessingStatus.COMPLETED
                )
                task.processed_at = datetime.now(
                    timezone.utc
                )
                task.updated_at = datetime.now(timezone.utc)
                session.add(task)
                session.commit()
                logger.info(
                    f"Successfully completed processing task {task_id}"
                )
                return  # Success, exit function

            except Exception as e:
                logger.error(
                    f"Failed to process task {task_id} "
                    f"(attempt {attempt + 1}/{max_retries + 1}): "
                    f"{str(e)}"
                )

                # If this was the last attempt, mark as failed and raise
                if attempt == max_retries:
                    logger.error(
                        f"All attempts failed for task {task_id}"
                    )
                    task.processing_status = (
                        ProcessingStatus.FAILED
                    )
                    task.updated_at = datetime.now(
                        timezone.utc
                    )
                    session.add(task)
                    session.commit()
                    raise RoboServiceError(
                        f"Failed to process task {task_id}: {str(e)}"
                    )

                # Wait before retrying with exponential backoff
                delay = calculate_backoff(attempt + 1)
                logger.info(
                    f"Waiting {delay}s before retry"
                )
                time.sleep(delay)

    except Exception as e:
        if not isinstance(
            e, (ValueError, RoboServiceError)
        ):
            logger.error(
                f"Error in process_task_job for task {task_id}: {str(e)}",
                exc_info=True,  # Include stack trace
            )
        raise

    finally:
        # Only close the session if we created it
        if not session_provided and session:
            logger.debug("Closing database session")
            session.close()

        duration = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()
        logger.info(
            f"Task {task_id} processing completed in {duration}s"
        )
