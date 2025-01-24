"""Service layer for document operations."""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, UploadFile, status
from io import BytesIO

from domain.document import DocumentData, DocumentStatus
from domain.storage import IStorageService, StorageError
from repositories.DocumentRepository import DocumentRepository
from schemas.pydantic.DocumentSchema import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
)
from orm.DocumentModel import Document


class DocumentService:
    """Service for document operations."""

    def __init__(
        self,
        repository: DocumentRepository,
        storage: IStorageService,
    ):
        """Initialize document service.

        Args:
            repository: Document repository instance
            storage: Storage service instance
        """
        self.repository = repository
        self.storage = storage

    async def _get_document_internal(self, document_id: int) -> Optional[Document]:
        """Get document by ID for internal use.

        Args:
            document_id: ID of the document to retrieve

        Returns:
            Optional[Document]: Document if found, None otherwise
        """
        return self.repository.get_by_id(document_id)

    async def _get_document_for_user(self, document_id: int, user_id: str) -> Optional[Document]:
        """Get document by ID with user access check.

        Args:
            document_id: ID of the document to retrieve
            user_id: ID of the user making the request

        Returns:
            Optional[Document]: Document if found and accessible, None otherwise
        """
        return self.repository.get_by_id(document_id, user_id)

    def _generate_unique_name(self, user_id: str, filename: str) -> str:
        """Generate a unique name for a document.

        Args:
            user_id: ID of the document owner
            filename: Original filename

        Returns:
            str: Generated unique name
        """
        # Remove file extension and non-alphanumeric characters
        base_name = "".join(c for c in filename.split(".")[0] if c.isalnum())
        timestamp = str(int(datetime.now().timestamp()))
        # Remove hyphens from user_id and concatenate all parts
        clean_user_id = "".join(c for c in user_id if c.isalnum())
        return f"{clean_user_id}{timestamp}{base_name}"

    def _validate_unique_name(self, unique_name: str) -> None:
        """Validate unique name format.

        Args:
            unique_name: Unique name to validate

        Raises:
            HTTPException: If validation fails
        """
        if not unique_name.replace("_", "").isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="unique_name must be alphanumeric (underscores allowed)",
            )

    def _prepare_document_response(
        self, document: Document
    ) -> DocumentResponse:
        """Prepare document response from domain model.

        Args:
            document: Document domain model

        Returns:
            DocumentResponse: Response schema
        """
        # Ensure metadata is a dictionary
        if document.doc_metadata is None:
            document.doc_metadata = {}

        # Convert domain model to response schema
        return DocumentResponse.model_validate({
            "id": document.id,
            "user_id": document.user_id,
            "name": document.name,
            "mime_type": document.mime_type,
            "storage_url": document.storage_url,
            "size_bytes": document.size_bytes,
            "status": document.status,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
            "metadata": document.doc_metadata,  # Map doc_metadata to metadata
            "unique_name": document.unique_name,
            "is_public": document.is_public,
        })

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
            # Check file size before reading content
            file_size = 0
            chunk_size = 8192  # Read in 8KB chunks
            chunks = []

            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                file_size += len(chunk)
                chunks.append(chunk)
                if file_size > DocumentData.MAX_DOCUMENT_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size ({file_size} bytes) exceeds maximum allowed size ({DocumentData.MAX_DOCUMENT_SIZE} bytes)"
                    )

            content = b"".join(chunks)

            # Generate unique name for public documents if not provided
            if document.is_public:
                if not document.unique_name:
                    document.unique_name = self._generate_unique_name(user_id, file.filename)
                else:
                    self._validate_unique_name(document.unique_name)

            # Create initial document record
            doc_data = document.to_domain(user_id=user_id)
            db_doc = self.repository.create(
                **doc_data.__dict__
            )

            try:
                # Store file in storage service
                stored_file = await self.storage.store(
                    file_data=content,
                    file_id=str(db_doc.id),
                    user_id=user_id,
                    mime_type=document.mime_type,
                )

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
                return self._prepare_document_response(db_doc)
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
        except HTTPException as e:
            # Re-raise HTTP exceptions directly
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create document: {str(e)}",
            ) from e

    async def get_document(
        self, document_id: int, user_id: str
    ) -> DocumentResponse:
        """Get a document by ID.

        Args:
            document_id: ID of the document to retrieve
            user_id: ID of the user making the request

        Returns:
            DocumentResponse: Retrieved document data

        Raises:
            HTTPException: If document not found or user not authorized
        """
        try:
            document = await self._get_document_for_user(document_id, user_id)
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )
            return self._prepare_document_response(document)
        except HTTPException as e:
            # Re-raise HTTP exceptions directly
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve document: {str(e)}",
            ) from e

    async def get_file_content(self, document_id: int, user_id: str) -> BytesIO:
        """Get document file content.

        Args:
            document_id: ID of the document
            user_id: ID of the user making the request

        Returns:
            BytesIO: Document file content

        Raises:
            HTTPException: If document not found or user not authorized
        """
        try:
            document = await self._get_document_for_user(document_id, user_id)
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            # Get file content from storage
            content = await self.storage.retrieve(
                file_id=str(document_id),
                user_id=user_id
            )
            return content
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get document content: {str(e)}",
            ) from e

    async def get_document_content(
        self, document_id: int, user_id: str
    ) -> BytesIO:
        """Get document file content.

        Args:
            document_id: ID of the document
            user_id: ID of the user making the request

        Returns:
            BytesIO: Document file content

        Raises:
            HTTPException: If document not found or user not authorized
        """
        document = await self._get_document_for_user(document_id, user_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        try:
            # Get file content from storage
            content = await self.storage.retrieve(
                file_id=str(document_id),
                user_id=user_id
            )
            if not isinstance(content, BytesIO):
                content = BytesIO(content)
            content.seek(0)
            return content
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document content not found: {str(e)}",
            ) from e
        except StorageError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get document content: {str(e)}",
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get document content: {str(e)}",
            ) from e

    async def update_document(
        self,
        document_id: int,
        document: DocumentUpdate,
        user_id: str,
    ) -> DocumentResponse:
        """Update a document.

        Args:
            document_id: ID of the document to update
            document: Document update data
            user_id: ID of the user making the request

        Returns:
            DocumentResponse: Updated document data

        Raises:
            HTTPException: If update fails or user not authorized
        """
        try:
            existing_doc = await self._get_document_for_user(document_id, user_id)
            if not existing_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            # Update document with non-None fields
            update_data = {}
            for field, value in document.model_dump(
                exclude_unset=True
            ).items():
                if value is not None:
                    update_data[field] = value

            updated_doc = self.repository.update(
                document_id, update_data
            )
            self.repository.db.commit()
            return self._prepare_document_response(updated_doc)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update document: {str(e)}",
            ) from e

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
        try:
            document = await self._get_document_for_user(document_id, user_id)
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            # Delete from storage first
            try:
                await self.storage.delete(str(document_id), user_id)
            except FileNotFoundError:
                # If file doesn't exist in storage, just log and continue
                pass
            except StorageError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete document from storage: {str(e)}",
                ) from e

            # Then delete from database
            self.repository.delete(document_id, user_id)
            self.repository.db.commit()
        except HTTPException as e:
            # Re-raise HTTP exceptions directly
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document: {str(e)}",
            ) from e

    async def list_documents(
        self,
        user_id: str,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status: Optional[DocumentStatus] = None,
        is_public: Optional[bool] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentResponse]:
        """List documents with optional filtering.

        Args:
            user_id: ID of the user making the request
            skip: Number of records to skip
            limit: Maximum number of records to return
            offset: Alias for skip (backward compatibility)
            status: Filter by document status
            is_public: Filter by public/private status
            filters: Additional filters to apply

        Returns:
            List[DocumentResponse]: List of documents
        """
        try:
            # Handle offset/skip
            if offset is not None and skip is None:
                skip = offset

            # Build filter criteria
            filter_criteria = {}
            if status:
                filter_criteria["status"] = status
            if is_public is not None:
                filter_criteria["is_public"] = is_public
            if filters:
                filter_criteria.update(filters)

            # Get documents from repository
            documents = self.repository.list(
                user_id=user_id,
                skip=skip,
                limit=limit,
                filters=filter_criteria,
            )

            # Convert to response schema
            return [
                self._prepare_document_response(doc)
                for doc in documents
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list documents: {str(e)}",
            ) from e

    async def get_user_storage_usage(self, user_id: str) -> int:
        """Get total storage usage for a user.

        Args:
            user_id: ID of the user

        Returns:
            int: Total storage usage in bytes
        """
        return self.repository.get_total_size_by_user(
            user_id
        )

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
        try:
            document = await self._get_document_for_user(document_id, user_id)
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            updated_doc = self.repository.update_status(
                document_id, new_status
            )
            return self._prepare_document_response(updated_doc)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update document status: {str(e)}",
            ) from e
