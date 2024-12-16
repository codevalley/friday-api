from typing import List, Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from jsonschema import (
    ValidationError,
    validate as validate_schema,
)
import re

from configs.Database import get_db_connection
from repositories.ActivityRepository import (
    ActivityRepository,
)
from repositories.MomentRepository import MomentRepository
from schemas.pydantic.ActivitySchema import (
    ActivityCreate,
    ActivityUpdate,
    ActivityList,
    ActivityResponse,
)
from schemas.graphql.types.Activity import Activity
import json


class ActivityService:
    def __init__(
        self, db: Session = Depends(get_db_connection)
    ):
        """Initialize the service with database session

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.activity_repository = ActivityRepository(db)
        self.moment_repository = MomentRepository(db)

    def _validate_pagination(
        self, page: int, size: int
    ) -> None:
        """Validate pagination parameters

        Args:
            page: Page number (1-based)
            size: Items per page

        Raises:
            HTTPException: If parameters are invalid
        """
        if page < 1:
            raise HTTPException(
                status_code=400,
                detail="Page number must be positive",
            )
        if size < 1 or size > 100:
            raise HTTPException(
                status_code=400,
                detail="Page size must be between 1 and 100",
            )

    def _validate_color(self, color: str) -> None:
        """Validate hex color code format

        Args:
            color: Color code to validate

        Raises:
            HTTPException: If color format is invalid
        """
        if not re.match("^#[0-9A-Fa-f]{6}$", color):
            raise HTTPException(
                status_code=400,
                detail="Color must be a valid hex code (e.g. #FF0000)",
            )

    def _validate_activity_schema(
        self, schema: dict
    ) -> None:
        """Validate activity schema format

        Args:
            schema: JSON schema to validate

        Raises:
            HTTPException: If schema is invalid
        """
        try:
            # Basic JSON Schema validation
            meta_schema = {
                "type": "object",
                "required": ["type", "properties"],
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["object"],
                    },
                    "properties": {"type": "object"},
                },
            }
            validate_schema(
                instance=schema, schema=meta_schema
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid activity schema format: {str(e)}",
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
            HTTPException: If schema validation fails
        """
        try:
            # Convert to domain model
            domain_data = activity_data.to_domain()
            domain_data.user_id = str(
                user_id
            )  # Ensure user_id is string

            # Validate color format
            self._validate_color(domain_data.color)

            # Validate activity schema
            self._validate_activity_schema(
                domain_data.activity_schema
            )

            # Create activity
            activity = self.activity_repository.create(
                instance_or_name=domain_data.name,
                description=domain_data.description,
                activity_schema=domain_data.activity_schema,
                icon=domain_data.icon,
                color=domain_data.color,
                user_id=domain_data.user_id,
            )

            # Convert back to response model
            return ActivityResponse.from_orm(activity)
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid activity data: {str(e)}",
            )

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
            activity_data: Updated activity data
            user_id: ID of user updating the activity

        Returns:
            Updated activity response if found, None otherwise

        Raises:
            HTTPException: If schema validation fails
        """
        # Get existing activity
        activity = self.activity_repository.get_by_id(
            activity_id,
            str(user_id),  # Ensure user_id is string
        )
        if not activity:
            return None

        try:
            # Update fields - validation handled by Pydantic
            update_data = activity_data.dict(
                exclude_unset=True
            )
            updated = self.activity_repository.update(
                activity_id=activity_id,
                user_id=str(
                    user_id
                ),  # Ensure user_id is string
                **update_data,
            )
            if not updated:
                return None
            return ActivityResponse.from_orm(updated)
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid activity data: {str(e)}",
            )

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
        """Create activity for GraphQL

        Args:
            activity_data: Activity data to create (GraphQL input type)
            user_id: ID of user creating the activity

        Returns:
            Created activity in GraphQL format

        Raises:
            HTTPException: If validation fails
        """
        # Convert activity_schema to dict if it's a string
        activity_schema = activity_data.activitySchema
        if isinstance(activity_schema, str):
            try:
                activity_schema = json.loads(activity_schema)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid activity schema format: must be valid JSON",
                )

        # Validate the schema
        self._validate_activity_schema(activity_schema)

        activity = self.activity_repository.create(
            name=activity_data.name,
            description=activity_data.description,
            activity_schema=activity_schema,
            icon=activity_data.icon,
            color=activity_data.color,
            user_id=str(user_id),  # Ensure user_id is string
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
        """Update activity for GraphQL

        Args:
            activity_id: ID of activity to update
            activity_data: Updated activity data (GraphQL input type)
            user_id: ID of user updating the activity

        Returns:
            Updated activity in GraphQL format

        Raises:
            HTTPException: If validation fails or activity not found
        """
        # Get existing activity to ensure it exists
        existing = self.activity_repository.get_by_id(
            activity_id,
            str(user_id),  # Ensure user_id is string
        )
        if not existing:
            raise HTTPException(
                status_code=404, detail="Activity not found"
            )

        # Convert activity_schema to dict if it's a string
        if activity_data.activitySchema:
            try:
                activity_schema = json.loads(activity_data.activitySchema)
                # Validate the schema before updating
                self._validate_activity_schema(activity_schema)
                activity_data.activitySchema = activity_schema
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid activity schema format: must be valid JSON",
                )

        # Create an ActivityUpdate instance with the correct field names
        update_data = ActivityUpdate(
            name=activity_data.name,
            description=activity_data.description,
            activity_schema=activity_data.activitySchema,
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
