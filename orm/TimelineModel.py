"""ORM model for timeline events"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    JSON,
    Enum,
)
from sqlalchemy.sql import func

from domain.timeline import TimelineEventType
from .BaseModel import Base


class Timeline(Base):
    """ORM model for timeline events"""

    __tablename__ = "timeline"

    id = Column(
        Integer, primary_key=True, autoincrement=True
    )
    event_type = Column(
        Enum(TimelineEventType),
        nullable=False,
        index=True,
        comment="Type of timeline event",
    )
    user_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="ID of the user who owns this event",
    )
    event_metadata = Column(
        JSON,
        nullable=False,
        comment="Event-specific metadata (e.g. task_id for task events)",
    )
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="When this event occurred",
    )

    def __repr__(self) -> str:
        """String representation of the timeline event

        Returns:
            String representation
        """
        return (
            f"Timeline(id={self.id}, "
            f"event_type={self.event_type}, "
            f"user_id={self.user_id}, "
            f"timestamp={self.timestamp})"
        )
