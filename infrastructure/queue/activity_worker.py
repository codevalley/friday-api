"""Worker for processing activity schemas."""

import logging
from datetime import datetime, UTC
from typing import Optional
from sqlalchemy.orm import Session

from configs.Database import SessionLocal
from services.robo import get_robo_service
from domain.exceptions import RoboAPIError
from domain.values import ProcessingStatus
from domain.robo import RoboService
import orm.UserModel  # noqa: F401 Required for SQLAlchemy model registry
import orm.NoteModel  # noqa: F401 Required for SQLAlchemy model registry
import orm.ActivityModel  # noqa: F401 Required for SQLAlchemy model registry
import orm.MomentModel  # noqa: F401 Required for SQLAlchemy model registry
import orm.TaskModel  # noqa: F401 Required for SQLAlchemy model registry
from orm.ActivityModel import Activity

logger = logging.getLogger(__name__)
# Reduce SQLAlchemy logging
logging.getLogger("sqlalchemy.engine").setLevel(
    logging.WARNING
)


def process_activity_job(
    activity_id: int,
    session: Optional[Session] = None,
    robo_service: Optional[RoboService] = None,
) -> None:
    """Process an activity's schema for rendering suggestions.

    Args:
        activity_id: ID of the activity to process
        session: Optional database session
        robo_service: Optional RoboService instance
    """
    logger.info(
        f"Starting to process activity {activity_id}"
    )
    session_provided = session is not None
    start_time = datetime.now(UTC)

    try:
        # Create session if not provided
        if not session:
            session = SessionLocal()

        # Get activity
        activity = (
            session.query(Activity)
            .filter(Activity.id == activity_id)
            .first()
        )

        if not activity:
            logger.error(
                f"Activity {activity_id} not found"
            )
            return

        # Update status to PROCESSING
        activity.processing_status = (
            ProcessingStatus.PROCESSING
        )
        activity.updated_at = datetime.now(UTC)
        session.add(activity)
        session.commit()
        logger.info(
            f"Activity {activity_id} status set to PROCESSING"
        )

        # Create RoboService if not provided
        if not robo_service:
            robo_service = get_robo_service()

        logger.info(
            f"Analyzing schema for activity {activity_id}"
        )
        render_suggestion = (
            robo_service.analyze_activity_schema(
                activity.activity_schema
            )
        )

        # Update activity with results
        activity.schema_render = render_suggestion
        activity.processing_status = (
            ProcessingStatus.COMPLETED
        )
        activity.processed_at = datetime.now(UTC)
        activity.updated_at = datetime.now(UTC)
        session.add(activity)
        session.commit()
        logger.info(
            f"Activity {activity_id} processing completed successfully"
        )

    except RoboAPIError as e:
        logger.error(
            f"RoboAPI error processing activity {activity_id}: {str(e)}"
        )
        if activity:
            activity.processing_status = (
                ProcessingStatus.FAILED
            )
            activity.updated_at = datetime.now(UTC)
            session.add(activity)
            session.commit()
    except Exception as e:
        logger.error(
            f"Error processing activity {activity_id}: {str(e)}",
            exc_info=True,
        )
        if activity:
            activity.processing_status = (
                ProcessingStatus.FAILED
            )
            activity.updated_at = datetime.now(UTC)
            session.add(activity)
            session.commit()
    finally:
        # Only close the session if we created it
        if not session_provided and session:
            session.close()

        duration = (
            datetime.now(UTC) - start_time
        ).total_seconds()
        logger.info(
            f"Activity {activity_id} processing finished in {duration:.2f}s"
        )
