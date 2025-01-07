"""Worker for processing activity schemas."""

import logging
from datetime import datetime, UTC
from typing import Dict, Any

from sqlalchemy.orm import Session

from configs.Database import get_db_connection
from configs.RoboConfig import get_robo_service
from domain.exceptions import RoboAPIError
from orm.ActivityModel import Activity

logger = logging.getLogger(__name__)

def process_activity(
    activity_id: int,
    user_id: str,
    activity_schema: Dict[str, Any]
) -> None:
    """Process an activity's schema for rendering suggestions.

    Args:
        activity_id: ID of activity to process
        user_id: Owner of the activity
        activity_schema: Schema to analyze
    """
    logger.info(f"Processing activity {activity_id}")

    # Get database session
    db = next(get_db_connection())

    try:
        # Update status to PROCESSING
        activity = db.query(Activity).filter(
            Activity.id == activity_id,
            Activity.user_id == user_id
        ).first()

        if not activity:
            logger.error(f"Activity {activity_id} not found")
            return

        activity.processing_status = 'PROCESSING'
        db.commit()

        # Get RoboService and process
        robo_service = get_robo_service()
        render_suggestion = robo_service.analyze_activity_schema(
            activity_schema
        )

        # Update activity with results
        activity.schema_render = render_suggestion
        activity.processing_status = 'COMPLETED'
        activity.processed_at = datetime.now(UTC)
        db.commit()

        logger.info(f"Successfully processed activity {activity_id}")

    except RoboAPIError as e:
        logger.error(f"RoboAPI error processing activity {activity_id}: {str(e)}")
        activity.processing_status = 'FAILED'
        db.commit()
    except Exception as e:
        logger.error(f"Error processing activity {activity_id}: {str(e)}")
        activity.processing_status = 'FAILED'
        db.commit()
    finally:
        db.close()
