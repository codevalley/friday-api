"""Pydantic schemas for timeline responses"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict

from domain.timeline import TimelineEventType
from .PaginationSchema import PaginationResponse


class TimelineEvent(BaseModel):
    """Schema for a timeline event"""

    id: int
    event_type: TimelineEventType
    user_id: str
    event_metadata: dict
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class TimelineList(PaginationResponse[TimelineEvent]):
    """Schema for paginated timeline events"""

    items: List[TimelineEvent]
