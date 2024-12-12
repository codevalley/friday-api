import strawberry
from typing import Optional
from datetime import datetime
from utils.json_utils import ensure_string, ensure_dict


@strawberry.type
class Moment:
    @classmethod
    def from_db(cls, db_moment):
        """Convert SQLAlchemy model to GraphQL type"""
        return cls(
            id=db_moment.id,
            timestamp=db_moment.timestamp,
            activity_id=db_moment.activity_id,
            data=ensure_string(db_moment.data),
            activity=(
                Activity.from_db(db_moment.activity)
                if db_moment.activity
                else None
            ),
        )

    id: int
    timestamp: datetime
    activity_id: int
    data: str  # JSON string
    # Note: activity will be added after Activity type is defined
    activity: "Activity" = strawberry.field(default=None)

    @strawberry.field
    def activityId(self) -> int:
        """Alias for activity_id in GraphQL"""
        return self.activity_id


@strawberry.input
class MomentInput:
    activityId: int
    data: str  # JSON string
    timestamp: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert input to dictionary with proper types"""
        return {
            "activity_id": self.activityId,
            "data": ensure_dict(self.data),
            "timestamp": self.timestamp,
        }


@strawberry.input
class MomentUpdateInput:
    data: Optional[str] = None  # JSON string
    timestamp: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert input to dictionary with proper types"""
        update_dict = {}
        if self.data is not None:
            update_dict["data"] = ensure_dict(self.data)
        if self.timestamp is not None:
            update_dict["timestamp"] = self.timestamp
        return update_dict


@strawberry.type
class MomentConnection:
    """Type for paginated moment lists"""

    items: list[Moment]
    total: int
    page: int
    size: int
    pages: int


# Import at the bottom to avoid circular imports
from .Activity import Activity  # noqa
