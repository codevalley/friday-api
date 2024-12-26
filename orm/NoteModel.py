from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship, Mapped
from datetime import datetime
from typing import Optional, List, Dict, Any
from orm.BaseModel import EntityMeta
from orm.UserModel import User
from domain.note import NoteData
from domain.values import AttachmentType
from orm.types import JSONType


class Note(EntityMeta):
    """Note Model represents a user's note in the system.

    This model stores note content and optional attachments.
    Each note is associated with a user and can have various types of
    attachments (voice, photo, file).

    Attributes:
        id: Unique identifier for the note
        content: The text content of the note
        user_id: ID of the user who owns this note
        activity_id: ID of the activity associated with this note
        moment_id: ID of the moment associated with this note
        attachment_url: Optional URL to an attachment
        attachment_type: Type of the attachment (if any)
        created_at: Timestamp when the note was created
        updated_at: Timestamp when the note was last updated
        owner: Relationship to the User model
    """

    __tablename__ = "notes"

    # Primary key
    id: Mapped[int] = Column(
        Integer, primary_key=True, index=True
    )

    # Content fields
    content: Mapped[str] = Column(
        String(2000), nullable=False
    )
    user_id: Mapped[str] = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("activities.id"), nullable=True
    )
    moment_id: Mapped[Optional[int]] = Column(
        Integer, ForeignKey("moments.id"), nullable=True
    )
    attachment_url: Mapped[Optional[str]] = Column(
        String(500), nullable=True
    )
    attachment_type: Mapped[
        Optional[AttachmentType]
    ] = Column(SQLEnum(AttachmentType), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = Column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime, nullable=True, onupdate=datetime.utcnow
    )

    # Relationships
    owner: Mapped[User] = relationship(
        "User", back_populates="notes"
    )

    # Add attachments column
    attachments: Mapped[
        Optional[List[Dict[str, Any]]]
    ] = Column(JSONType, nullable=True)

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "content IS NOT NULL AND content != ''",
            name="check_content_not_empty",
        ),
        CheckConstraint(
            "(attachment_url IS NULL AND attachment_type IS NULL) OR "
            "(attachment_url IS NOT NULL AND attachment_type IS NOT NULL)",
            name="check_attachment_consistency",
        ),
    )

    def to_domain(self) -> NoteData:
        """Convert ORM model to domain model.

        Returns:
            NoteData instance with this note's data
        """
        return NoteData(
            id=self.id,
            content=self.content,
            user_id=self.user_id,
            activity_id=self.activity_id,
            moment_id=self.moment_id,
            attachments=self.attachments,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, domain: NoteData) -> "Note":
        """Create Note model from domain data.

        Args:
            domain: NoteData instance with the note data

        Returns:
            Note ORM model instance
        """
        return cls(
            id=domain.id,
            content=domain.content,
            user_id=domain.user_id,
            activity_id=domain.activity_id,
            moment_id=domain.moment_id,
            attachments=domain.attachments,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    def __repr__(self) -> str:
        """String representation of the note.

        Returns:
            String representation including id and user_id
        """
        return f"<Note(id={self.id}, user_id='{self.user_id}')>"
