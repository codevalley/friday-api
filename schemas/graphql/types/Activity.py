"""Activity GraphQL types."""

from datetime import datetime
from typing import List, Optional, Any
import json
import strawberry

from domain.models.activity import ActivityData
from schemas.graphql.types.Moment import Moment


@strawberry.type
class Activity:
    """GraphQL type for Activity."""

    @strawberry.field
    def id(self) -> int:
        """Activity ID."""
        return self._domain.id

    @strawberry.field
    def name(self) -> str:
        """Activity name."""
        return self._domain.name

    @strawberry.field
    def description(self) -> str:
        """Activity description."""
        return self._domain.description

    @strawberry.field
    def activity_schema(self) -> str:
        """Activity schema as JSON string."""
        return json.dumps(self._domain.activity_schema)

    @strawberry.field
    def icon(self) -> str:
        """Activity icon."""
        return self._domain.icon

    @strawberry.field
    def color(self) -> str:
        """Activity color."""
        return self._domain.color

    @strawberry.field
    def user_id(self) -> str:
        """ID of the user who created the activity."""
        return self._domain.user_id

    @strawberry.field
    def moment_count(self) -> int:
        """Number of moments using this activity."""
        return self._domain.moment_count

    @strawberry.field
    def moments(self) -> Optional[List[Moment]]:
        """List of moments using this activity."""
        if not self._domain.moments:
            return None
        return [
            Moment.from_domain(m)
            for m in self._domain.moments
        ]

    @strawberry.field
    def created_at(self) -> datetime:
        """When the activity was created."""
        return self._domain.created_at

    @strawberry.field
    def updated_at(self) -> Optional[datetime]:
        """When the activity was last updated."""
        return self._domain.updated_at

    def __init__(self, domain: ActivityData):
        """Initialize with domain model."""
        self._domain = domain

    @classmethod
    def from_domain(
        cls, domain: ActivityData
    ) -> "Activity":
        """Create from domain model."""
        return cls(domain)

    @classmethod
    def from_db(cls, db_model: Any) -> "Activity":
        """Create from database model."""
        return cls(ActivityData.from_orm(db_model))


@strawberry.type
class ActivityConnection:
    """Type for paginated activity lists."""

    @strawberry.field(description="List of activities")
    def items(self) -> List[Activity]:
        """Get list of activities."""
        return self._items

    @strawberry.field(description="Total number of items")
    def total(self) -> int:
        """Get total number of items."""
        return self._total

    @strawberry.field(description="Current page number")
    def page(self) -> int:
        """Get current page number."""
        return self._page

    @strawberry.field(
        description="Number of items per page"
    )
    def size(self) -> int:
        """Get number of items per page."""
        return self._size

    @strawberry.field(description="Total number of pages")
    def pages(self) -> int:
        """Get total number of pages."""
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
    def from_domain(
        cls, items: List[ActivityData], page: int, size: int
    ) -> "ActivityConnection":
        """Create from domain models."""
        return cls(
            items=[
                Activity.from_domain(item) for item in items
            ],
            total=len(items),
            page=page,
            size=size,
        )


@strawberry.input
class ActivityInput:
    """GraphQL input type for creating an Activity."""

    name: str
    description: str
    activitySchema: str
    icon: str
    color: str

    def to_domain(self) -> ActivityData:
        """Convert to domain model."""
        return ActivityData(
            name=self.name,
            description=self.description,
            activity_schema=json.loads(self.activitySchema),
            icon=self.icon,
            color=self.color,
            user_id="",  # Will be set by the service
        )


@strawberry.input
class ActivityUpdateInput:
    """GraphQL input type for updating an Activity."""

    name: Optional[str] = None
    description: Optional[str] = None
    activitySchema: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None

    def to_domain(
        self, existing: ActivityData
    ) -> ActivityData:
        """Convert to domain model, using existing data for missing fields."""
        activity_schema = (
            json.loads(self.activitySchema)
            if self.activitySchema is not None
            else existing.activity_schema
        )

        return ActivityData(
            id=existing.id,
            name=self.name or existing.name,
            description=self.description
            or existing.description,
            activity_schema=activity_schema,
            icon=self.icon or existing.icon,
            color=self.color or existing.color,
            user_id=existing.user_id,
            moment_count=existing.moment_count,
            moments=existing.moments,
            created_at=existing.created_at,
            updated_at=datetime.now(),
        )
