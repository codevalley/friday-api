"""Repository for managing documents in the database."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
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

    def create(self, **kwargs) -> Document:
        """Create a new document.

        Args:
            **kwargs: Document attributes

        Returns:
            Document: Created document instance

        Raises:
            DocumentValidationError: If document creation fails due to invalid data
        """
        document = Document(**kwargs)
        try:
            return super().create(document)
        except HTTPException as e:
            if e.status_code == 409:
                raise DocumentValidationError(
                    "Document creation failed: duplicate entry"
                )
            raise DocumentValidationError(str(e.detail))
        except IntegrityError as e:
            raise DocumentValidationError(
                f"Document creation failed: {str(e)}"
            )

    def get_by_user_id(
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
        query = self.db.query(Document).filter(Document.user_id == user_id)

        # Apply filters
        if status:
            query = query.filter(Document.status == status)
        if mime_type:
            query = query.filter(Document.mime_type == mime_type)

        # Apply ordering
        order_column = getattr(Document, order_by, Document.created_at)
        if order == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        return query.offset(skip).limit(limit).all()

    def update_status(
        self, document_id: int, new_status: DocumentStatus
    ) -> Document:
        """Update document status.

        Args:
            document_id: ID of the document to update
            new_status: New status to set

        Returns:
            Document: Updated document

        Raises:
            DocumentStatusError: If status transition is invalid
        """
        document = self.get_by_id(document_id)
        if not document:
            raise DocumentValidationError(
                f"Document not found: {document_id}"
            )

        try:
            document.status = new_status
            document.updated_at = datetime.utcnow()
            self.db.commit()
            return document
        except IntegrityError as e:
            self.db.rollback()
            raise DocumentStatusError(
                f"Failed to update document status: {str(e)}"
            )

    def get_by_storage_url(self, storage_url: str) -> Optional[Document]:
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
                func.sum(Document.size_bytes).label("total_size")
            )
            .first()
        )
        return result.total_size or 0
