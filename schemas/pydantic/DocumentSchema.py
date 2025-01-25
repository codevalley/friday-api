"""Pydantic schemas for document-related operations."""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from domain.document import DocumentStatus, DocumentData


class DocumentBase(BaseModel):
    """Base schema for document data."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

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
    doc_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata about the document",
        alias="metadata",
    )
    unique_name: Optional[str] = Field(
        None,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Unique identifier for public access",
    )
    is_public: bool = Field(
        False,
        description="Whether the document is publicly accessible",
    )


class DocumentCreate(DocumentBase):
    """Schema for document creation."""

    pass

    def to_domain(
        self,
        user_id: str,
    ) -> DocumentData:
        """Convert to domain model.

        Args:
            user_id: ID of the document owner

        Returns:
            DocumentData: Domain model instance
        """
        return DocumentData(
            name=self.name,
            mime_type=self.mime_type,
            user_id=user_id,
            metadata=self.doc_metadata,
            unique_name=self.unique_name,
            is_public=self.is_public,
        )


class DocumentUpdate(BaseModel):
    """Schema for document update."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "Updated Document",
                "metadata": {"key": "value"},
                "is_public": True,
                "unique_name": "updated-doc",
            }
        }
    )

    name: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = Field(
        None,
        alias="metadata",
    )
    is_public: Optional[bool] = None
    unique_name: Optional[str] = Field(
        None,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Unique identifier for public access",
    )


class DocumentStatusUpdate(BaseModel):
    """Document status update schema."""

    status: DocumentStatus


class DocumentResponse(DocumentBase):
    """Schema for document responses."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: int
    user_id: str
    storage_url: str
    size_bytes: int
    status: DocumentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    unique_name: Optional[str] = Field(
        None,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Unique identifier for public access",
    )
    is_public: bool = Field(
        False,
        description="Whether the document is publicly accessible",
    )
    doc_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata about the document",
        alias="metadata",
    )
