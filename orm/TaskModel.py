"""Task ORM model."""

from typing import Dict, Any, Optional, List
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
    from .NoteModel import Note


class Task(EntityMeta):
    """Task Model represents a single task or todo item.

    Each task belongs to a user and can optionally be part of a hierarchy
    through parent-child relationships. Tasks maintain their state through
    status and priority flags.

    Attributes:
        id: Unique identifier
        title: Task title (non-empty string)
        description: Detailed task description
        user_id: ID of the task owner
        status: Current task status (TODO, IN_PROGRESS, etc.)
        priority: Task priority level (LOW, MEDIUM, HIGH)
        due_date: Optional deadline for the task
        tags: List of tags for categorization
        parent_id: Optional ID of parent task
        note_id: Optional ID of associated note
        created_at: Timestamp of task creation
        updated_at: Timestamp of last update
        owner: User who owns the task
        parent: Parent task if this is a subtask
        subtasks: List of child tasks
        note: Optional associated note
    """

    __tablename__ = "tasks"

    # Primary key
    id: Mapped[int] = Column(
        Integer, primary_key=True, index=True
    )

    # Basic fields
    title: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[str] = Column(Text, nullable=False)

    # Foreign keys
    user_id: Mapped[str] = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[Optional[int]] = Column(
        Integer,
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    note_id: Mapped[Optional[int]] = Column(
        Integer,
        ForeignKey("notes.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Status and metadata
    status: Mapped[TaskStatus] = Column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.TODO,
        server_default=TaskStatus.TODO.value,
    )
    priority: Mapped[TaskPriority] = Column(
        Enum(TaskPriority),
        nullable=False,
        default=TaskPriority.MEDIUM,
        server_default=TaskPriority.MEDIUM.value,
    )
    due_date: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), nullable=True
    )
    tags: Mapped[List[str]] = Column(
        JSON, nullable=True, default=list
    )

    # Timestamps
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User", back_populates="tasks"
    )
    parent: Mapped[Optional["Task"]] = relationship(
        "Task",
        remote_side=[id],
        back_populates="subtasks",
    )
    subtasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    note: Mapped[Optional["Note"]] = relationship(
        "Note",
        uselist=False,
        back_populates="tasks",
        doc="Optional note associated with this task",
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
    )

    def __init__(self, **kwargs):
        """Initialize task with defaults if not provided."""
        if "status" not in kwargs:
            kwargs["status"] = TaskStatus.TODO
        if "priority" not in kwargs:
            kwargs["priority"] = TaskPriority.MEDIUM
        if "tags" not in kwargs:
            kwargs["tags"] = []
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
            "parent_id": self.parent_id,
            "note_id": self.note_id,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date,
            "tags": self.tags or [],
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
