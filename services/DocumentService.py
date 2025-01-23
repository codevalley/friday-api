"""Service for managing documents."""

from typing import List, Optional, Tuple
import asyncio
from fastapi import (
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from domain.document import DocumentStatus
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
        storage_service=None,
    ):
        """Initialize service with repository and storage.

        Args:
            db: Database connection or repository instance
            storage_service: Optional storage service for testing
        """
        if isinstance(db, DocumentRepository):
            self.repository = db
        else:
            self.repository = DocumentRepository(db)

        self._storage = storage_service

    @property
    def storage(self) -> IStorageService:
        """Get storage service instance."""
        if self._storage is None:
            self._storage = (
                StorageFactory.create_storage_service()
            )
        return self._storage

    def create_document(
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
            # Create initial document record
            doc_data = document.to_domain(user_id=user_id)
            db_doc = self.repository.create(
                **doc_data.__dict__
            )

            try:
                # Handle async operations synchronously
                async def process_file():
                    # Read file content
                    content = await file.read()

                    # Store file in storage service
                    stored_file = await self.storage.store(
                        user_id=user_id,
                        file_name=document.name,
                        content=content,
                    )
                    return stored_file

                stored_file = asyncio.run(process_file())

                # Update document with storage info
                update_data = {
                    "storage_url": stored_file.path,
                    "size_bytes": stored_file.size_bytes,
                    "status": DocumentStatus.ACTIVE,
                }
                db_doc = self.repository.update(
                    db_doc.id, update_data
                )

                # Return document response
                self.repository.db.commit()
                return DocumentResponse.model_validate(
                    db_doc
                )
            except StorageError as e:
                # Update document status to ERROR if storage fails
                db_doc = self.repository.update(
                    db_doc.id,
                    {"status": DocumentStatus.ERROR},
                )
                self.repository.db.commit()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to store document: {str(e)}",
                ) from e
            except Exception as e:
                # Update document status to ERROR for any other failure
                db_doc = self.repository.update(
                    db_doc.id,
                    {"status": DocumentStatus.ERROR},
                )
                self.repository.db.commit()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to process document: {str(e)}",
                ) from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create document: {str(e)}",
            ) from e

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
        return [
            DocumentResponse.model_validate(doc)
            for doc in documents
        ]

    def get_document(
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
        document = self.repository.get_by_id(document_id)
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

        return DocumentResponse.model_validate(document)

    def get_document_content(
        self, document_id: int, user_id: str
    ) -> bytes:
        """Get the content of a document."""
        document = self.repository.get_by_id(document_id)
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

        # Handle async storage operations synchronously
        content = b""

        async def get_content():
            nonlocal content
            iterator = await self.storage.retrieve(
                document.storage_url.split("/")[-1], user_id
            )
            async for chunk in iterator:
                content += chunk
            return content

        return asyncio.run(get_content())

    def get_public_document(
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
        document = self.repository.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if not document.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Document is not public",
            )
        return DocumentResponse.model_validate(document)

    def get_public_document_content(
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
        document = self.get_public_document(document_id)
        content = b""

        async def get_content():
            nonlocal content
            iterator = await self.storage.retrieve(
                document.storage_url.split("/")[-1],
                document.user_id,
            )
            async for chunk in iterator:
                content += chunk
            return content

        content = asyncio.run(get_content())
        return document, content

    def update_document(
        self,
        document_id: int,
        user_id: str,
        update_data: DocumentUpdate,
    ) -> DocumentResponse:
        """Update a document.

        Args:
            document_id: ID of the document to update
            user_id: ID of the user making the request
            update_data: Document update data

        Returns:
            DocumentResponse: Updated document data

        Raises:
            HTTPException: If update fails or user not authorized
        """
        document = self.repository.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        if document.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this document",
            )

        try:
            # Prepare update data, only include non-None fields
            update_dict = {}
            for (
                field,
                value,
            ) in update_data.model_dump().items():
                if value is not None:
                    update_dict[field] = value

            # Update document
            db_doc = self.repository.update(
                document_id, update_dict
            )
            self.repository.db.commit()

            # Return updated document
            return DocumentResponse.model_validate(db_doc)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update document: {str(e)}",
            ) from e

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
                detail="You do not have permission to update this document",
            )

        updated_doc = self.repository.update_status(
            document_id, new_status
        )
        return DocumentResponse.model_validate(updated_doc)

    def delete_document(
        self, document_id: int, user_id: str
    ) -> None:
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

        if document.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this document",
            )

        # Delete from storage first
        async def delete_from_storage():
            await self.storage.delete(
                document.storage_url.split("/")[-1],
                user_id,
            )

        try:
            asyncio.run(delete_from_storage())
            self.repository.delete(document_id)
            self.repository.db.commit()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document: {str(e)}",
            ) from e

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
