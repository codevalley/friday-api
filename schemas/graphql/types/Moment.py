import strawberry
from typing import Optional
from datetime import datetime
from schemas.base.moment_schema import MomentData


@strawberry.input
class MomentInput:
    activityId: int
    data: str  # JSON string for the data
    timestamp: Optional[datetime] = None

    def to_domain(self) -> MomentData:
        """Convert to domain model"""
        return MomentData.from_dict(
            {
                "activity_id": self.activityId,
                "data": self.data,  # Will be converted to dict by MomentData
                "timestamp": self.timestamp,
            }
        )


@strawberry.type
class Moment:
    id: int
    activityId: int
    data: str  # JSON string for the data
    timestamp: datetime
    userId: Optional[str] = None

    @classmethod
    def from_domain(cls, moment: MomentData) -> "Moment":
        """Create from domain model"""
        moment_dict = moment.to_json_dict(graphql=True)
        return cls(
            id=moment_dict["id"],
            activityId=moment_dict["activityId"],
            data=moment_dict["data"],
            timestamp=moment_dict["timestamp"],
            userId=moment_dict.get("userId"),
        )

    @classmethod
    def from_db(cls, db_moment) -> "Moment":
        """Create from database model"""
        return cls.from_domain(
            MomentData.from_dict(
                {
                    "id": db_moment.id,
                    "activity_id": db_moment.activity_id,
                    "data": db_moment.data,
                    "timestamp": db_moment.timestamp,
                    "user_id": db_moment.user_id,
                }
            )
        )
