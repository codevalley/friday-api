import strawberry
from typing import List, Optional, Dict, Any

from models.ActivityModel import Activity as ActivityModel
from schemas.base.activity_schema import ActivityData
from utils.json_utils import ensure_dict
from .Moment import Moment


@strawberry.type
class Activity:
    """Activity type for GraphQL queries.

    Represents an activity that can be logged with moments.
    Each activity has its own schema for validating moment data.
    """

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
        """Initialize Activity type.

        Args:
            id: Unique identifier
            name: Display name
            description: Detailed description
            activitySchema: JSON Schema for moment data
            icon: Display icon (emoji)
            color: Display color (hex code)
            momentCount: Number of moments using this activity
            moments: List of moments using this activity
        """
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
        """Create from domain model.

        Args:
            activity: Domain model instance to convert

        Returns:
            Activity: GraphQL type instance
        """
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
    def from_db(
        cls, db_activity: ActivityModel
    ) -> "Activity":
        """Create from database model.

        Args:
            db_activity: SQLAlchemy model instance

        Returns:
            Activity: GraphQL type instance
        """
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
    """Input type for creating a new activity.

    Defines the structure for activity creation mutations.
    """

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Pydantic model creation.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "name": self.name,
            "description": self.description,
            "activity_schema": ensure_dict(
                self.activitySchema
            ),
            "icon": self.icon,
            "color": self.color,
        }

    def to_domain(self) -> ActivityData:
        """Convert to domain model.

        Returns:
            ActivityData: Domain model instance
        """
        return ActivityData.from_dict(self.to_dict())


@strawberry.input
class ActivityUpdateInput:
    """Input type for updating an activity.

    All fields are optional since this is used for partial updates.
    """

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Pydantic model creation.

        Returns:
            Dict[str, Any]: Dictionary with only set fields
        """
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
        return update_dict

    def to_domain(
        self, existing: ActivityData
    ) -> ActivityData:
        """Convert to domain model, preserving existing data.

        Args:
            existing: Existing activity data to update

        Returns:
            ActivityData: Updated domain model instance
        """
        existing_dict = existing.to_dict()
        existing_dict.update(self.to_dict())
        return ActivityData.from_dict(existing_dict)


@strawberry.type
class ActivityConnection:
    """Type for paginated activity lists.

    Implements cursor-based pagination for activities.
    """

    @strawberry.field(description="List of activities")
    def items(self) -> List[Activity]:
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
        return (self._total + self._size - 1) // self._size

    def __init__(
        self,
        items: List[Activity],
        total: int,
        page: int = 1,
        size: int = 50,
    ):
        """Initialize ActivityConnection.

        Args:
            items: List of activities for current page
            total: Total number of activities
            page: Current page number (1-based)
            size: Number of items per page
        """
        self._items = items
        self._total = total
        self._page = page
        self._size = size

    @classmethod
    def from_pydantic(
        cls, activity_list: ActivityData
    ) -> "ActivityConnection":
        """Convert pydantic ActivityList to GraphQL ActivityConnection.

        Args:
            activity_list: Pydantic model instance

        Returns:
            ActivityConnection: GraphQL type instance
        """
        return cls(
            items=[
                Activity.from_db(item)
                for item in activity_list.items
            ],
            total=activity_list.total,
            page=activity_list.page,
            size=activity_list.size,
        )
