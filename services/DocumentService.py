"""Service for managing documents."""

from typing import List, Optional, Tuple
from fastapi import (
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from domain.document import DocumentData, DocumentStatus
from domain.storage import IStorageService, StorageError
from schemas.pydantic.DocumentSchema import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
)
from repositories.DocumentRepository import (
    DocumentRepository,
)
from configs.Database import get_db_connection
from infrastructure.storage.factory import StorageFactory


class DocumentService:
    """Service for managing documents."""

    def __init__(
        self,
        db=Depends(get_db_connection),
        storage: Optional[IStorageService] = None,
    ):
        """Initialize service with repository and storage.

        Args:
            db: Database connection or repository instance
            storage: Storage service implementation
        """
        if isinstance(db, DocumentRepository):
            self.repository = db
        else:
            self.repository = DocumentRepository(db)

        self.storage = (
            storage
            or StorageFactory.create_storage_service()
        )

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
            content = await file.read()

            # Store file in storage service
            stored_file = await self.storage.store(
                user_id=user_id,
                file_name=document.name,
                content=content,
            )

            # Create document in database
            db_doc = await self.repository.create(
                DocumentData(
                    name=document.name,
                    mime_type=document.mime_type,
                    metadata=document.metadata,
                    storage_url=stored_file.path,
                    size_bytes=stored_file.size_bytes,
                    user_id=user_id,
                    is_public=False,
                )
            )

            # Return document response
            return DocumentResponse.model_validate(db_doc)
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
        return [
            DocumentResponse.from_orm(doc)
            for doc in documents
        ]

    async def get_document(
        self, document_id: int, user_id: str
    ) -> DocumentResponse:
        """Get a document by ID.

        Args:
            document_id: ID of the document
            user_id: ID of the user making the request

        Returns:
            DocumentResponse: Document data

        Raises:
            HTTPException: If document not found or user not authorized
        """
        document = await self.repository.get_by_id(
            document_id
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        if (
            str(document.user_id) != user_id
            and not document.is_public
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this document",
            )

        return DocumentResponse.from_orm(document)

    async def get_document_content(
        self, document_id: int, user_id: str
    ) -> bytes:
        """Get the content of a document."""
        document = await self.repository.get_by_id(
            document_id
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        if (
            document.user_id != user_id
            and not document.is_public
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this document",
            )

        content = b""
        async for chunk in self.storage.retrieve(
            document.storage_url.split("/")[-1], user_id
        ):
            content += chunk
        return content

    async def get_public_document(
        self,
        document_id: int,
    ) -> DocumentResponse:
        """Get a public document.

        Args:
            document_id: ID of the document

        Returns:
            DocumentResponse: Document data

        Raises:
            HTTPException: If document not found or not public
        """
        document = await self.repository.get_by_id(
            document_id
        )
        if not document or not document.is_public:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or not public",
            )

        return DocumentResponse.from_orm(document)

    async def get_public_document_content(
        self,
        document_id: int,
    ) -> Tuple[DocumentResponse, bytes]:
        """Get a public document's content.

        Args:
            document_id: ID of the document

        Returns:
            Tuple[DocumentResponse, bytes]: Document metadata and content

        Raises:
            HTTPException: If document not found or not public
        """
        document = await self.repository.get_by_id(
            document_id
        )
        if not document or not document.is_public:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or not public",
            )

        content = b""
        async for chunk in self.storage.retrieve(
            document.storage_url.split("/")[-1]
        ):
            content += chunk

        return DocumentResponse.from_orm(document), content

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
        document = await self.repository.get_by_id(
            document_id
        )
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

        await self.repository.db.commit()
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
        document = await self.repository.get_by_id(
            document_id
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if str(document.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this document",
            )

        updated_doc = await self.repository.update_status(
            document_id, new_status
        )
        return DocumentResponse.from_orm(updated_doc)

    async def delete_document(
        self, document_id: int, user_id: str
    ) -> None:
        """Delete a document.

        Args:
            document_id: ID of the document to delete
            user_id: ID of the user making the request

        Raises:
            HTTPException: If deletion fails or user not authorized
        """
        document = await self.repository.get_by_id(
            document_id
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if str(document.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this document",
            )

        await self.repository.delete(document_id)
        await self.storage.delete(
            document.storage_url.split("/")[-1], user_id
        )

    def get_user_storage_usage(self, user_id: str) -> int:
        """Get total storage usage for a user.

        Args:
            user_id: ID of the user

        Returns:
            int: Total size in bytes of all active documents
        """
        return self.repository.get_total_size_by_user(
            user_id
        )
