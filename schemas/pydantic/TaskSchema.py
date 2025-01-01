"""Pydantic schemas for task-related operations."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from domain.values import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    """Base schema for task data."""

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    status: TaskStatus = Field(default=TaskStatus.TODO)
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM
    )
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    parent_id: Optional[int] = None


class TaskCreate(TaskBase):
    """Schema for task creation."""

    def to_domain(self, user_id: str) -> dict:
        """Convert to domain model data."""
        return {
            **self.model_dump(),
            "user_id": user_id,
        }


class TaskUpdate(BaseModel):
    """Schema for task updates."""

    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, min_length=1)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    parent_id: Optional[int] = None


class TaskResponse(TaskBase):
    """Schema for task responses."""

    id: int
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True
