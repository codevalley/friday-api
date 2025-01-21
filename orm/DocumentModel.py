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
    BigInteger,
    Boolean,
    event,
)
from sqlalchemy.orm import relationship, Mapped
from typing import TYPE_CHECKING

from domain.document import DocumentStatus, DocumentData
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

    # Primary key
    id = Column(Integer, primary_key=True)

    # Basic document metadata
    name = Column(String(255), nullable=False)
    storage_url = Column(String(2048), nullable=False)
    mime_type = Column(String(255), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)

    # Document status
    status = Column(
        Enum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.PENDING,
    )

    # Optional metadata as JSON
    doc_metadata = Column(
        JSON, nullable=True
    )  # Renamed from metadata to avoid conflict

    # Foreign keys and relationships
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner: Mapped["User"] = relationship(
        "User", back_populates="documents"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Public access fields
    unique_name = Column(
        String(128), nullable=True, unique=True
    )
    is_public = Column(
        Boolean, nullable=False, default=False
    )

    def to_domain(self) -> DocumentData:
        """Convert ORM model to domain model.

        Returns:
            DocumentData: Domain model instance
        """
        return DocumentData(
            id=str(self.id),
            name=self.name,
            storage_url=self.storage_url,
            mime_type=self.mime_type,
            size_bytes=self.size_bytes,
            user_id=str(self.user_id),
            status=self.status,
            metadata=self.doc_metadata,
            created_at=self.created_at,
            updated_at=self.updated_at,
            unique_name=self.unique_name,
            is_public=self.is_public,
        )

    @classmethod
    def from_domain(
        cls, domain: DocumentData
    ) -> "Document":
        """Create ORM model from domain model.

        Args:
            domain: Domain model instance

        Returns:
            Document: New ORM model instance
        """
        return cls(
            id=int(domain.id) if domain.id else None,
            name=domain.name,
            storage_url=domain.storage_url,
            mime_type=domain.mime_type,
            size_bytes=domain.size_bytes,
            user_id=domain.user_id,
            status=domain.status,
            doc_metadata=domain.metadata,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
            unique_name=domain.unique_name,
            is_public=domain.is_public,
        )


@event.listens_for(Document, "before_update")
def receive_before_update(mapper, connection, target):
    """Update the updated_at timestamp before any update."""
    target.updated_at = datetime.now(UTC)
