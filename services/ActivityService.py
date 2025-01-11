"""Activity service implementation."""

import logging
from typing import Optional

from domain.activity import ActivityData
from repositories.ActivityRepository import (
    ActivityRepository,
)
from domain.ports.QueueService import QueueService
from domain.exceptions import (
    ActivityServiceError,
    ErrorCode,
)
from schemas.pydantic.ActivitySchema import ActivityList
from orm.ActivityModel import Activity
from domain.values import ProcessingStatus

logger = logging.getLogger(__name__)


class ActivityService:
    """Service for managing activities."""

    def __init__(
        self,
        repository: ActivityRepository,
        queue_service: QueueService,
    ):
        """Initialize activity service.

        Args:
            repository: Repository for activity persistence
            queue_service: Queue service for async processing
        """
        self.repository = repository
        self.queue_service = queue_service

    def create_activity(
        self, data: ActivityData, user_id: str
    ) -> ActivityData:
        """Create activity and queue for processing.

        Args:
            data: Activity data to create
            user_id: ID of user creating activity

        Returns:
            Created activity with processing status

        Raises:
            ActivityServiceError: If creation fails
        """
        try:
            # Convert to domain model with user ID
            activity_data = data.to_domain(user_id=user_id)

            # Convert domain model to ORM model
            activity = Activity(
                name=activity_data.name,
                description=activity_data.description,
                activity_schema=activity_data.activity_schema,
                icon=activity_data.icon,
                color=activity_data.color,
                user_id=activity_data.user_id,
                processing_status=ProcessingStatus.PENDING,
            )

            # Create activity
            activity = self.repository.create(activity)

            try:
                # Queue for processing
                job_id = (
                    self.queue_service.enqueue_activity(
                        activity.id
                    )
                )

                if not job_id:
                    logger.error(
                        f"Failed to queue activity {activity.id}"
                    )
                    # Update status if queueing failed
                    activity = self.repository.update(
                        activity.id,
                        {
                            "processing_status": ProcessingStatus.FAILED
                        },
                    )

            except Exception as e:
                logger.error(
                    f"Error queueing activity {activity.id}: {str(e)}"
                )
                # Update status if queueing failed
                activity = self.repository.update(
                    activity.id,
                    {
                        "processing_status": ProcessingStatus.FAILED
                    },
                )

            # Return activity regardless of queue status
            return ActivityData.from_orm(activity)

        except Exception as e:
            logger.error(
                f"Error creating activity: {str(e)}"
            )
            raise ActivityServiceError(
                message=f"Failed to create activity: {str(e)}",
                code=ErrorCode.TASK_INVALID_STATUS,
            )

    def list_activities(
        self, user_id: str, page: int = 1, size: int = 10
    ) -> ActivityList:
        """List activities for a user with pagination.

        Args:
            user_id: ID of user to list activities for
            page: Page number (1-based)
            size: Number of items per page

        Returns:
            Paginated list of activities
        """
        try:
            result = self.repository.list_by_user(
                user_id=user_id,
                page=page,
                size=size,
            )

            # Calculate total pages
            pages = (result["total"] + size - 1) // size

            return ActivityList(
                items=result["items"],
                total=result["total"],
                page=page,
                size=size,
                pages=pages,
            )
        except Exception as e:
            logger.error(
                f"Error listing activities: {str(e)}"
            )
            raise ActivityServiceError(
                message=f"Failed to list activities: {str(e)}",
                code=ErrorCode.TASK_INVALID_STATUS,
            )

    def get_activity(
        self, activity_id: int, user_id: str
    ) -> ActivityData:
        """Get activity by ID.

        Args:
            activity_id: ID of activity to get
            user_id: ID of user requesting activity

        Returns:
            Activity data

        Raises:
            ActivityServiceError: If activity not found or access denied
        """
        activity = self.repository.get_by_id(
            activity_id, user_id
        )
        if not activity:
            raise ActivityServiceError(
                message=f"Activity {activity_id} not found",
                code=ErrorCode.TASK_INVALID_REFERENCE,
            )
        return ActivityData.from_orm(activity)

    def get_processing_status(
        self, activity_id: int, user_id: str
    ) -> dict:
        """Get activity processing status.

        Args:
            activity_id: ID of activity to check
            user_id: ID of user requesting status

        Returns:
            Dict containing:
                - status: Current processing status
                - processed_at: When processing completed (if done)
                - schema_render: Rendering suggestions (if done)
        """
        activity = self.repository.get_by_id(
            activity_id, user_id
        )
        if not activity:
            raise ActivityServiceError(
                message=f"Activity {activity_id} not found",
                code=ErrorCode.TASK_INVALID_REFERENCE,
            )

        return {
            "status": activity.processing_status,
            "processed_at": activity.processed_at,
            "schema_render": activity.schema_render,
        }

    def retry_processing(
        self, activity_id: int, user_id: str
    ) -> Optional[str]:
        """Retry processing for failed activities.

        Args:
            activity_id: ID of activity to retry
            user_id: ID of user requesting retry

        Returns:
            Optional[str]: New job ID if queued successfully

        Raises:
            ActivityServiceError: If activity not found or retry fails
        """
        activity = self.repository.get_by_id(
            activity_id, user_id
        )
        if not activity:
            raise ActivityServiceError(
                message=f"Activity {activity_id} not found",
                code=ErrorCode.TASK_INVALID_REFERENCE,
            )

        if activity.processing_status not in [
            "FAILED",
            "SKIPPED",
        ]:
            raise ActivityServiceError(
                message=f"Activity {activity_id} is not in a failed state",
                code=ErrorCode.TASK_INVALID_STATUS,
            )

        # Update status and queue
        self.repository.update(
            activity_id,
            {
                "processing_status": "PENDING",
                "processed_at": None,
                "schema_render": None,
            },
        )

        job_id = self.queue_service.enqueue_activity(
            activity_id
        )

        if not job_id:
            raise ActivityServiceError(
                message=f"Failed to queue activity {activity_id} for retry",
                code=ErrorCode.TASK_INVALID_STATUS,
            )

        return job_id
