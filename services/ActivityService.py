"""Service for handling activity-related operations."""

from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from configs.Database import get_db_connection
from domain.exceptions import ActivityValidationError
from repositories.ActivityRepository import (
    ActivityRepository,
)
from repositories.MomentRepository import MomentRepository
from schemas.pydantic.ActivitySchema import (
    ActivityCreate,
    ActivityResponse,
    ActivityUpdate,
    ActivityList,
)
from utils.validation import (
    validate_pagination,
    validate_color,
    validate_activity_schema,
)
from utils.errors.domain_exceptions import (
    handle_domain_exception,
)
from domain.ports.QueueService import QueueService

import logging

logger = logging.getLogger(__name__)


class ActivityService:
    def __init__(
        self, db: Session = Depends(get_db_connection), queue_service: QueueService = Depends()
    ):
        """Initialize the service with database session and queue service.

        Args:
            db (Session): SQLAlchemy database session
            queue_service (QueueService): Queue service for enqueuing activities
        """
        self.db = db
        self.queue_service = queue_service
        self.activity_repository = ActivityRepository(db)
        self.moment_repository = MomentRepository(db)
        logger.info(
            "ActivityService initialized with database session and queue service"
        )

    def _validate_color(self, color: str) -> None:
        """Validate color format.

        Args:
            color: Color string to validate

        Raises:
            HTTPException: If color format is invalid
        """
        try:
            validate_color(color)
        except ValueError:
            raise ActivityValidationError.invalid_color(
                color
            )
        except ActivityValidationError as e:
            raise handle_domain_exception(e)

    def _validate_activity_schema(
        self, schema: Dict
    ) -> None:
        """Validate activity schema structure.

        Args:
            schema: Schema dictionary to validate

        Raises:
            HTTPException: If schema is invalid
        """
        try:
            validate_activity_schema(schema)
        except ValueError as e:
            raise ActivityValidationError.invalid_field_value(
                "activity_schema", str(e)
            )
        except ActivityValidationError as e:
            raise handle_domain_exception(e)

    def _validate_pagination(
        self, page: int, size: int
    ) -> None:
        """Validate pagination parameters using centralized validation.

        Args:
            page (int): Page number to validate
            size (int): Page size to validate

        Raises:
            HTTPException: If validation fails
        """
        try:
            validate_pagination(page, size)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )

    def create_activity(
        self, activity_data: ActivityCreate, user_id: str
    ) -> ActivityResponse:
        """Create a new activity with schema validation

        Args:
            activity_data: Activity data to create
            user_id: ID of the user creating the activity

        Returns:
            Created activity response

        Raises:
            HTTPException: If validation fails
        """
        try:
            logger.info(
                f"Creating activity for user {user_id}"
            )
            logger.debug(f"Activity data: {activity_data}")

            # Validate color and schema
            if activity_data.color:
                self._validate_color(activity_data.color)
            if activity_data.activity_schema:
                self._validate_activity_schema(
                    activity_data.activity_schema
                )

            # Convert to domain model with user_id
            domain_data = activity_data.to_domain(
                str(user_id)
            )

            # Create activity - validation handled by domain model
            activity = self.activity_repository.create(
                instance_or_name=domain_data.name,
                description=domain_data.description,
                activity_schema=domain_data.activity_schema,
                icon=domain_data.icon,
                color=domain_data.color,
                user_id=domain_data.user_id,
            )
            logger.info(
                f"Activity created with ID: {activity.id}"
            )

            # Enqueue activity for processing
            job_id = self.queue_service.enqueue_activity(activity.id)
            if job_id:
                logger.info(f"Activity enqueued for processing with job ID: {job_id}")
            else:
                logger.warning("Failed to enqueue activity for processing")

            # Convert back to response model
            return ActivityResponse.from_orm(activity)
        except ValueError as e:
            logger.error(
                f"Validation error creating activity: {str(e)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            logger.error(
                f"Error creating activity: {str(e)}",
                exc_info=True,
            )
            raise

    def get_activity(
        self, activity_id: int, user_id: str
    ) -> Optional[ActivityResponse]:
        """Get an activity by ID

        Args:
            activity_id: ID of activity to get
            user_id: ID of user requesting the activity

        Returns:
            Activity response if found, None otherwise
        """
        activity = self.activity_repository.get_by_user(
            activity_id,
            str(user_id),  # Ensure user_id is string
        )
        if not activity:
            return None
        return ActivityResponse.from_orm(activity)

    def list_activities(
        self, user_id: str, page: int = 1, size: int = 100
    ) -> ActivityList:
        """List all activities with pagination

        Args:
            user_id: ID of user requesting activities
            page: Page number (1-based)
            size: Maximum number of items per page

        Returns:
            List of activities with pagination metadata
        """
        # Validate pagination parameters
        self._validate_pagination(page, size)

        # Convert page/size to skip/limit for repository
        skip = (page - 1) * size
        limit = size

        activities = (
            self.activity_repository.list_activities(
                user_id=str(
                    user_id
                ),  # Ensure user_id is string
                skip=skip,
                limit=limit,
            )
        )

        # Convert to list of ActivityResponse objects
        activity_responses = [
            ActivityResponse.from_orm(activity)
            for activity in activities
        ]

        total = len(activity_responses)
        pages = (total + size - 1) // size

        # Create and return ActivityList
        return ActivityList(
            items=activity_responses,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    def update_activity(
        self,
        activity_id: int,
        activity_data: ActivityUpdate,
        user_id: str,
    ) -> Optional[ActivityResponse]:
        """Update an activity

        Args:
            activity_id: ID of activity to update
            activity_data: New activity data
            user_id: ID of user updating the activity

        Returns:
            Updated activity response if found, None otherwise
        """
        # Get existing activity
        activity = self.activity_repository.get_by_id(
            activity_id,
            str(user_id),  # Ensure user_id is string
        )
        if not activity:
            return None

        # Validate color if provided
        if activity_data.color:
            self._validate_color(activity_data.color)

        # Validate schema if provided
        if activity_data.activity_schema:
            self._validate_activity_schema(
                activity_data.activity_schema
            )

        # Update activity
        updated = self.activity_repository.update(
            activity_id,
            str(user_id),  # Ensure user_id is string
            activity_data.model_dump(exclude_unset=True),
        )
        if not updated:
            return None

        return ActivityResponse.from_orm(updated)

    def delete_activity(
        self, activity_id: int, user_id: str
    ) -> bool:
        """Delete an activity

        Args:
            activity_id: ID of activity to delete
            user_id: ID of user requesting deletion

        Returns:
            True if activity was deleted, False otherwise
        """
        return self.activity_repository.delete(
            activity_id, str(user_id)
        )

    def validate(self, data: Dict[str, Any]) -> None:
        """Validate activity data.

        Args:
            data: Activity data to validate

        Raises:
            HTTPException: If validation fails
        """
        if "color" in data:
            self._validate_color(data["color"])
        if "activity_schema" in data:
            self._validate_activity_schema(
                data["activity_schema"]
            )
