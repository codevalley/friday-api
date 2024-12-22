"""Service for handling activity-related operations."""

import json
from typing import Dict, Any, List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from configs.Database import get_db_connection
from domain.activity import ActivityData
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
from schemas.graphql.types.Activity import Activity
from utils.validation import (
    validate_pagination,
    validate_color,
    validate_activity_schema,
)
from utils.errors.domain_exceptions import (
    handle_domain_exception,
)

import logging

logger = logging.getLogger(__name__)


class ActivityService:
    def __init__(
        self, db: Session = Depends(get_db_connection)
    ):
        """Initialize the service with database session.

        Args:
            db (Session): SQLAlchemy database session
        """
        self.db = db
        self.activity_repository = ActivityRepository(db)
        self.moment_repository = MomentRepository(db)
        logger.info(
            "ActivityService initialized with database session"
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
            user_id: ID of user deleting the activity

        Returns:
            True if activity was deleted, False otherwise
        """
        return self.activity_repository.delete(
            activity_id,
            str(user_id),  # Ensure user_id is string
        )

    # GraphQL specific methods
    def create_activity_graphql(
        self, activity_data, user_id: str
    ) -> Activity:
        """Create activity for GraphQL"""
        # Handle activity schema that could be either string or dict
        activity_schema = activity_data.activitySchema
        if isinstance(activity_schema, str):
            try:
                activity_schema = json.loads(
                    activity_schema
                )
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid activity schema format: "
                        "must be valid JSON"
                    ),
                )
        elif not isinstance(activity_schema, dict):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Activity schema must be either "
                    "a JSON string or a dictionary"
                ),
            )

        # Validate schema
        self._validate_activity_schema(activity_schema)

        # Create activity
        activity = self.activity_repository.create(
            name=activity_data.name,
            description=activity_data.description,
            activity_schema=activity_schema,
            icon=activity_data.icon,
            color=activity_data.color,
            user_id=str(
                user_id
            ),  # Ensure user_id is string
        )
        return Activity.from_db(activity)

    def get_activity_graphql(
        self, activity_id: int, user_id: str
    ) -> Optional[Activity]:
        """Get an activity by ID for GraphQL

        Args:
            activity_id: ID of activity to get
            user_id: ID of user requesting the activity

        Returns:
            Activity in GraphQL format if found, None otherwise
        """
        activity = self.activity_repository.get_by_id(
            activity_id,
            str(user_id),  # Ensure user_id is string
        )
        if not activity:
            return None
        return Activity.from_db(activity)

    def list_activities_graphql(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Activity]:
        """List all activities with pagination for GraphQL

        Args:
            user_id: ID of user requesting activities
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of activities in GraphQL format
        """
        activities = (
            self.activity_repository.list_activities(
                user_id=str(
                    user_id
                ),  # Ensure user_id is string
                skip=skip,
                limit=limit,
            )
        )
        return [Activity.from_db(a) for a in activities]

    def update_activity_graphql(
        self,
        activity_id: int,
        activity_data,
        user_id: str,
    ) -> Activity:
        """Update activity for GraphQL"""
        activity_schema = None
        if activity_data.activitySchema:
            if isinstance(
                activity_data.activitySchema, str
            ):
                try:
                    activity_schema = json.loads(
                        activity_data.activitySchema
                    )
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Invalid activity schema format: "
                            "must be valid JSON"
                        ),
                    )
            elif isinstance(
                activity_data.activitySchema, dict
            ):
                activity_schema = (
                    activity_data.activitySchema
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Activity schema must be either "
                        "a JSON string or a dictionary"
                    ),
                )

            # Validate schema
            self._validate_activity_schema(activity_schema)

        # Create update data
        update_data = ActivityUpdate(
            name=activity_data.name,
            description=(activity_data.description),
            activity_schema=activity_schema,
            icon=activity_data.icon,
            color=activity_data.color,
        )

        # Update the activity
        updated = self.update_activity(
            activity_id,
            update_data,
            str(user_id),  # Ensure user_id is string
        )
        if not updated:
            raise HTTPException(
                status_code=404, detail="Activity not found"
            )
        return Activity.from_db(updated)

    def to_graphql_json(
        self, activity_data: ActivityData
    ) -> Dict[str, Any]:
        """Convert activity data to GraphQL-compatible JSON format.

        Args:
            activity_data: Activity domain model to convert

        Returns:
            GraphQL-compatible dictionary representation
        """
        return json.loads(
            json.dumps(
                {
                    "id": activity_data.id,
                    "name": activity_data.name,
                    "color": activity_data.color,
                    "activitySchema": activity_data.activity_schema,
                }
            )
        )

    def validate(self, data: Dict[str, Any]) -> None:
        """Validate activity data.

        Args:
            data: Data to validate

        Raises:
            HTTPException: If validation fails
        """
        try:
            if "color" in data:
                validate_color(data["color"])

            if "schema" in data:
                validate_activity_schema(data["schema"])
        except ValueError as e:
            raise ActivityValidationError.invalid_field_value(
                "data", str(e)
            )
        except ActivityValidationError as e:
            raise handle_domain_exception(e)
