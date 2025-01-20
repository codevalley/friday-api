"""Domain model for Document management.

This module contains the domain models and business logic for document
management in the system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from zoneinfo import UTC

from domain.exceptions import DocumentValidationError


class DocumentStatus(str, Enum):
    """Document status enum."""
    PENDING = "pending"      # Document is being uploaded
    ACTIVE = "active"        # Document is available
    ARCHIVED = "archived"    # Document is archived (soft-deleted)
    ERROR = "error"          # Error in document processing


@dataclass
class DocumentData:
    """Domain model for Document.

    This class represents a document in the system and contains
    all business logic and validation rules for documents.

    Data Flow and Conversions:
    1. API Layer: Incoming data is validated by Pydantic schemas
       (DocumentCreate/DocumentUpdate)
    2. Domain Layer: Data is converted to DocumentData using to_domain()
       methods
    3. Database Layer: DocumentData is converted to ORM models
       using from_dict()
    4. Response: ORM models are converted back to DocumentData using from_orm()
    5. API Response: DocumentData is converted to response schemas
       using from_domain()

    Attributes:
        name: Original name of the document
        storage_url: URL where the document is stored
        mime_type: MIME type of the document
        size_bytes: Size of the document in bytes
        user_id: ID of the user who owns this document
        status: Current status of the document
        metadata: Additional metadata about the document (optional)
        id: Unique identifier for this document (optional)
        created_at: When this document was created
        updated_at: When this document was last updated
        unique_name: Unique identifier for public access (optional)
        is_public: Whether the document is publicly accessible
    """

    name: str
    storage_url: str
    mime_type: str
    size_bytes: int
    user_id: str
    status: DocumentStatus = DocumentStatus.PENDING
    metadata: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    unique_name: Optional[str] = None
    is_public: bool = False

    def __post_init__(self) -> None:
        """Validate document data after initialization."""
        # Set timestamps if not provided
        if self.created_at is None:
            self.created_at = datetime.now(UTC)
        if self.updated_at is None:
            self.updated_at = self.created_at

        self.validate()

    def validate(self, require_user_id: bool = True) -> None:
        """Validate document data.

        Args:
            require_user_id: Whether to require user_id to be set

        Raises:
            DocumentValidationError: If validation fails
        """
        if not self.name:
            raise DocumentValidationError("name is required")

        if not self.storage_url:
            raise DocumentValidationError("storage_url is required")

        if not self.mime_type:
            raise DocumentValidationError("mime_type is required")

        if self.size_bytes < 0:
            raise DocumentValidationError("size_bytes must be non-negative")

        if require_user_id and not self.user_id:
            raise DocumentValidationError("user_id is required")

        if not isinstance(self.status, DocumentStatus):
            raise DocumentValidationError(
                f"invalid status: {self.status}"
            )

        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise DocumentValidationError(
                "metadata must be a dictionary if provided"
            )

        if self.unique_name is not None:
            if len(self.unique_name) > 128:
                raise DocumentValidationError(
                    "unique_name must be 128 characters or less"
                )
            if not self.unique_name.isalnum():
                raise DocumentValidationError(
                    "unique_name must be alphanumeric"
                )

    def can_access(self, user_id: Optional[str]) -> bool:
        """Check if a user can access this document.

        Args:
            user_id: ID of the user requesting access, or None for public access

        Returns:
            bool: True if the user can access the document
        """
        return self.is_public or (user_id and user_id == self.user_id)

    def can_modify(self, user_id: str) -> bool:
        """Check if a user can modify this document.

        Args:
            user_id: ID of the user requesting modification

        Returns:
            bool: True if the user can modify the document
        """
        return user_id == self.user_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for repository operations.

        Returns:
            dict: Dictionary representation of the document
        """
        return {
            "id": self.id,
            "name": self.name,
            "storage_url": self.storage_url,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "user_id": self.user_id,
            "status": self.status.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "unique_name": self.unique_name,
            "is_public": self.is_public,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentData':
        """Create DocumentData from dictionary data.

        Args:
            data: Dictionary containing document data

        Returns:
            DocumentData instance
        """
        # Convert string status to enum if needed
        status = data.get("status")
        if isinstance(status, str):
            status = DocumentStatus(status)
        elif status is None:
            status = DocumentStatus.PENDING

        # Handle both snake_case and camelCase keys
        user_id = data.get("user_id") or data.get("userId")

        return cls(
            id=data.get("id"),
            name=data["name"],
            storage_url=data["storage_url"],
            mime_type=data["mime_type"],
            size_bytes=data["size_bytes"],
            user_id=user_id,
            status=status,
            metadata=data.get("metadata"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            unique_name=data.get("unique_name"),
            is_public=data.get("is_public", False),
        )

    @classmethod
    def from_orm(cls, orm_model: Any) -> 'DocumentData':
        """Create a DocumentData instance from an ORM model.

        This method is the bridge between the database layer and domain layer.
        It ensures that data from the database is properly validated before use.

        Args:
            orm_model: SQLAlchemy model instance

        Returns:
            DocumentData: New instance with validated data from the database
        """
        return cls(
            id=str(orm_model.id),
            name=orm_model.name,
            storage_url=orm_model.storage_url,
            mime_type=orm_model.mime_type,
            size_bytes=orm_model.size_bytes,
            user_id=str(orm_model.user_id),
            status=DocumentStatus(orm_model.status),
            metadata=orm_model.metadata,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
            unique_name=orm_model.unique_name,
            is_public=orm_model.is_public,
        )

    def update_status(self, new_status: DocumentStatus) -> None:
        """Update document status.

        Args:
            new_status: New status to set

        Raises:
            DocumentValidationError: If status transition is invalid
        """
        if not isinstance(new_status, DocumentStatus):
            raise DocumentValidationError(
                f"invalid status: {new_status}"
            )

        # Validate status transitions
        if (self.status == DocumentStatus.ARCHIVED and
                new_status != DocumentStatus.ACTIVE):
            raise DocumentValidationError(
                "archived documents can only be restored to active"
            )

        self.status = new_status
        self.updated_at = datetime.now(UTC)
