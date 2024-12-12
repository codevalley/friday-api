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


class MomentService:
    def __init__(
        self, db: Session = Depends(get_db_connection)
    ):
        self.db = db
        self.moment_repository = MomentRepository(db)
        self.activity_repository = ActivityRepository(db)

    def create_moment(
        self, moment_data: MomentCreate
    ) -> MomentType:
        """Create a new moment with data validation"""
        # Get activity to validate data against schema
        activity = (
            self.activity_repository.validate_existence(
                moment_data.activity_id
            )
        )

        try:
            # Validate moment data against activity schema
            jsonschema.validate(
                instance=moment_data.data,
                schema=activity.activity_schema,
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid moment data: {str(e)}",
            )

        moment = self.moment_repository.create(
            activity_id=moment_data.activity_id,
            data=moment_data.data,
            timestamp=moment_data.timestamp,
        )

        return MomentType.from_db(moment)

    def get_moment(
        self, moment_id: int
    ) -> Optional[MomentType]:
        """Get a moment by ID"""
        moment = self.moment_repository.validate_existence(
            moment_id
        )
        return (
            MomentType.from_db(moment) if moment else None
        )

    def list_moments(
        self,
        page: int = 1,
        size: int = 50,
        activity_id: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> MomentConnection:
        """List moments with filtering and pagination"""
        moments_list = self.moment_repository.list_moments(
            page=page,
            size=size,
            activity_id=activity_id,
            start_time=start_time,
            end_time=end_time,
        )

        return MomentConnection(
            items=[
                MomentType.from_db(moment)
                for moment in moments_list.items
            ],
            total=moments_list.total,
            page=moments_list.page,
            size=moments_list.size,
            pages=moments_list.pages,
        )

    def update_moment(
        self, moment_id: int, moment_data: MomentUpdate
    ) -> Optional[MomentType]:
        """Update a moment"""
        moment = self.moment_repository.validate_existence(
            moment_id
        )
        activity = (
            self.activity_repository.validate_existence(
                moment.activity_id
            )
        )

        if moment_data.data is not None:
            try:
                # Validate moment data against activity schema
                jsonschema.validate(
                    instance=moment_data.data,
                    schema=activity.activity_schema,
                )
            except ValidationError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid moment data: {str(e)}",
                )

        moment = self.moment_repository.update(
            moment_id,
            data=moment_data.data,
            timestamp=moment_data.timestamp,
        )

        return (
            MomentType.from_db(moment) if moment else None
        )

    def delete_moment(self, moment_id: int) -> bool:
        """Delete a moment"""
        return self.moment_repository.delete(moment_id)
