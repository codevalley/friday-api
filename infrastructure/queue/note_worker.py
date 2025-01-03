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
from services.TestRoboService import get_robo_service
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
        # Create session if not provided
        if not session:
            session = SessionLocal()

        # Create repository if not provided
        if not note_repository:
            note_repository = NoteRepository(session)

        # Get note
        note = note_repository.get_by_id(note_id)
        if not note:
            raise ValueError(f"Note {note_id} not found")

        logger.info(f"Processing note {note_id}")

        # Update to PROCESSING
        note.processing_status = ProcessingStatus.PROCESSING
        note.updated_at = datetime.now(timezone.utc)
        session.add(note)
        session.commit()

        # Create RoboService if not provided
        if not robo_service:
            robo_service = get_robo_service()

        for attempt in range(max_retries + 1):
            try:
                # Process the note
                result = robo_service.process_text(
                    note.content
                )
                note.enrichment_data = {
                    "content": result.content,
                    "metadata": result.metadata,
                    "tokens_used": result.tokens_used,
                    "model_name": result.model_name,
                    "created_at": result.created_at.isoformat(),
                }

                # Update to COMPLETED
                note.processing_status = (
                    ProcessingStatus.COMPLETED
                )
                note.processed_at = datetime.now(
                    timezone.utc
                )
                note.updated_at = datetime.now(timezone.utc)
                session.add(note)
                session.commit()
                return  # Success, exit function

            except Exception as e:
                logger.error(
                    f"Failed to process note {note_id} "
                    f"(attempt {attempt + 1}/{max_retries + 1}): "
                    f"{str(e)}"
                )

                # If this was the last attempt, mark as failed and raise
                if attempt == max_retries:
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
                time.sleep(delay)

    except Exception as e:
        if not isinstance(
            e, (ValueError, RoboServiceError)
        ):
            logger.error(
                f"Error in process_note_job for note {note_id}: {str(e)}"
            )
        raise

    finally:
        # Only close the session if we created it
        if not session_provided and session:
            session.close()

        duration = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()
        logger.info(
            f"Note {note_id} processing completed in {duration}s"
        )
