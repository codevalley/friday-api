from sqlalchemy import (
    Column,
    String,
    DateTime,
    CheckConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped
from uuid import uuid4
from typing import List, TYPE_CHECKING

from models.BaseModel import EntityMeta

if TYPE_CHECKING:
    from models.ActivityModel import Activity
    from models.MomentModel import Moment


class User(EntityMeta):
    """User Model represents a registered user in the system.

    This model stores user authentication and identification information.
    Each user can have multiple activities and moments associated with them.

    Attributes:
        id: Unique identifier (UUID)
        username: Unique username for the user
        key_id: API key identifier
        user_secret: Hashed API secret
        created_at: Timestamp of user creation
        updated_at: Timestamp of last update
        activities: List of user's activities
        moments: List of user's moments
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[str] = Column(
        String(36),  # UUID length is 36 characters
        primary_key=True,
        default=lambda: str(uuid4()),
        index=True,
    )

    # Authentication fields
    username: Mapped[str] = Column(
        String(50),  # Max length of 50 characters
        unique=True,
        index=True,
        nullable=False,
    )
    key_id: Mapped[str] = Column(
        String(36),  # UUID length is 36 characters
        unique=True,
        index=True,
        nullable=False,
    )
    user_secret: Mapped[str] = Column(
        String(64),  # Length for secure secret
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[DateTime] = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[DateTime] = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    activities: Mapped[List["Activity"]] = relationship(
        "Activity",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    moments: Mapped[List["Moment"]] = relationship(
        "Moment",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "length(username) >= 3",
            name="check_username_min_length",
        ),
        CheckConstraint(
            "username ~ '^[a-zA-Z0-9_-]+$'",
            name="check_username_format",
        ),
    )

    def __repr__(self) -> str:
        """String representation of the user.

        Returns:
            String representation including id and username
        """
        return f"<User(id={self.id}, username={self.username})>"

    @property
    def activity_count(self) -> int:
        """Get the number of activities owned by the user.

        Returns:
            Number of activities
        """
        return len(self.activities)

    @property
    def moment_count(self) -> int:
        """Get the number of moments created by the user.

        Returns:
            Number of moments
        """
        return len(self.moments)
