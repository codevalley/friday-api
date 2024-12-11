from typing import List, Optional, Dict
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
import jsonschema
from jsonschema import ValidationError

from configs.Database import get_db_connection
from repositories.ActivityRepository import ActivityRepository
from repositories.MomentRepository import MomentRepository
from schemas.pydantic.ActivitySchema import ActivityCreate, ActivityUpdate
from schemas.graphql.Activity import Activity as ActivityType


class ActivityService:
    def __init__(self, db: Session = Depends(get_db_connection)):
        self.db = db
        self.activity_repository = ActivityRepository(db)
        self.moment_repository = MomentRepository(db)

    def create_activity(self, activity_data: ActivityCreate) -> ActivityType:
        """Create a new activity with schema validation"""
        try:
            # Validate that the activity_schema is a valid JSON Schema
            jsonschema.Draft7Validator.check_schema(activity_data.activity_schema)
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON Schema in activity_schema: {str(e)}"
            )

        activity = self.activity_repository.create(
            name=activity_data.name,
            description=activity_data.description,
            activity_schema=activity_data.activity_schema,
            icon=activity_data.icon,
            color=activity_data.color
        )

        return ActivityType.from_db(activity)

    def get_activity(self, activity_id: int) -> Optional[ActivityType]:
        """Get an activity by ID"""
        activity = self.activity_repository.validate_existence(activity_id)
        moment_count = self.moment_repository.get_activity_moments_count(activity_id)
        activity.moment_count = moment_count
        return ActivityType.from_db(activity) if activity else None

    def list_activities(self, skip: int = 0, limit: int = 100) -> List[ActivityType]:
        """List all activities with their moment counts"""
        activities = self.activity_repository.list_all(skip=skip, limit=limit)
        for activity in activities:
            moment_count = self.moment_repository.get_activity_moments_count(activity.id)
            activity.moment_count = moment_count
        return [ActivityType.from_db(activity) for activity in activities]

    def update_activity(self, activity_id: int, activity_data: ActivityUpdate) -> Optional[ActivityType]:
        """Update an activity"""
        # Validate existence
        self.activity_repository.validate_existence(activity_id)

        # If activity_schema is being updated, validate it
        if activity_data.activity_schema:
            try:
                jsonschema.Draft7Validator.check_schema(activity_data.activity_schema)
            except ValidationError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid JSON Schema in activity_schema: {str(e)}"
                )

        # Update only provided fields
        update_data = activity_data.dict(exclude_unset=True)
        activity = self.activity_repository.update(activity_id, **update_data)

        return ActivityType.from_db(activity) if activity else None

    def delete_activity(self, activity_id: int) -> bool:
        """Delete an activity and all its moments"""
        # Check if activity exists and has moments
        activity = self.activity_repository.validate_existence(activity_id)
        moment_count = self.moment_repository.get_activity_moments_count(activity_id)

        if moment_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete activity with {moment_count} moments. Delete moments first."
            )

        return self.activity_repository.delete(activity_id)

    def validate_moment_data(self, activity_id: int, data: Dict) -> None:
        """Validate moment data against activity schema"""
        activity = self.activity_repository.validate_existence(activity_id)
        
        try:
            jsonschema.validate(instance=data, schema=activity.activity_schema)
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid moment data: {str(e)}"
            )
