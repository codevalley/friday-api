"""Task ORM model."""

from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    JSON,
    Enum,
    CheckConstraint,
)
from sqlalchemy.orm import relationship, Mapped
from typing import TYPE_CHECKING

from domain.values import (
    TaskStatus,
    TaskPriority,
    ProcessingStatus,
)
from .BaseModel import EntityMeta

if TYPE_CHECKING:
    from .UserModel import User
    from .NoteModel import Note
    from .TopicModel import Topic


class Task(EntityMeta):
    """Task Model represents a single task or todo item.

    Each task belongs to a user and can optionally be part of a hierarchy
    through parent-child relationships. Tasks maintain their state through
    status and priority flags.

    Attributes:
        id: Unique identifier
        content: Task content in markdown format
        user_id: ID of the task owner
        status: Task progress status (TODO, IN_PROGRESS, DONE)
        priority: Task priority level (LOW, MEDIUM, HIGH)
        due_date: Optional deadline for the task
        tags: List of tags for categorization
        parent_id: Optional ID of parent task
        note_id: Optional ID of associated note
        topic_id: Optional ID of associated topic
        processing_status: Status of content processing
        enrichment_data: Data from content processing
        processed_at: When the content was processed
        created_at: When the task was created
        updated_at: When the task was last updated
        owner: User who owns the task
        parent: Parent task if this is a subtask
        subtasks: List of child tasks
        note: Optional associated note
        topic: Optional associated topic
    """

    __tablename__ = "tasks"

    # Primary key
    id: Mapped[int] = Column(
        Integer, primary_key=True, index=True
    )

    # Basic fields
    content: Mapped[str] = Column(
        String(512),
        nullable=False,
        doc="Task content in markdown format (max 512 chars)",
    )

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
    topic_id: Mapped[Optional[int]] = Column(
        Integer,
        ForeignKey("topics.id", ondelete="SET NULL"),
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
    processing_status: Mapped[ProcessingStatus] = Column(
        Enum(ProcessingStatus),
        nullable=False,
        default=ProcessingStatus.PENDING,
        server_default=ProcessingStatus.PENDING.value,
    )
    enrichment_data: Mapped[
        Optional[Dict[str, Any]]
    ] = Column(JSON, nullable=True, default=None)
    processed_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), nullable=True
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
    topic: Mapped[Optional["Topic"]] = relationship(
        "Topic",
        back_populates="tasks",
        doc="Optional topic associated with this task",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "content != ''",
            name="check_content_not_empty",
        ),
    )

    def __init__(self, **kwargs):
        """Initialize task with defaults if not provided."""
        if "status" not in kwargs:
            kwargs["status"] = TaskStatus.TODO
        if "priority" not in kwargs:
            kwargs["priority"] = TaskPriority.MEDIUM
        if "processing_status" not in kwargs:
            kwargs[
                "processing_status"
            ] = ProcessingStatus.PENDING
        if "tags" not in kwargs:
            kwargs["tags"] = []
        super().__init__(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of task
        """
        result = {
            "id": self.id,
            "content": self.content,
            "user_id": self.user_id,
            "parent_id": self.parent_id,
            "note_id": self.note_id,
            "topic_id": self.topic_id,
            "status": self.status,
            "priority": self.priority,
            "processing_status": self.processing_status,
            "enrichment_data": self.enrichment_data,
            "processed_at": self.processed_at,
            "due_date": self.due_date,
            "tags": self.tags or [],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

        if self.topic:
            result["topic"] = self.topic.to_dict()

        return result

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
