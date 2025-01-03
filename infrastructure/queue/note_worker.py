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
from services.robo import get_robo_service
from utils.retry import calculate_backoff
from configs.Database import SessionLocal
import orm.NoteModel  # noqa: F401 Required for SQLAlchemy model registry
import orm.UserModel  # noqa: F401 Required for SQLAlchemy model registry
import orm.MomentModel  # noqa: F401 Required for SQLAlchemy model registry
import orm.TaskModel  # noqa: F401 Required for SQLAlchemy model registry
import orm.ActivityModel  # noqa: F401 Required for SQLAlchemy model registry

logger = logging.getLogger(__name__)


def process_note_job(
    note_id: int,
    session: Optional[Session] = None,
    robo_service: Optional[RoboService] = None,
    note_repository: Optional[NoteRepository] = None,
    max_retries: int = 3,
) -> None:
    """Process a note using RoboService.

    Args:
        note_id: ID of note to process
        session: Optional database session
        robo_service: Optional RoboService instance
        note_repository: Optional note repository
        max_retries: Maximum number of retries

    Raises:
        ValueError: If note not found
        RoboServiceError: If processing fails
    """
    session_provided = session is not None
    start_time = datetime.now(timezone.utc)

    try:
        logger.info(f"Starting to process note {note_id}")

        # Create session if not provided
        if not session:
            logger.debug("Creating new database session")
            session = SessionLocal()

        # Create repository if not provided
        if not note_repository:
            logger.debug("Creating new note repository")
            note_repository = NoteRepository(session)

        # Get note
        logger.debug(
            f"Fetching note {note_id} from database"
        )
        note = note_repository.get_by_id(note_id)
        if not note:
            raise ValueError(f"Note {note_id} not found")

        logger.info(
            f"Processing note {note_id} with content: "
            f"{note.content[:100]}..."
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

        for attempt in range(max_retries + 1):
            try:
                # Process the note with enrichment context
                logger.info(
                    f"Attempt {attempt + 1}/{max_retries + 1} "
                    f"to process note {note_id}"
                )
                result = robo_service.process_text(
                    note.content,
                    context={"type": "note_enrichment"},
                )
                logger.info(
                    f"Successfully processed note {note_id}"
                )
                logger.debug(f"Processing result: {result}")

                note.enrichment_data = {
                    "title": result.metadata["title"],
                    "formatted": result.content,
                    "tokens_used": result.tokens_used,
                    "model_name": result.model_name,
                    "created_at": result.created_at.isoformat(),
                    "metadata": result.metadata,
                }

                # Update to COMPLETED
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
                    f"Successfully completed processing note {note_id}"
                )
                return  # Success, exit function

            except Exception as e:
                logger.error(
                    f"Failed to process note {note_id} "
                    f"(attempt {attempt + 1}/{max_retries + 1}): "
                    f"{str(e)}"
                )

                # If this was the last attempt, mark as failed and raise
                if attempt == max_retries:
                    logger.error(
                        f"All attempts failed for note {note_id}"
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

    except Exception as e:
        if not isinstance(
            e, (ValueError, RoboServiceError)
        ):
            logger.error(
                f"Error in process_note_job for note {note_id}: {str(e)}",
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
            f"Note {note_id} processing completed in {duration}s"
        )
