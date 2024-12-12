from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from models.BaseModel import EntityMeta


class User(EntityMeta):
    """User Model represents a registered user in the system"""

    __tablename__ = "users"

    id = Column(
        String(36),  # UUID length is 36 characters
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    username = Column(
        String(50),  # Max length of 50 characters
        unique=True,
        index=True,
        nullable=False,
    )
    user_secret = Column(
        String(64),  # Length for secure secret
        unique=True,
        index=True,
        nullable=False,
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    activities = relationship(
        "Activity",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    moments = relationship(
        "Moment",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
