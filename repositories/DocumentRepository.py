"""Repository for managing documents in the database."""

from typing import List, Optional
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from domain.document import DocumentStatus
from orm.DocumentModel import Document
from .BaseRepository import BaseRepository
from domain.exceptions import (
    DocumentValidationError,
    DocumentStatusError,
)


class DocumentRepository(BaseRepository[Document, int]):
    """Repository for managing Document entities.

    This repository extends the BaseRepository to provide CRUD operations
    for Document entities, along with document-specific functionality like
    filtering by status, type, and size.
    """

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        super().__init__(db, Document)

    def create(self, document: Document) -> Document:
        """Create a new document.

        Args:
            document: Document model to create

        Returns:
            Document: Created document instance

        Raises:
            DocumentValidationError: If doc creation fails due to invalid data
            HTTPException: If unique name already exists
        """
        try:
            # Check if unique_name already exists
            if document.unique_name:
                existing = (
                    self.db.query(Document)
                    .filter(
                        Document.unique_name
                        == document.unique_name
                    )
                    .first()
                )
                if existing:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Document with unique_name "
                        f"{document.unique_name} already exists",
                    )

            # Ensure metadata is a dictionary
            self._ensure_metadata_dict(document)

            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            return document
        except IntegrityError as e:
            self.db.rollback()
            raise DocumentValidationError(str(e)) from e

    def list_documents(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[DocumentStatus] = None,
        mime_type: Optional[str] = None,
        order_by: str = "created_at",
        order: str = "desc",
    ) -> List[Document]:
        """Get documents for a specific user with optional filtering.

        Args:
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by document status
            mime_type: Filter by MIME type
            order_by: Field to order by (created_at, name, size_bytes)
            order: Sort order (asc or desc)

        Returns:
            List[Document]: List of documents matching the criteria
        """
        query = self.db.query(Document).filter(
            Document.user_id == user_id
        )

        # Apply filters
        if status:
            query = query.filter(Document.status == status)
        if mime_type:
            query = query.filter(
                Document.mime_type == mime_type
            )

        # Apply ordering
        order_column = getattr(
            Document, order_by, Document.created_at
        )
        if order == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        return query.offset(skip).limit(limit).all()

    def update_status(
        self,
        document_id: int,
        user_id: str,
        new_status: DocumentStatus,
    ) -> Optional[Document]:
        """Update document status.

        Args:
            document_id: ID of the document to update
            user_id: ID of the document owner
            new_status: New status to set

        Returns:
            Document: Updated doc if found and owned by user, None otherwise

        Raises:
            DocumentStatusError: If status transition is invalid
        """
        document = self.get_by_owner(document_id, user_id)
        if not document:
            return None

        try:
            document.status = new_status
            document.updated_at = datetime.now(UTC)
            self.db.commit()
            return document
        except IntegrityError as e:
            self.db.rollback()
            raise DocumentStatusError(
                f"Failed to update document status: {str(e)}"
            )

    def get_by_storage_url(
        self, storage_url: str
    ) -> Optional[Document]:
        """Get document by its storage URL.

        Args:
            storage_url: URL where the document is stored

        Returns:
            Optional[Document]: Document if found, None otherwise
        """
        return (
            self.db.query(Document)
            .filter(Document.storage_url == storage_url)
            .first()
        )

    def get_by_unique_name(
        self, unique_name: str
    ) -> Optional[Document]:
        """Get public document by its unique name.

        Args:
            unique_name: Unique identifier for public access

        Returns:
            Optional[Document]: Document if found and public, None otherwise
        """
        return (
            self.db.query(Document)
            .filter(
                Document.unique_name == unique_name,
                Document.is_public == True,  # noqa: E712
            )
            .first()
        )

    def delete(self, id: int, user_id: str) -> bool:
        """Delete a document by ID and verify ownership.

        Args:
            id: Document ID
            user_id: Owner's user ID

        Returns:
            bool: True if doc was deleted, False if not found or owned by user
        """
        document = self.get_by_owner(id, user_id)
        if not document:
            return False

        self.db.delete(document)
        self.db.commit()
        return True

    def get_total_size_by_user(self, user_id: str) -> int:
        """Get total size of all active documents for a user.

        Args:
            user_id: ID of the user

        Returns:
            int: Total size in bytes
        """
        result = (
            self.db.query(Document)
            .filter(
                Document.user_id == user_id,
                Document.status == DocumentStatus.ACTIVE,
            )
            .with_entities(
                func.sum(Document.size_bytes).label(
                    "total_size"
                )
            )
            .first()
        )
        return result.total_size or 0

    def _ensure_metadata_dict(
        self, document: Document
    ) -> None:
        """Ensure document metadata is a dictionary.

        Args:
            document: Document instance to check

        Returns:
            None
        """
        if document.doc_metadata is None:
            document.doc_metadata = {}
        elif not isinstance(document.doc_metadata, dict):
            document.doc_metadata = {}

    def get_by_id(
        self, id: int, user_id: str = None
    ) -> Optional[Document]:
        """Get document by ID and optionally user ID.

        Args:
            id: Document ID
            user_id: Optional User ID. If provided, checks access permissions.

        Returns:
            Optional[Document]: Document if found, None otherwise
        """
        document = (
            self.db.query(Document)
            .filter(Document.id == id)
            .first()
        )

        if document:
            self._ensure_metadata_dict(document)
            if (
                user_id is None
                or document.user_id == user_id
                or document.is_public
            ):
                return document
        return None

    def list(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10,
        offset: int = None,  # For backward compatibility
        filters: dict = None,
    ) -> List[Document]:
        """List documents for a user with optional filters.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            offset: Deprecated, use skip instead
            filters: Optional filters to apply

        Returns:
            List[Document]: List of documents
        """
        # Use offset if provided for backward compatibility
        if offset is not None:
            skip = offset

        # Base query for user's own documents
        query = self.db.query(Document).filter(
            Document.user_id == user_id
        )

        # Include public documents only if requested
        if filters and filters.get("include_public"):
            query = self.db.query(Document).filter(
                (Document.user_id == user_id)
                | Document.is_public
            )

        if filters:
            if filters.get("status"):
                query = query.filter(
                    Document.status == filters["status"]
                )
            if filters.get("mime_type"):
                query = query.filter(
                    Document.mime_type
                    == filters["mime_type"]
                )
            if filters.get("name"):
                query = query.filter(
                    Document.name.ilike(
                        f"%{filters['name']}%"
                    )
                )

        documents = query.offset(skip).limit(limit).all()
        for document in documents:
            self._ensure_metadata_dict(document)
        return documents

    def count_by_user(self, user_id: str) -> int:
        """Count total documents for a user.

        Args:
            user_id: ID of the user

        Returns:
            int: Total number of documents
        """
        return (
            self.db.query(Document)
            .filter(Document.user_id == user_id)
            .count()
        )
