"""Service for managing documents."""

from typing import List, Optional
from fastapi import Depends, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from configs.Database import get_db
from domain.document import DocumentStatus
from repositories.DocumentRepository import DocumentRepository
from schemas.pydantic.DocumentSchema import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
)


class DocumentService:
    """Service for managing documents.

    This service handles the business logic for document operations,
    coordinating between the API layer and the repository layer.
    """

    def __init__(self, db: Session = Depends(get_db)):
        """Initialize service with database session.

        Args:
            db: Database session
        """
        self.repository = DocumentRepository(db)

    def create_document(
        self,
        document: DocumentCreate,
        user_id: str,
        file: UploadFile,
        storage_url: str,
    ) -> DocumentResponse:
        """Create a new document.

        Args:
            document: Document creation data
            user_id: ID of the document owner
            file: Uploaded file data
            storage_url: URL where the file is stored

        Returns:
            DocumentResponse: Created document data

        Raises:
            HTTPException: If document creation fails
        """
        # Convert to domain model
        domain_doc = document.to_domain(
            user_id=user_id,
            storage_url=storage_url,
            size_bytes=file.size,
        )

        # Create document in database
        db_doc = self.repository.create(
            name=domain_doc.name,
            storage_url=domain_doc.storage_url,
            mime_type=domain_doc.mime_type,
            size_bytes=domain_doc.size_bytes,
            user_id=domain_doc.user_id,
            metadata=domain_doc.metadata,
        )

        return DocumentResponse.from_orm(db_doc)

    def get_user_documents(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[DocumentStatus] = None,
        mime_type: Optional[str] = None,
    ) -> List[DocumentResponse]:
        """Get documents for a specific user.

        Args:
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by document status
            mime_type: Filter by MIME type

        Returns:
            List[DocumentResponse]: List of documents
        """
        documents = self.repository.get_by_user_id(
            user_id=user_id,
            skip=skip,
            limit=limit,
            status=status,
            mime_type=mime_type,
        )
        return [DocumentResponse.from_orm(doc) for doc in documents]

    def get_document(
        self, document_id: int, user_id: str
    ) -> DocumentResponse:
        """Get a specific document.

        Args:
            document_id: ID of the document
            user_id: ID of the user requesting the document

        Returns:
            DocumentResponse: Document data

        Raises:
            HTTPException: If document not found or user not authorized
        """
        document = self.repository.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if str(document.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this document",
            )
        return DocumentResponse.from_orm(document)

    def update_document(
        self,
        document_id: int,
        user_id: str,
        update_data: DocumentUpdate,
    ) -> DocumentResponse:
        """Update a document's metadata.

        Args:
            document_id: ID of the document to update
            user_id: ID of the user making the update
            update_data: New document data

        Returns:
            DocumentResponse: Updated document

        Raises:
            HTTPException: If update fails or user not authorized
        """
        document = self.repository.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if str(document.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this document",
            )

        # Update only allowed fields
        if update_data.metadata is not None:
            document.metadata = update_data.metadata

        self.repository.db.commit()
        return DocumentResponse.from_orm(document)

    def update_document_status(
        self,
        document_id: int,
        user_id: str,
        new_status: DocumentStatus,
    ) -> DocumentResponse:
        """Update a document's status.

        Args:
            document_id: ID of the document
            user_id: ID of the user making the update
            new_status: New status to set

        Returns:
            DocumentResponse: Updated document

        Raises:
            HTTPException: If update fails or user not authorized
        """
        document = self.repository.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if str(document.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this document",
            )

        updated = self.repository.update_status(
            document_id=document_id,
            new_status=new_status,
        )
        return DocumentResponse.from_orm(updated)

    def delete_document(self, document_id: int, user_id: str) -> None:
        """Delete a document.

        Args:
            document_id: ID of the document to delete
            user_id: ID of the user making the request

        Raises:
            HTTPException: If deletion fails or user not authorized
        """
        document = self.repository.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if str(document.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this document",
            )

        self.repository.delete(document)

    def get_user_storage_usage(self, user_id: str) -> int:
        """Get total storage usage for a user.

        Args:
            user_id: ID of the user

        Returns:
            int: Total size in bytes of all active documents
        """
        return self.repository.get_total_size_by_user(user_id)
