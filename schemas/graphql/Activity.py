import strawberry
from typing import List, Optional, Dict, Any
from schemas.base.activity_schema import ActivityData
from utils.json_utils import ensure_dict
from .types.Moment import (
    Moment,
)  # Import at the top instead of bottom


@strawberry.type
class Activity:
    """Activity type for GraphQL queries"""

    @strawberry.field(
        description="Unique identifier for the activity"
    )
    def id(self) -> int:
        return self._id

    @strawberry.field(description="Name of the activity")
    def name(self) -> str:
        return self._name

    @strawberry.field(
        description="Detailed description of the activity"
    )
    def description(self) -> str:
        return self._description

    @strawberry.field(
        description="JSON Schema defining the structure of moment data"
    )
    def activitySchema(self) -> str:
        return self._activity_schema

    @strawberry.field(
        description="Icon identifier for the activity"
    )
    def icon(self) -> str:
        return self._icon

    @strawberry.field(
        description="Color code for the activity (hex format)"
    )
    def color(self) -> str:
        return self._color

    @strawberry.field(
        description="Number of moments using this activity",
    )
    def momentCount(self) -> int:
        return self._moment_count

    @strawberry.field(
        description="Moments using this activity",
    )
    def moments(self) -> List[Moment]:
        return self._moments

    def __init__(
        self,
        id: int,
        name: str,
        description: str,
        activitySchema: str,
        icon: str,
        color: str,
        momentCount: int = 0,
        moments: Optional[List[Moment]] = None,
    ):
        self._id = id
        self._name = name
        self._description = description
        self._activity_schema = activitySchema
        self._icon = icon
        self._color = color
        self._moment_count = momentCount
        self._moments = moments or []

    @classmethod
    def from_domain(
        cls, activity: ActivityData
    ) -> "Activity":
        """Create from domain model"""
        activity_dict = activity.to_json_dict(graphql=True)
        return cls(
            id=activity_dict["id"],
            name=activity_dict["name"],
            description=activity_dict["description"],
            activitySchema=activity_dict["activitySchema"],
            icon=activity_dict["icon"],
            color=activity_dict["color"],
            momentCount=activity_dict["momentCount"],
            moments=[],  # Lazy load moments
        )

    @classmethod
    def from_db(cls, db_activity: Any) -> "Activity":
        """Create from database model"""
        return cls.from_domain(
            ActivityData.from_dict(
                {
                    "id": db_activity.id,
                    "name": db_activity.name,
                    "description": db_activity.description,
                    "activity_schema": db_activity.activity_schema,
                    "icon": db_activity.icon,
                    "color": db_activity.color,
                    "moment_count": getattr(
                        db_activity, "moment_count", 0
                    ),
                }
            )
        )


@strawberry.input
class ActivityInput:
    """Input type for creating a new activity"""

    name: str = strawberry.field(
        description="Name of the activity (1-255 characters)"
    )
    description: str = strawberry.field(
        description="Detailed description (1-1000 characters)"
    )
    activitySchema: str = strawberry.field(
        description="JSON Schema defining the structure of moment data"
    )
    icon: str = strawberry.field(
        description="Icon identifier (1-255 characters)"
    )
    color: str = strawberry.field(
        description="Color code in hex format (e.g., #4A90E2)"
    )

    def to_domain(self) -> ActivityData:
        """Convert to domain model"""
        return ActivityData.from_dict(
            {
                "name": self.name,
                "description": self.description,
                "activity_schema": ensure_dict(
                    self.activitySchema
                ),
                "icon": self.icon,
                "color": self.color,
            }
        )


@strawberry.input
class ActivityUpdateInput:
    """Input type for updating an activity"""

    name: Optional[str] = strawberry.field(
        default=None,
        description="Name of the activity (1-255 characters)",
    )
    description: Optional[str] = strawberry.field(
        default=None,
        description="Detailed description (1-1000 characters)",
    )
    activitySchema: Optional[str] = strawberry.field(
        default=None,
        description="JSON Schema defining the structure of moment data",
    )
    icon: Optional[str] = strawberry.field(
        default=None,
        description="Icon identifier (1-255 characters)",
    )
    color: Optional[str] = strawberry.field(
        default=None,
        description="Color code in hex format (e.g., #4A90E2)",
    )

    def to_domain(
        self, existing: ActivityData
    ) -> ActivityData:
        """Convert to domain model, preserving existing data"""
        update_dict: Dict[str, Any] = {}
        if self.name is not None:
            update_dict["name"] = self.name
        if self.description is not None:
            update_dict["description"] = self.description
        if self.activitySchema is not None:
            update_dict["activity_schema"] = ensure_dict(
                self.activitySchema
            )
        if self.icon is not None:
            update_dict["icon"] = self.icon
        if self.color is not None:
            update_dict["color"] = self.color

        existing_dict = existing.to_dict()
        existing_dict.update(update_dict)
        return ActivityData.from_dict(existing_dict)


@strawberry.type
class ActivityConnection:
    """Type for paginated activity lists"""

    @strawberry.field(description="List of activities")
    def items(self) -> List[Activity]:
        return self._items

    @strawberry.field(description="Total number of items")
    def total(self) -> int:
        return self._total

    @strawberry.field(description="Number of items skipped")
    def skip(self) -> int:
        return self._skip

    @strawberry.field(
        description="Maximum number of items returned (max 100)"
    )
    def limit(self) -> int:
        return self._limit

    def __init__(
        self,
        items: List[Activity],
        total: int,
        skip: int = 0,
        limit: int = 50,
    ):
        self._items = items
        self._total = total
        self._skip = skip
        self._limit = limit

    @classmethod
    def from_pydantic(
        cls, activity_list: Any
    ) -> "ActivityConnection":
        """Convert pydantic ActivityList to GraphQL ActivityConnection"""
        return cls(
            items=[
                Activity.from_db(item)
                for item in activity_list.items
            ],
            total=activity_list.total,
            skip=activity_list.skip,
            limit=activity_list.limit,
        )
