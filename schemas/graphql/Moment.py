import strawberry
from typing import Optional
from datetime import datetime


@strawberry.type
class Moment:
    id: int
    timestamp: datetime
    activity_id: int
    data: str  # JSON string
    # Note: activity will be added after Activity type is defined
    activity: "Activity" = strawberry.field(default=None)


@strawberry.input
class MomentInput:
    activity_id: int
    data: str  # JSON string
    timestamp: Optional[datetime] = None


@strawberry.input
class MomentUpdateInput:
    data: Optional[str] = None  # JSON string
    timestamp: Optional[datetime] = None


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
