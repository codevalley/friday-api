from typing import List, Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
import jsonschema
from jsonschema import ValidationError
import json

from configs.Database import get_db_connection
from repositories.ActivityRepository import (
    ActivityRepository,
)
from repositories.MomentRepository import MomentRepository
from schemas.pydantic.ActivitySchema import (
    ActivityCreate,
    ActivityUpdate,
    ActivityResponse,
)
from schemas.graphql.Activity import (
    Activity as ActivityType,
)


class ActivityService:
    def __init__(
        self, db: Session = Depends(get_db_connection)
    ):
        self.db = db
        self.activity_repository = ActivityRepository(db)
        self.moment_repository = MomentRepository(db)

    def create_activity(
        self, activity_data: ActivityCreate, user_id: str
    ) -> ActivityResponse:
        """Create a new activity with schema validation"""
        try:
            # Validate that the activity_schema is a valid JSON Schema
            jsonschema.Draft7Validator.check_schema(
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
            user_id=user_id,
        )
        return ActivityResponse.from_orm(activity)

    def get_activity(
        self, activity_id: int, user_id: str
    ) -> Optional[ActivityResponse]:
        """Get an activity by ID"""
        activity = self.activity_repository.get_by_id(
            activity_id, user_id
        )
        if not activity:
            return None
        return ActivityResponse.from_orm(activity)

    def list_activities(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[ActivityResponse]:
        """List all activities with pagination"""
        activities = (
            self.activity_repository.list_activities(
                user_id=user_id, skip=skip, limit=limit
            )
        )
        return [
            ActivityResponse.from_orm(a) for a in activities
        ]

    def update_activity(
        self,
        activity_id: int,
        activity_data: ActivityUpdate,
        user_id: str,
    ) -> Optional[ActivityResponse]:
        """Update an activity"""
        # Get existing activity
        activity = self.activity_repository.get_by_id(
            activity_id, user_id
        )
        if not activity:
            return None

        # Update fields
        update_data = activity_data.dict(exclude_unset=True)
        if "activity_schema" in update_data:
            try:
                jsonschema.Draft7Validator.check_schema(
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
            user_id=user_id,
            **update_data,
        )
        if not updated:
            return None
        return ActivityResponse.from_orm(updated)

    def delete_activity(
        self, activity_id: int, user_id: str
    ) -> bool:
        """Delete an activity"""
        return self.activity_repository.delete(
            activity_id, user_id
        )

    # GraphQL specific methods
    def create_activity_graphql(
        self, activity_data: ActivityCreate, user_id: str
    ) -> ActivityType:
        """Create activity for GraphQL"""
        activity = self.activity_repository.create(
            name=activity_data.name,
            description=activity_data.description,
            activity_schema=activity_data.activity_schema,
            icon=activity_data.icon,
            color=activity_data.color,
            user_id=user_id,
        )
        return ActivityType.from_db(activity)

    def get_activity_graphql(
        self, activity_id: int, user_id: str
    ) -> Optional[ActivityType]:
        """Get an activity by ID for GraphQL"""
        activity = self.activity_repository.get_by_id(
            activity_id, user_id
        )
        if not activity:
            return None
        return ActivityType.from_db(activity)

    def list_activities_graphql(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[ActivityType]:
        """List all activities with pagination for GraphQL"""
        activities = (
            self.activity_repository.list_activities(
                user_id=user_id, skip=skip, limit=limit
            )
        )
        return [ActivityType.from_db(a) for a in activities]

    def update_activity_graphql(
        self,
        activity_id: int,
        activity_data: ActivityUpdate,
        user_id: str,
    ) -> ActivityType:
        """Update activity for GraphQL"""
        # Convert activity_schema to dict if it's a string
        if activity_data.activity_schema and isinstance(
            activity_data.activity_schema, str
        ):
            activity_data.activity_schema = json.loads(
                activity_data.activity_schema
            )

        activity = self.update_activity(
            activity_id, activity_data, user_id
        )
        return ActivityType.from_db(activity)
