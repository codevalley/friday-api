"""Pydantic schemas for document-related operations."""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    constr,
)
from domain.document import DocumentStatus, DocumentData


# Type alias for alphanumeric + underscore string
UniqueName = constr(pattern=r"^[a-zA-Z0-9_]+$")


class DocumentBase(BaseModel):
    """Base schema for document data."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "example.pdf",
                "mime_type": "application/pdf",
                "metadata": {
                    "category": "reports",
                    "tags": ["2024", "Q1"],
                },
                "unique_name": "q1_report_2024",
                "is_public": False,
            }
        },
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original name of the document",
        examples=["report.pdf", "image.jpg", "data.csv"],
    )
    mime_type: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=r"^[a-z]+/[a-z0-9\-\+\.]+$",
        description=(
            "MIME type of the document "
            "(e.g., application/pdf, image/jpeg)"
        ),
        examples=[
            "application/pdf",
            "image/jpeg",
            "text/plain",
        ],
    )
    doc_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata about the document",
        alias="metadata",
        examples=[
            {"category": "reports", "tags": ["2024", "Q1"]},
            {"author": "John Doe", "department": "Finance"},
        ],
    )
    unique_name: Optional[UniqueName] = Field(
        default=None,
        max_length=128,
        description=(
            "Unique identifier for public access "
            "(alphanumeric and underscore only)"
        ),
        examples=[
            "q1_report_2024",
            "user_manual_v1",
            "data_2024",
        ],
    )
    is_public: bool = Field(
        default=False,
        description="Whether the document is publicly accessible",
    )


class DocumentCreate(DocumentBase):
    """Schema for document creation."""

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
            metadata=self.doc_metadata
            or {},  # Ensure metadata is never None
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
                "name": "Updated Report.pdf",
                "metadata": {
                    "status": "reviewed",
                    "reviewer": "Jane Smith",
                },
                "is_public": True,
                "unique_name": "reviewed_report_2024",
            }
        },
    )

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New name for the document",
    )
    doc_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        alias="metadata",
        description="Updated metadata for the document",
    )
    is_public: Optional[bool] = Field(
        default=None,
        description="Whether to make the document public",
    )
    unique_name: Optional[UniqueName] = Field(
        default=None,
        max_length=128,
        description=(
            "New unique identifier for public access "
            "(alphanumeric and underscore only)"
        ),
    )


class DocumentStatusUpdate(BaseModel):
    """Document status update schema."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"status": "ARCHIVED"}
        }
    )

    status: DocumentStatus = Field(
        ...,
        description="New status for the document",
    )


class DocumentResponse(DocumentBase):
    """Schema for document responses."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": "user123",
                "name": "report.pdf",
                "mime_type": "application/pdf",
                "storage_url": "s3://bucket/user123/doc1.pdf",
                "size_bytes": 1048576,
                "status": "ACTIVE",
                "created_at": "2024-01-25T12:00:00Z",
                "updated_at": "2024-01-25T12:00:00Z",
                "metadata": {"category": "reports"},
                "unique_name": "report_2024",
                "is_public": False,
            }
        },
    )

    id: int = Field(
        ...,
        description="Unique identifier for the document",
    )
    user_id: str = Field(
        ...,
        description="ID of the document owner",
    )
    storage_url: str = Field(
        ...,
        description="URL where the document is stored",
    )
    size_bytes: int = Field(
        ...,
        ge=0,
        description="Size of the document in bytes",
    )
    status: DocumentStatus = Field(
        ...,
        description="Current status of the document",
    )
    created_at: datetime = Field(
        ...,
        description="When the document was created",
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="When the document was last updated",
    )
