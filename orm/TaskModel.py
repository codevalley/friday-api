"""Task ORM model."""

from typing import Dict, Any, Optional
from datetime import datetime, UTC
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    JSON,
    Enum,
    CheckConstraint,
)
from sqlalchemy.orm import relationship, Mapped
from typing import TYPE_CHECKING

from domain.values import TaskStatus, TaskPriority
from .BaseModel import EntityMeta

if TYPE_CHECKING:
    from .UserModel import User


class Task(EntityMeta):
    """Task model for ORM."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.TODO,
    )
    priority = Column(
        Enum(TaskPriority),
        nullable=False,
        default=TaskPriority.MEDIUM,
    )
    _due_date = Column(
        "due_date",
        DateTime,
        nullable=True,
    )
    tags = Column(
        JSON,
        nullable=True,
        default=list,
    )
    parent_id = Column(
        Integer,
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="tasks",
    )
    parent = relationship(
        "Task",
        remote_side=[id],
        back_populates="subtasks",
    )
    subtasks = relationship(
        "Task",
        back_populates="parent",
        cascade="all, delete",
    )

    __table_args__ = (
        CheckConstraint(
            "title != ''",
            name="check_title_not_empty",
        ),
        CheckConstraint(
            "description != ''",
            name="check_description_not_empty",
        ),
    )

    def __init__(self, **kwargs):
        """Initialize a Task instance.

        Args:
            **kwargs: Task attributes
        """
        # Set defaults if not provided
        if "status" not in kwargs:
            kwargs["status"] = TaskStatus.TODO
        if "priority" not in kwargs:
            kwargs["priority"] = TaskPriority.MEDIUM
        if "tags" not in kwargs:
            kwargs["tags"] = []

        # Check for self-reference before initialization
        if "id" in kwargs and "parent_id" in kwargs:
            if kwargs["id"] == kwargs["parent_id"]:
                raise ValueError(
                    "Task cannot reference itself as parent"
                )

        # Ensure due_date is in UTC if provided
        if (
            "due_date" in kwargs
            and kwargs["due_date"] is not None
        ):
            # Convert to UTC and remove microseconds
            kwargs["due_date"] = (
                kwargs["due_date"]
                .astimezone(UTC)
                .replace(microsecond=0)
            )

        super().__init__(**kwargs)

    @property
    def due_date(self) -> Optional[datetime]:
        """Get the due date with UTC timezone."""
        if self._due_date is None:
            return None
        return self._due_date.replace(tzinfo=UTC)

    @due_date.setter
    def due_date(self, value: Optional[datetime]):
        """Set the due date, converting to UTC if needed."""
        if value is not None:
            value = value.astimezone(UTC).replace(
                microsecond=0
            )
        self._due_date = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary.

        Returns:
            Dict[str, Any]: Task data
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "user_id": self.user_id,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date,
            "tags": self.tags,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def update(self, data: Dict[str, Any]) -> None:
        """Update task with new data.

        Args:
            data: Dictionary of fields to update

        Raises:
            ValueError: If task tries to reference itself as parent
        """
        # Check for self-reference
        if (
            "parent_id" in data
            and data["parent_id"] == self.id
        ):
            raise ValueError(
                "Task cannot reference itself as parent"
            )

        # Update fields
        for key, value in data.items():
            setattr(self, key, value)
