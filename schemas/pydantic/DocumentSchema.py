"""Pydantic schemas for document-related operations."""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, constr
from domain.document import DocumentStatus, DocumentData


class DocumentBase(BaseModel):
    """Base schema for document data.

    Attributes:
        name: Original name of the document
        mime_type: MIME type of the document
        metadata: Additional metadata about the document (optional)
        unique_name: Unique identifier for public access (optional)
        is_public: Whether the document is publicly accessible (default: False)
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original name of the document",
    )
    mime_type: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="MIME type of the document",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata about the document",
    )
    unique_name: Optional[
        constr(
            max_length=128,
            pattern=r"^[a-zA-Z0-9]+$",  # noqa: F722
        )
    ] = Field(
        None,
        description="Unique identifier for public access",
    )
    is_public: bool = Field(
        False,
        description="Whether the document is publicly accessible",
    )


class DocumentCreate(DocumentBase):
    """Schema for document creation.

    Note: storage_url and size_bytes are not included here as they
    will be set by the storage service after file upload.
    """

    def to_domain(
        self,
        user_id: str,
        storage_url: str,
        size_bytes: int,
    ) -> DocumentData:
        """Convert to domain model.

        Args:
            user_id: ID of the document owner
            storage_url: URL where the document is stored
            size_bytes: Size of the document in bytes

        Returns:
            DocumentData: Domain model instance
        """
        return DocumentData(
            name=self.name,
            storage_url=storage_url,
            mime_type=self.mime_type,
            size_bytes=size_bytes,
            user_id=user_id,
            metadata=self.metadata,
            unique_name=self.unique_name,
            is_public=self.is_public,
        )


class DocumentUpdate(BaseModel):
    """Schema for document updates.

    Only metadata can be updated directly. Other changes
    (like status) must be done through specific endpoints.
    """

    name: Optional[str] = Field(
        None, description="New name for the document"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated metadata for the document",
    )
    unique_name: Optional[
        constr(
            max_length=128,
            pattern=r"^[a-zA-Z0-9]+$",  # noqa: F722
        )
    ] = Field(
        None,
        description="Unique identifier for public access",
    )
    is_public: Optional[bool] = Field(
        None,
        description="Whether the document is publicly accessible",
    )


class DocumentResponse(DocumentBase):
    """Schema for document responses."""

    id: int
    user_id: str
    storage_url: str
    size_bytes: int
    status: DocumentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        orm_mode = True
