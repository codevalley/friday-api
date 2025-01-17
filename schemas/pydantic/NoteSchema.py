"""Note schemas for request/response validation."""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from domain.note import NoteData
from domain.values import ProcessingStatus
from schemas.pydantic.PaginationSchema import PaginationResponse


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


class NoteList(PaginationResponse):
    """Response schema for list of Notes.

    This schema is used for paginated responses when listing notes.
    It includes pagination metadata along with the list of notes.

    Attributes:
        items: List of notes
        total: Total number of items
        page: Current page number
        size: Items per page
        pages: Total number of pages
    """

    items: List[NoteResponse] = Field(
        description="List of notes on this page"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "content": "Meeting notes for Q1 planning",
                        "attachments": [],
                        "processing_status": "NOT_PROCESSED",
                        "enrichment_data": None,
                        "processed_at": None,
                        "created_at": "2024-01-11T12:00:00Z",
                        "updated_at": "2024-01-12T15:30:00Z",
                    },
                    {
                        "id": 2,
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "content": "Ideas for new features",
                        "attachments": [
                            {
                                "type": "image",
                                "url": "https://example.com/sketch.png"
                            }
                        ],
                        "processing_status": "PROCESSED",
                        "enrichment_data": {
                            "topics": ["features", "planning"],
                            "sentiment": "positive"
                        },
                        "processed_at": "2024-01-11T12:05:00Z",
                        "created_at": "2024-01-11T12:00:00Z",
                        "updated_at": None,
                    }
                ],
                "total": 10,
                "page": 1,
                "size": 2,
                "pages": 5
            }
        }
    )

    @classmethod
    def from_domain(
        cls, items: List[NoteData], page: int, size: int, total: int
    ) -> "NoteList":
        """Create paginated response from domain models.

        Args:
            items: List of note domain models
            page: Current page number
            size: Items per page
            total: Total number of items

        Returns:
            NoteList: Paginated response with notes and metadata
        """
        return cls(
            items=[
                NoteResponse.from_domain(item)
                for item in items
            ],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )
