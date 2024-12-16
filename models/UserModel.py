from sqlalchemy import (
    Column,
    String,
    DateTime,
    text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped
from uuid import uuid4
from typing import List, TYPE_CHECKING, Optional
from sqlalchemy.engine.default import DefaultDialect
from sqlalchemy.dialects.postgresql.base import PGDialect
import re

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

    # Validation patterns
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    MIN_USERNAME_LENGTH = 3

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

    # Remove database-specific constraints
    __table_args__ = ()

    def __init__(self, **kwargs):
        self.validate_username(kwargs.get('username'))
        super().__init__(**kwargs)

    @classmethod
    def validate_username(cls, username: Optional[str]) -> None:
        """Validate the username format.

        Args:
            username: The username to validate

        Raises:
            ValueError: If username is invalid
        """
        if username is None:
            raise ValueError("Username cannot be None")
            
        if len(username) < cls.MIN_USERNAME_LENGTH:
            raise ValueError(
                f"Username must be at least {cls.MIN_USERNAME_LENGTH} characters long"
            )
            
        if not cls.USERNAME_PATTERN.match(username):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )

    def __repr__(self) -> str:
        """String representation of the user.

        Returns:
            String representation including id and username
        """
        return f"<User {self.id} ({self.username})>"

    def activity_count(self) -> int:
        """Get the number of activities owned by the user.

        Returns:
            Number of activities
        """
        return len(self.activities)

    def moment_count(self) -> int:
        """Get the number of moments created by the user.

        Returns:
            Number of moments
        """
        return len(self.moments)
