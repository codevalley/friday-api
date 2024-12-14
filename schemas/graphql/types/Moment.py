import strawberry
from typing import Optional, Any, List
from datetime import datetime
from schemas.base.moment_schema import MomentData


@strawberry.type
class Moment:
    """Type for moment data in GraphQL"""

    @strawberry.field(
        description="Unique identifier for the moment"
    )
    def id(self) -> int:
        return self._id

    @strawberry.field(
        description="ID of the activity this moment belongs to"
    )
    def activityId(self) -> int:
        return self._activity_id

    @strawberry.field(
        description="JSON string for the moment data"
    )
    def data(self) -> str:
        return self._data

    @strawberry.field(
        description="UTC timestamp for the moment"
    )
    def timestamp(self) -> datetime:
        return self._timestamp

    @strawberry.field(
        description="ID of the user who created this moment"
    )
    def userId(self) -> Optional[str]:
        return self._user_id

    def __init__(
        self,
        id: int,
        activityId: int,
        data: str,
        timestamp: datetime,
        userId: Optional[str] = None,
    ):
        self._id = id
        self._activity_id = activityId
        self._data = data
        self._timestamp = timestamp
        self._user_id = userId

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
    def from_db(cls, db_moment: Any) -> "Moment":
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


@strawberry.type
class MomentConnection:
    """Type for paginated moment lists"""

    @strawberry.field(description="List of moments")
    def items(self) -> List[Moment]:
        return self._items

    @strawberry.field(description="Total number of items")
    def total(self) -> int:
        return self._total

    @strawberry.field(description="Current page number")
    def page(self) -> int:
        return self._page

    @strawberry.field(
        description="Number of items per page"
    )
    def size(self) -> int:
        return self._size

    @strawberry.field(description="Total number of pages")
    def pages(self) -> int:
        return self._pages

    def __init__(
        self,
        items: List[Moment],
        total: int,
        page: int = 1,
        size: int = 50,
    ):
        self._items = items
        self._total = total
        self._page = page
        self._size = size
        self._pages = (total + size - 1) // size

    @classmethod
    def from_pydantic(
        cls, moment_list: Any
    ) -> "MomentConnection":
        """Create from pydantic MomentList"""
        return cls(
            items=[
                Moment.from_db(moment)
                for moment in moment_list.items
            ],
            total=moment_list.total,
            page=moment_list.page,
            size=moment_list.size,
        )


@strawberry.input
class MomentInput:
    """Input type for creating a new moment"""

    activityId: int = strawberry.field(
        description="ID of the activity this moment belongs to"
    )
    data: str = strawberry.field(
        description="JSON string for the moment data"
    )
    timestamp: Optional[datetime] = strawberry.field(
        default=None,
        description="UTC timestamp for the moment",
    )

    def to_domain(self) -> MomentData:
        """Convert to domain model"""
        return MomentData.from_dict(
            {
                "activity_id": self.activityId,
                "data": self.data,  # Will be converted to dict by MomentData
                "timestamp": self.timestamp,
            }
        )
