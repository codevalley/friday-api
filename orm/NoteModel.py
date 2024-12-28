"""Note ORM model."""

from datetime import datetime
from typing import Dict, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    JSON,
    DateTime,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from domain.values import ProcessingStatus
from .BaseModel import Base


class Note(Base):
    """Note ORM model.

    Attributes:
        id: Primary key
        content: Note content
        user_id: ID of the user who created the note
        activity_id: Optional ID of associated activity
        moment_id: Optional ID of associated moment
        attachments: List of attachments
        processing_status: Current processing status
        enrichment_data: Data from note processing
        processed_at: When the note was processed
        created_at: When the note was created
        updated_at: When the note was last updated
    """

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    content = Column(String(4096), nullable=False)
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    activity_id = Column(
        Integer,
        ForeignKey("activities.id"),
        nullable=True,
    )
    moment_id = Column(
        Integer, ForeignKey("moments.id"), nullable=True
    )
    attachments = Column(JSON, nullable=False, default=list)
    processing_status = Column(
        SQLEnum(ProcessingStatus),
        nullable=False,
        default=ProcessingStatus.PENDING,
        server_default=ProcessingStatus.PENDING.value,
    )
    enrichment_data = Column(
        JSON, nullable=True, default=None
    )
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at = Column(
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
    )

    # Relationships
    owner = relationship("User", back_populates="notes")

    def __init__(self, **kwargs):
        """Initialize note with default processing status if not provided."""
        if "processing_status" not in kwargs:
            kwargs[
                "processing_status"
            ] = ProcessingStatus.PENDING
        super().__init__(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert note to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of note
        """
        return {
            "id": self.id,
            "content": self.content,
            "user_id": self.user_id,
            "activity_id": self.activity_id,
            "moment_id": self.moment_id,
            "attachments": self.attachments or [],
            "processing_status": self.processing_status,
            "enrichment_data": self.enrichment_data,
            "processed_at": self.processed_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Note":
        """Create note from dictionary.

        Args:
            data: Dictionary data

        Returns:
            Note: Created note instance
        """
        return cls(**data)

    def update(self, data: Dict[str, Any]) -> None:
        """Update note with dictionary data.

        Args:
            data: Dictionary of fields to update
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
