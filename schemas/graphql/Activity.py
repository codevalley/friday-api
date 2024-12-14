import strawberry
from typing import List, Optional
from schemas.base.activity_schema import ActivityData
from utils.json_utils import ensure_dict


@strawberry.type
class Activity:
    """Activity type for GraphQL queries"""

    id: int = strawberry.field(
        description="Unique identifier for the activity"
    )
    name: str = strawberry.field(
        description="Name of the activity"
    )
    description: str = strawberry.field(
        description="Detailed description of the activity"
    )
    activitySchema: str = strawberry.field(
        description="JSON Schema defining the structure of moment data"
    )
    icon: str = strawberry.field(
        description="Icon identifier for the activity"
    )
    color: str = strawberry.field(
        description="Color code for the activity (hex format)"
    )
    momentCount: int = strawberry.field(
        default=0,
        description="Number of moments using this activity",
    )
    moments: List["Moment"] = strawberry.field(
        default_factory=list,
        description="Moments using this activity",
    )

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
    def from_db(cls, db_activity) -> "Activity":
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
        None,
        description="Name of the activity (1-255 characters)",
    )
    description: Optional[str] = strawberry.field(
        None,
        description="Detailed description (1-1000 characters)",
    )
    activitySchema: Optional[str] = strawberry.field(
        None,
        description="JSON Schema defining the structure of moment data",
    )
    icon: Optional[str] = strawberry.field(
        None,
        description="Icon identifier (1-255 characters)",
    )
    color: Optional[str] = strawberry.field(
        None,
        description="Color code in hex format (e.g., #4A90E2)",
    )

    def to_domain(
        self, existing: ActivityData
    ) -> ActivityData:
        """Convert to domain model, preserving existing data"""
        update_dict = {}
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

    items: List[Activity]
    total: int
    skip: int = strawberry.field(
        default=0, description="Number of items skipped"
    )
    limit: int = strawberry.field(
        default=50,
        description="Maximum number of items returned (max 100)",
    )

    @classmethod
    def from_pydantic(cls, activity_list):
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


# Import at the bottom to avoid circular imports
from .Moment import Moment  # noqa
