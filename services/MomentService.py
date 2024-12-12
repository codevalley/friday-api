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
    MomentResponse,
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
    ) -> MomentResponse:
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

        return MomentResponse.from_orm(moment)

    def create_moment_graphql(
        self, moment_data: MomentCreate, user_id: str
    ) -> MomentType:
        """Create a moment for GraphQL"""
        moment = self.create_moment(moment_data, user_id)
        return MomentType.from_db(moment)

    def list_moments(
        self,
        page: int,
        size: int,
        activity_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> MomentList:
        """List moments with filtering and pagination for REST"""
        moments = self.moment_repository.list_moments(
            page=page,
            size=size,
            activity_id=activity_id,
            start_time=start_date,
            end_time=end_date,
            user_id=user_id,
        )
        return moments

    def list_moments_graphql(
        self,
        page: int = 1,
        size: int = 50,
        activity_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> MomentConnection:
        """List moments with filtering and pagination for GraphQL"""
        moments = self.moment_repository.list_moments(
            page=page,
            size=size,
            activity_id=activity_id,
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
        )
        return MomentConnection.from_pydantic(moments)

    def get_moment(
        self, moment_id: int, user_id: str
    ) -> MomentResponse:
        """Get a moment by ID for REST"""
        moment = self.moment_repository.get_by_id(moment_id)
        if not moment or moment.activity.user_id != user_id:
            raise HTTPException(
                status_code=404, detail="Moment not found"
            )
        return MomentResponse.from_orm(moment)

    def get_moment_graphql(
        self, moment_id: int, user_id: str
    ) -> MomentType:
        """Get a moment by ID for GraphQL"""
        moment = self.get_moment(moment_id, user_id)
        return MomentType.from_db(moment)

    def update_moment(
        self,
        moment_id: int,
        moment_data: MomentUpdate,
        user_id: str,
    ) -> MomentResponse:
        """Update a moment for REST"""
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

        updated = self.moment_repository.update(
            moment_id=moment_id,
            **moment_data.dict(exclude_unset=True)
        )
        return MomentResponse.from_orm(updated)

    def update_moment_graphql(
        self,
        moment_id: int,
        moment_data: MomentUpdate,
        user_id: str,
    ) -> MomentType:
        """Update a moment for GraphQL"""
        moment = self.update_moment(
            moment_id, moment_data, user_id
        )
        return MomentType.from_db(moment)

    def delete_moment(self, moment_id: int, user_id: str):
        """Delete a moment"""
        moment = self.moment_repository.get_by_id(moment_id)
        if not moment or moment.activity.user_id != user_id:
            raise HTTPException(
                status_code=404, detail="Moment not found"
            )
        self.moment_repository.delete(moment_id)
