from typing import Optional, Dict
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
import jsonschema
from jsonschema import ValidationError

from configs.Database import get_db_connection
from repositories.MomentRepository import MomentRepository
from repositories.ActivityRepository import (
    ActivityRepository,
)
from schemas.pydantic.MomentSchema import (
    MomentCreate,
    MomentUpdate,
    MomentList,
)
from schemas.graphql.Moment import Moment as MomentType
from schemas.graphql.Moment import MomentConnection
from datetime import datetime


class MomentService:
    def __init__(
        self, db: Session = Depends(get_db_connection)
    ):
        self.db = db
        self.moment_repository = MomentRepository(db)
        self.activity_repository = ActivityRepository(db)

    def create_moment(
        self, moment_data: MomentCreate, user_id: str
    ) -> MomentType:
        """Create a new moment with data validation"""
        # Get activity to validate data against schema
        activity = (
            self.activity_repository.validate_existence(
                moment_data.activity_id
            )
        )

        # Verify activity belongs to user
        if activity.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to create moments for this activity",
            )

        try:
            # Validate moment data against activity schema
            jsonschema.validate(
                instance=moment_data.data,
                schema=activity.activity_schema_dict,
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid moment data: {str(e)}",
            )

        # Create the moment
        moment = self.moment_repository.create(
            activity_id=moment_data.activity_id,
            data=moment_data.data,
            user_id=user_id,
            timestamp=moment_data.timestamp,
        )

        return moment

    def get_moment(
        self, moment_id: int, user_id: str
    ) -> Optional[MomentType]:
        """Get a moment by ID"""
        moment = self.moment_repository.get_by_id(moment_id)
        if not moment or moment.activity.user_id != user_id:
            raise HTTPException(
                status_code=404, detail="Moment not found"
            )
        return moment

    def list_moments(
        self,
        page: int,
        size: int,
        activity_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> MomentList:
        """List moments with filtering and pagination"""
        moments = self.moment_repository.list_moments(
            page=page,
            size=size,
            activity_id=activity_id,
            start_time=start_date,
            end_time=end_date,
        )

        # Filter by user_id if provided
        if user_id:
            moments.items = [
                m
                for m in moments.items
                if m.activity.user_id == user_id
            ]
            moments.total = len(moments.items)

        return moments

    def update_moment(
        self,
        moment_id: int,
        moment_data: MomentUpdate,
        user_id: str,
    ) -> MomentType:
        """Update a moment"""
        moment = self.moment_repository.get_by_id(moment_id)
        if not moment or moment.activity.user_id != user_id:
            raise HTTPException(
                status_code=404, detail="Moment not found"
            )

        # If updating data, validate against activity schema
        if moment_data.data is not None:
            try:
                jsonschema.validate(
                    instance=moment_data.data,
                    schema=moment.activity.activity_schema_dict,
                )
            except ValidationError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid moment data: {str(e)}",
                )

        return self.moment_repository.update(
            moment_id, moment_data
        )

    def delete_moment(self, moment_id: int, user_id: str):
        """Delete a moment"""
        moment = self.moment_repository.get_by_id(moment_id)
        if not moment or moment.activity.user_id != user_id:
            raise HTTPException(
                status_code=404, detail="Moment not found"
            )
        self.moment_repository.delete(moment_id)
