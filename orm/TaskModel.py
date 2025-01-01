"""Task ORM model."""

from datetime import datetime
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Enum as SQLEnum,
    Text,
    ARRAY,
    CheckConstraint,
)
from sqlalchemy.orm import relationship, Mapped

from domain.values import TaskStatus, TaskPriority
from .BaseModel import EntityMeta

if TYPE_CHECKING:
    from orm.UserModel import User


class Task(EntityMeta):
    """Task ORM model.

    This model represents a user task in the database with all its properties
    and relationships.

    Attributes:
        id: Primary key
        title: Task title (required)
        description: Detailed task description
        user_id: ID of the user who owns this task
        status: Current status (todo/in_progress/done)
        priority: Priority level (low/medium/high/urgent)
        due_date: When the task is due
        tags: List of tags/topics
        parent_id: ID of parent task (for subtasks)
        created_at: When the task was created
        updated_at: When the task was last updated
        owner: Relationship to the user
        subtasks: Relationship to child tasks
        parent: Relationship to parent task
    """

    __tablename__ = "tasks"

    # Primary key
    id: Mapped[int] = Column(
        Integer, primary_key=True, index=True
    )

    # Required fields
    title: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[str] = Column(Text, nullable=False)
    user_id: Mapped[str] = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Status and priority
    status: Mapped[TaskStatus] = Column(
        SQLEnum(TaskStatus),
        nullable=False,
        default=TaskStatus.TODO,
        server_default=TaskStatus.TODO.value,
    )
    priority: Mapped[TaskPriority] = Column(
        SQLEnum(TaskPriority),
        nullable=False,
        default=TaskPriority.MEDIUM,
        server_default=TaskPriority.MEDIUM.value,
    )

    # Optional fields
    due_date: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    tags: Mapped[Optional[List[str]]] = Column(
        ARRAY(String), nullable=True
    )
    parent_id: Mapped[Optional[int]] = Column(
        Integer,
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=datetime.utcnow,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User", back_populates="tasks"
    )
    subtasks: Mapped[List["Task"]] = relationship(
        "Task",
        backref="parent_task",
        remote_side=[id],
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "title != ''",
            name="check_title_not_empty",
        ),
        CheckConstraint(
            "description != ''",
            name="check_description_not_empty",
        ),
        CheckConstraint(
            "parent_id != id",
            name="check_no_self_reference",
        ),
    )

    def __init__(self, **kwargs):
        """Initialize task with default status and priority if not provided."""
        if "status" not in kwargs:
            kwargs["status"] = TaskStatus.TODO
        if "priority" not in kwargs:
            kwargs["priority"] = TaskPriority.MEDIUM
        super().__init__(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of task
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "user_id": self.user_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "due_date": self.due_date,
            "tags": self.tags,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary.

        Args:
            data: Dictionary data

        Returns:
            Task: Created task instance
        """
        return cls(**data)

    def update(self, data: Dict[str, Any]) -> None:
        """Update task with dictionary data.

        Args:
            data: Dictionary of fields to update
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
