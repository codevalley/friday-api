"""Worker script for processing notes from the queue."""

import logging
import random
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from configs.Database import SessionLocal
from domain.values import ProcessingStatus
from domain.exceptions import RoboServiceError
from repositories.NoteRepository import NoteRepository
from services.RoboService import RoboService
from configs.RoboConfig import get_robo_settings

logger = logging.getLogger(__name__)


def get_robo_service() -> RoboService:
    """Get a configured RoboService instance.

    Returns:
        RoboService: Configured service instance
    """
    config = get_robo_settings().to_domain_config()
    return RoboService(config)


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    jitter: float = 0.1,
) -> float:
    """Calculate delay with exponential backoff and jitter.

    Args:
        attempt: Current attempt number (1-based)
        base_delay: Base delay in seconds
        jitter: Jitter factor (0-1) to add randomness

    Returns:
        Delay in seconds
    """
    # Calculate exponential backoff
    delay = min(
        base_delay * (2 ** (attempt - 1)), 60
    )  # Cap at 60 seconds
    # Add jitter
    jitter_amount = delay * jitter
    return delay + random.uniform(
        -jitter_amount, jitter_amount
    )


def process_note_job(
    note_id: int,
    session: Session = None,
    robo_service: RoboService = None,
    note_repository: NoteRepository = None,
    max_retries: int = 3,
) -> None:
    """
    Process a note job from the queue.

    Args:
        note_id: The ID of the note to process
        session: The database session (optional, will create if not provided)
        robo_service: The RoboService instance to use for processing
            (optional, will create if not provided)
        note_repository: The NoteRepository instance to use for database
            operations (optional, will create if not provided)
        max_retries: Maximum number of retry attempts

    Raises:
        ValueError: If note is not found
        RoboServiceError: If processing fails after all retries
    """
    # Use provided session or create a new one
    session_provided = session is not None
    if not session:
        session = SessionLocal()

    try:
        # Create repository if not provided
        if not note_repository:
            note_repository = NoteRepository(session)

        # Get the note within this session
        note = note_repository.get_by_id(note_id)
        if not note:
            logger.error(f"Note {note_id} not found")
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
                enrichment_data = robo_service.enrich_note(
                    note.content
                )
                note.enrichment_data = enrichment_data

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
