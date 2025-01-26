"""Document ORM model."""

from datetime import datetime, UTC
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    JSON,
    Enum,
    Boolean,
    event,
)
from sqlalchemy.orm import relationship, Mapped
from typing import TYPE_CHECKING, Optional, Dict, Any

from domain.values import DocumentStatus
from .BaseModel import EntityMeta

if TYPE_CHECKING:
    from .UserModel import User


class Document(EntityMeta):
    """Document Model represents a stored document or file.

    Each document belongs to a user and contains metadata about the stored
    file, including its location, size, and type. Documents maintain their
    state through a status flag.

    Attributes:
        id: Unique identifier
        name: Original name of the document
        storage_url: URL where the document is stored
        mime_type: MIME type of the document
        size_bytes: Size of the document in bytes
        user_id: ID of the document owner
        status: Current document status (PENDING, ACTIVE, etc.)
        metadata: Additional metadata about the document (optional)
        created_at: Timestamp of document creation
        updated_at: Timestamp of last update
        owner: User who owns the document
        unique_name: Unique identifier for public access (optional)
        is_public: Whether the document is publicly accessible
    """

    __tablename__ = "documents"

    # Primary key
    id: Mapped[int] = Column(Integer, primary_key=True)

    # Basic document metadata
    name: Mapped[str] = Column(String(255), nullable=False)
    mime_type: Mapped[str] = Column(
        String(255), nullable=False
    )
    storage_url: Mapped[Optional[str]] = Column(
        String(1024), nullable=True
    )
    doc_metadata: Mapped[Optional[Dict[str, Any]]] = Column(
        JSON, nullable=True
    )  # Renamed from metadata to avoid conflict

    # Document status
    status: Mapped[DocumentStatus] = Column(
        Enum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.ACTIVE,
        server_default=DocumentStatus.ACTIVE.value,
    )

    # Foreign keys and relationships
    user_id: Mapped[str] = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="documents",
    )

    # File size
    size_bytes: Mapped[int] = Column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Public access fields
    unique_name: Mapped[Optional[str]] = Column(
        String(128), nullable=True, unique=True
    )
    is_public: Mapped[bool] = Column(
        Boolean, nullable=False, default=False
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "user_id": self.user_id,
            "status": self.status,
            "metadata": self.doc_metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "storage_url": self.storage_url,
            "unique_name": self.unique_name,
            "is_public": self.is_public,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create document from dictionary.

        Args:
            data: Dictionary containing document data

        Returns:
            Document: New document instance
        """
        # Convert string status to enum if needed
        status = data.get("status")
        if isinstance(status, str):
            status = DocumentStatus(status)
        elif status is None:
            status = DocumentStatus.PENDING

        # Handle metadata field name difference
        metadata = data.get("metadata", {})
        if metadata is None:
            metadata = {}

        return cls(
            id=data.get("id"),
            name=data["name"],
            mime_type=data["mime_type"],
            size_bytes=data.get("size_bytes"),
            user_id=data["user_id"],
            status=status,
            doc_metadata=metadata,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            storage_url=data.get("storage_url"),
            unique_name=data.get("unique_name"),
            is_public=data.get("is_public", False),
        )


@event.listens_for(Document, "before_update")
def receive_before_update(mapper, connection, target):
    """Update the updated_at timestamp before any update."""
    target.updated_at = datetime.now(UTC)
