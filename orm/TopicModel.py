"""ORM model for Topic."""

from datetime import datetime, UTC
from typing import Dict, Any, ClassVar, List, TYPE_CHECKING
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, relationship

from orm.BaseModel import EntityMeta

if TYPE_CHECKING:
    from .UserModel import User
    from .TaskModel import Task


class Topic(EntityMeta):
    """Topic model represents a user-specific tag or classification object.

    Each topic has a unique name per user and an associated icon.
    Topics can be used to categorize various entities in the system.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        name: Unique name for the topic (per user)
        icon: Emoji character or URI for the icon
        created_at: Creation timestamp
        updated_at: Last update timestamp
        user: Relationship to User model
        tasks: Relationship to Task model
    """

    __tablename__ = "topics"

    # Field length constraints
    NAME_MAX_LENGTH: ClassVar[int] = 255
    ICON_MAX_LENGTH: ClassVar[int] = 255

    # Primary key
    id: Mapped[int] = Column(
        Integer, primary_key=True, index=True
    )

    # Required fields
    user_id: Mapped[str] = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = Column(
        String(NAME_MAX_LENGTH), nullable=False
    )
    icon: Mapped[str] = Column(
        String(ICON_MAX_LENGTH), nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="topics"
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="topic",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "name != ''", name="check_topic_name_not_empty"
        ),
        CheckConstraint(
            "icon != ''", name="check_topic_icon_not_empty"
        ),
        UniqueConstraint(
            "user_id",
            "name",
            name="uq_topic_name_per_user",
        ),
    )

    def __init__(self, **kwargs):
        """Initialize topic with defaults if not provided.

        Args:
            **kwargs: Topic attributes
        """
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.now(UTC)
        super().__init__(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert topic to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of topic
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "icon": self.icon,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Topic":
        """Create Topic from dictionary data.

        Args:
            data: Dictionary containing topic data

        Returns:
            Topic: New Topic instance
        """
        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            name=data["name"],
            icon=data["icon"],
            created_at=data.get(
                "created_at", datetime.now(UTC)
            ),
            updated_at=data.get("updated_at"),
        )

    def update(self, data: Dict[str, Any]) -> None:
        """Update topic with dictionary data.

        Args:
            data: Dictionary of fields to update
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
