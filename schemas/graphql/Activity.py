import strawberry
from typing import List, Optional
from datetime import datetime


@strawberry.type
class Activity:
    id: int
    name: str
    description: str
    activity_schema: str  # JSON string
    icon: str
    color: str
    # Note: moments will be added after Moment type is defined
    moments: List["Moment"] = strawberry.field(default_factory=list)


@strawberry.input
class ActivityInput:
    name: str
    description: str
    activity_schema: str  # JSON string
    icon: str
    color: str


@strawberry.input
class ActivityUpdateInput:
    name: Optional[str] = None
    description: Optional[str] = None
    activity_schema: Optional[str] = None  # JSON string
    icon: Optional[str] = None
    color: Optional[str] = None


# Import at the bottom to avoid circular imports
from .Moment import Moment  # noqa
