"""Worker for processing activity schemas."""

import time
import logging
from datetime import datetime, UTC

from domain.values import ProcessingStatus
from domain.exceptions import RoboAPIError, RoboServiceError
from orm.ActivityModel import Activity
from configs.Database import SessionLocal
from services.robo import get_robo_service

# Required for SQLAlchemy model registry
import orm.UserModel  # noqa: F401
import orm.TopicModel  # noqa: F401
import orm.NoteModel  # noqa: F401
import orm.MomentModel  # noqa: F401
import orm.TaskModel  # noqa: F401
import orm.ActivityModel  # noqa: F401

logger = logging.getLogger(__name__)
# Reduce SQLAlchemy logging
logging.getLogger("sqlalchemy.engine").setLevel(
    logging.WARNING
)


def process_activity_job(
    activity_id: int,
    session=None,
    robo_service=None,
    max_retries: int = 3,
) -> None:
    """Process an activity job.

    Args:
        activity_id: ID of the activity to process
        session: Optional database session
        robo_service: Optional service for processing activities (for testing)
        max_retries: Maximum number of retries for processing errors

    Raises:
        ValueError: If activity not found
        RoboAPIError: If processing fails with API error
        RoboServiceError: If processing fails with other errors
    """
    start_time = time.time()
    logger.info(
        f"Starting to process activity {activity_id}"
    )

    # Create robo_service instance if not provided
    if robo_service is None:
        robo_service = get_robo_service()

    # Create session if not provided
    session_created = False
    if session is None:
        session = SessionLocal()
        session_created = True

    activity = None
    try:
        # Get activity
        activity = (
            session.query(Activity)
            .filter(Activity.id == activity_id)
            .first()
        )

        if activity is None:
            raise ValueError(
                f"Failed to process activity {activity_id}"
            )

        # Process activity schema
        retries = 0
        while retries < max_retries:
            try:
                schema_render = (
                    robo_service.analyze_activity_schema(
                        activity.activity_schema
                    )
                )
                activity.schema_render = schema_render
                activity.processing_status = (
                    ProcessingStatus.COMPLETED
                )
                activity.processed_at = datetime.now(UTC)
                session.add(activity)
                session.commit()
                break
            except RoboAPIError as e:
                retries += 1
                logger.error(
                    f"Error processing activity {activity_id} "
                    f"(attempt {retries}): {str(e)}"
                )
                if retries < max_retries:
                    time.sleep(
                        2**retries
                    )  # Exponential backoff
                else:
                    activity.processing_status = (
                        ProcessingStatus.FAILED
                    )
                    session.add(activity)
                    session.commit()
                    raise RoboServiceError(
                        f"Failed to process activity {activity_id}: {str(e)}"
                    )
            except Exception as e:
                retries += 1
                logger.error(
                    f"Error processing activity {activity_id} "
                    f"(attempt {retries}): {str(e)}"
                )
                if retries < max_retries:
                    time.sleep(
                        2**retries
                    )  # Exponential backoff
                else:
                    activity.processing_status = (
                        ProcessingStatus.FAILED
                    )
                    session.add(activity)
                    session.commit()
                    raise RoboServiceError(
                        f"Failed to process activity {activity_id}"
                    ) from e

    except Exception as e:
        if activity is not None:
            activity.processing_status = (
                ProcessingStatus.FAILED
            )
            session.add(activity)
            session.commit()
        raise e

    finally:
        if session_created:
            session.close()

        duration = time.time() - start_time
        logger.info(
            f"Activity {activity_id} processing finished in {duration:.2f}s"
        )
