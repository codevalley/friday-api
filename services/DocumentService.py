"""Service for managing documents."""

from typing import List, Optional
from fastapi import Depends, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from configs.Database import get_db_connection
from domain.document import DocumentStatus
from domain.storage import IStorageService, StorageError, FileNotFoundError
from repositories.DocumentRepository import DocumentRepository
from infrastructure.storage.factory import StorageFactory
from schemas.pydantic.DocumentSchema import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
)


class DocumentService:
    """Service for managing documents.

    This service handles the business logic for document operations,
    coordinating between the API layer, repository layer, and storage layer.
    """

    def __init__(
        self,
        db: Session = Depends(get_db_connection),
        storage: IStorageService = Depends(StorageFactory.create_storage_service),
    ):
        """Initialize service with database session and storage.

        Args:
            db: Database session
            storage: Storage service implementation
        """
        self.repository = DocumentRepository(db)
        self.storage = storage

    async def create_document(
        self,
        document: DocumentCreate,
        user_id: str,
        file: UploadFile,
    ) -> DocumentResponse:
        """Create a new document.

        Args:
            document: Document creation data
            user_id: ID of the document owner
            file: Uploaded file data

        Returns:
            DocumentResponse: Created document data

        Raises:
            HTTPException: If document creation fails
        """
        try:
            # Read file content
            file_content = await file.read()
            file_id = str(uuid.uuid4())

            # Store file in storage backend
            stored_file = await self.storage.store(
                file_data=file_content,
                file_id=file_id,
                user_id=user_id,
                mime_type=document.mime_type,
            )

            # Create document in database
            db_doc = self.repository.create(
                name=document.name,
                storage_url=stored_file.path,
                mime_type=stored_file.mime_type,
                size_bytes=stored_file.size_bytes,
                user_id=user_id,
                metadata=document.metadata,
            )

            return DocumentResponse.from_orm(db_doc)
        except StorageError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store document: {str(e)}",
            )

    async def get_user_documents(
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

    async def get_document(
        self,
        document_id: int,
        user_id: str,
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

    async def get_document_content(
        self,
        document_id: int,
        user_id: str,
    ) -> bytes:
        """Get a document's content.

        Args:
            document_id: ID of the document
            user_id: ID of the user requesting the document

        Returns:
            bytes: Document content

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

        try:
            content = b""
            async for chunk in self.storage.retrieve(
                file_id=document.storage_url.split("/")[-1],
                user_id=user_id,
            ):
                content += chunk
            return content
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document content not found",
            )
        except StorageError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve document: {str(e)}",
            )

    async def update_document(
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

    async def update_document_status(
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

    async def delete_document(self, document_id: int, user_id: str) -> None:
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

        try:
            # Delete from storage first
            await self.storage.delete(
                file_id=document.storage_url.split("/")[-1],
                user_id=user_id,
            )
            # Then remove from database
            self.repository.delete(document)
        except StorageError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document: {str(e)}",
            )

    def get_user_storage_usage(self, user_id: str) -> int:
        """Get total storage usage for a user.

        Args:
            user_id: ID of the user

        Returns:
            int: Total size in bytes of all active documents
        """
        return self.repository.get_total_size_by_user(user_id)
