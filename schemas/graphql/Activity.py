import strawberry
from typing import List, Optional
from datetime import datetime
from utils.json_utils import ensure_string, ensure_dict


@strawberry.type
class Activity:
    @classmethod
    def from_db(cls, db_activity):
        """Convert SQLAlchemy model to GraphQL type"""
        return cls(
            id=db_activity.id,
            name=db_activity.name,
            description=db_activity.description,
            activity_schema=ensure_string(db_activity.activity_schema),
            icon=db_activity.icon,
            color=db_activity.color,
            moments=[],  # Lazy load moments
            moment_count=getattr(db_activity, 'moment_count', 0)  # Get moment_count if set
        )

    id: int
    name: str
    description: str
    activity_schema: str  # JSON string
    icon: str
    color: str
    # Note: moments will be added after Moment type is defined
    moments: List["Moment"] = strawberry.field(default_factory=list)
    moment_count: int = strawberry.field(default=0)

    @strawberry.field
    def activitySchema(self) -> str:
        """Alias for activity_schema in GraphQL"""
        return self.activity_schema

    @strawberry.field
    def momentCount(self) -> int:
        """Number of moments associated with this activity"""
        return self.moment_count


@strawberry.input
class ActivityInput:
    name: str
    description: str
    activitySchema: str  # JSON string
    icon: str
    color: str

    def to_dict(self) -> dict:
        """Convert input to dictionary with proper types"""
        return {
            "name": self.name,
            "description": self.description,
            "activity_schema": ensure_dict(self.activitySchema),
            "icon": self.icon,
            "color": self.color
        }


@strawberry.input
class ActivityUpdateInput:
    name: Optional[str] = None
    description: Optional[str] = None
    activitySchema: Optional[str] = None  # JSON string
    icon: Optional[str] = None
    color: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert input to dictionary with proper types"""
        update_dict = {}
        if self.name is not None:
            update_dict["name"] = self.name
        if self.description is not None:
            update_dict["description"] = self.description
        if self.activitySchema is not None:
            update_dict["activity_schema"] = ensure_dict(self.activitySchema)
        if self.icon is not None:
            update_dict["icon"] = self.icon
        if self.color is not None:
            update_dict["color"] = self.color
        return update_dict


# Import at the bottom to avoid circular imports
from .Moment import Moment  # noqa
