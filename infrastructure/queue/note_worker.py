"""Worker module for processing notes."""

import logging
import time
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from domain.values import ProcessingStatus
from domain.exceptions import RoboServiceError
from domain.robo import RoboService
from repositories.NoteRepository import NoteRepository
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


def process_note_job(
    note_id: int,
    session: Optional[Session] = None,
    robo_service: Optional[RoboService] = None,
    note_repository: Optional[NoteRepository] = None,
    task_repository: Optional[TaskRepository] = None,
    max_retries: int = 3,
) -> None:
    """Process a note using RoboService.

    Args:
        note_id: ID of note to process
        session: Optional database session
        robo_service: Optional RoboService instance
        note_repository: Optional note repository
        task_repository: Optional task repository
        max_retries: Maximum number of retries

    Raises:
        ValueError: If note not found
        RoboServiceError: If processing fails
    """
    session_provided = session is not None
    start_time = datetime.now(timezone.utc)
    task_stats = {
        "tasks_found": 0,
        "tasks_created": 0,
        "processing_time": 0,
    }

    try:
        logger.info(f"Starting to process note {note_id}")

        # Create session if not provided
        if not session:
            logger.debug("Creating new database session")
            session = SessionLocal()

        # Create repositories if not provided
        if not note_repository:
            logger.debug("Creating new note repository")
            note_repository = NoteRepository(session)

        if not task_repository:
            logger.debug("Creating new task repository")
            task_repository = TaskRepository(session)

        # Get note
        logger.debug(
            f"Fetching note {note_id} from database"
        )
        note = note_repository.get_by_id(note_id)
        if not note:
            raise ValueError(f"Note {note_id} not found")

        logger.info(
            f"Processing note {note_id} with content: {note.content[:100]}..."
        )

        # Update to PROCESSING
        logger.debug(
            f"Updating note {note_id} status to PROCESSING"
        )
        note.processing_status = ProcessingStatus.PROCESSING
        note.updated_at = datetime.now(timezone.utc)
        session.add(note)
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

        # Step 1: Process note with retries
        for attempt in range(max_retries + 1):
            try:
                logger.info(
                    f"Attempt {attempt + 1}/{max_retries + 1} "
                    f"to process note {note_id}"
                )
                result = robo_service.process_note(
                    note.content,
                    context={
                        "type": "note_enrichment",
                        "related_notes": (
                            note.related_notes
                            if hasattr(
                                note, "related_notes"
                            )
                            else []
                        ),
                        "topics": (
                            note.topics
                            if hasattr(note, "topics")
                            else []
                        ),
                    },
                )
                logger.info(
                    f"Successfully processed note {note_id}"
                )
                logger.debug(f"Processing result: {result}")

                # Update note with enrichment data
                note.enrichment_data = {
                    "title": result.metadata["title"],
                    "formatted": result.content,
                    "tokens_used": result.tokens_used,
                    "model_name": result.model_name,
                    "created_at": result.created_at.isoformat(),
                    "metadata": result.metadata,
                }

                # Update note status to COMPLETED
                logger.debug(
                    f"Updating note {note_id} status to COMPLETED"
                )
                note.processing_status = (
                    ProcessingStatus.COMPLETED
                )
                note.processed_at = datetime.now(
                    timezone.utc
                )
                note.updated_at = datetime.now(timezone.utc)
                session.add(note)
                session.commit()

                logger.info(
                    f"Successfully completed note processing for {note_id}"
                )
                break  # Success, exit retry loop

            except Exception as e:
                logger.error(
                    f"Failed to process note {note_id} "
                    f"(attempt {attempt + 1}/{max_retries + 1}): {str(e)}"
                )

                if attempt == max_retries:
                    logger.error(
                        f"All processing attempts failed for note {note_id}"
                    )
                    note.processing_status = (
                        ProcessingStatus.FAILED
                    )
                    note.updated_at = datetime.now(
                        timezone.utc
                    )
                    session.add(note)
                    session.commit()
                    raise RoboServiceError(
                        f"Failed to process note {note_id}: {str(e)}"
                    )

                # Wait before retrying with exponential backoff
                delay = calculate_backoff(attempt + 1)
                logger.info(
                    f"Waiting {delay}s before retry"
                )
                time.sleep(delay)

        # Step 2: Extract tasks (independent step,
        # failures don't affect note status)
        try:
            logger.info(
                f"Starting task extraction for note {note_id}"
            )
            extracted_tasks = robo_service.extract_tasks(
                note.content
            )
            task_stats["tasks_found"] = len(extracted_tasks)

            if task_stats["tasks_found"] > 0:
                logger.info(
                    f"Found {task_stats['tasks_found']} "
                    f"tasks in note {note_id}"
                )

                # Create tasks
                for task_data in extracted_tasks:
                    try:
                        created_at = datetime.now(
                            timezone.utc
                        )
                        task = task_repository.create(
                            content=task_data["content"],
                            source_note_id=note_id,
                            created_at=created_at,
                            updated_at=created_at,
                        )
                        session.add(task)
                        task_stats["tasks_created"] += 1
                        logger.debug(
                            f"Created task from note {note_id}: "
                            f"{task_data['content'][:50]}..."
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to create task from note {note_id}: "
                            f"{str(e)}"
                        )
                        continue

                session.commit()
                logger.info(
                    f"Successfully created {task_stats['tasks_created']} "
                    f"tasks from note {note_id}"
                )
            else:
                logger.info(
                    f"No tasks found in note {note_id}"
                )

        except Exception as e:
            logger.error(
                f"Task extraction failed for note {note_id}: {str(e)}"
            )
            # Task extraction failure is logged but doesn't affect note status

        # Update task extraction stats in note's enrichment data
        note.enrichment_data.update(
            {
                "task_extraction_stats": task_stats,
                "task_extraction_completed_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }
        )
        session.add(note)
        session.commit()

    except Exception as e:
        if not isinstance(
            e, (ValueError, RoboServiceError)
        ):
            logger.error(
                f"Error in process_note_job for note {note_id}: {str(e)}",
                exc_info=True,
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
        task_stats["processing_time"] = duration
        logger.info(
            f"Note {note_id} job completed in {duration}s"
        )
