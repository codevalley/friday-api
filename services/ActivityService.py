from typing import List, Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError
import json

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
            HTTPException: If JSON schema validation fails
        """
        try:
            # Validate that the activity_schema is a valid JSON Schema
            Draft7Validator.check_schema(
                activity_data.activity_schema
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON Schema: {str(e)}",
            )

        activity = self.activity_repository.create(
            name=activity_data.name,
            description=activity_data.description,
            activity_schema=activity_data.activity_schema,
            icon=activity_data.icon,
            color=activity_data.color,
            user_id=str(
                user_id
            ),  # Ensure user_id is string
        )
        return ActivityResponse.from_orm(activity)

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
        activity = self.activity_repository.get_by_id(
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
            HTTPException: If JSON schema validation fails
        """
        # Get existing activity
        activity = self.activity_repository.get_by_id(
            activity_id,
            str(user_id),  # Ensure user_id is string
        )
        if not activity:
            return None

        # Update fields
        update_data = activity_data.dict(exclude_unset=True)
        if "activity_schema" in update_data:
            try:
                Draft7Validator.check_schema(
                    update_data["activity_schema"]
                )
            except ValidationError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid JSON Schema: {str(e)}",
                )

        # Update the activity
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
        self, activity_data: ActivityCreate, user_id: str
    ) -> Activity:
        """Create activity for GraphQL

        Args:
            activity_data: Activity data to create
            user_id: ID of user creating the activity

        Returns:
            Created activity in GraphQL format

        Raises:
            HTTPException: If validation fails
        """
        activity = self.activity_repository.create(
            name=activity_data.name,
            description=activity_data.description,
            activity_schema=activity_data.activity_schema,
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
        activity_data: ActivityUpdate,
        user_id: str,
    ) -> Activity:
        """Update activity for GraphQL

        Args:
            activity_id: ID of activity to update
            activity_data: Updated activity data
            user_id: ID of user updating the activity

        Returns:
            Updated activity in GraphQL format

        Raises:
            HTTPException: If validation fails or activity not found
        """
        # Convert activity_schema to dict if it's a string
        if activity_data.activity_schema and isinstance(
            activity_data.activity_schema, str
        ):
            activity_data.activity_schema = json.loads(
                activity_data.activity_schema
            )

        activity = self.update_activity(
            activity_id,
            activity_data,
            str(user_id),  # Ensure user_id is string
        )
        if not activity:
            raise HTTPException(
                status_code=404, detail="Activity not found"
            )
        return Activity.from_db(activity)
