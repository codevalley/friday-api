"""Note schemas for request/response validation."""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from domain.note import NoteData
from domain.values import ProcessingStatus


class NoteBase(BaseModel):
    """Base schema for note data validation."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Content of the note",
    )
    attachments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of attachments",
    )
    processing_status: ProcessingStatus = Field(
        default_factory=ProcessingStatus.default,
        description="Processing status of the note",
    )


class NoteCreate(BaseModel):
    """Schema for creating a new note."""

    content: str = Field(
        ..., min_length=1, max_length=10000
    )
    attachments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of attachments",
    )

    def to_domain(self, user_id: str) -> NoteData:
        """Convert to domain model.

        Args:
            user_id: ID of the user creating the note

        Returns:
            NoteData instance with validated data
        """
        return NoteData(
            content=self.content,
            user_id=user_id,
            attachments=self.attachments,
        )


class NoteUpdate(BaseModel):
    """Schema for updating an existing note."""

    content: Optional[str] = Field(
        None, min_length=1, max_length=2000
    )
    attachments: Optional[List[Dict[str, Any]]] = None
    processing_status: Optional[ProcessingStatus] = Field(
        None, description="New processing status"
    )


class NoteResponse(BaseModel):
    """Schema for note responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    user_id: str
    attachments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of attachments",
    )
    processing_status: ProcessingStatus = Field(
        default_factory=ProcessingStatus.default,
        description="Processing status of the note",
    )
    enrichment_data: Optional[Dict[str, Any]] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @classmethod
    def from_domain(
        cls, domain: NoteData
    ) -> "NoteResponse":
        """Create response from domain model.

        Args:
            domain: NoteData instance

        Returns:
            NoteResponse instance
        """
        return cls(
            id=domain.id,
            content=domain.content,
            user_id=domain.user_id,
            attachments=domain.attachments,
            processing_status=domain.processing_status,
            enrichment_data=domain.enrichment_data,
            processed_at=domain.processed_at,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )


class NoteList(BaseModel):
    """Schema for list of notes."""

    items: List[NoteResponse]
    total: int
    page: Optional[int] = 1
    size: Optional[int] = 10
    pages: Optional[int] = 1
