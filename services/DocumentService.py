"""Service layer for document operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from io import BytesIO

from domain.document import DocumentData, DocumentStatus
from domain.storage import IStorageService, StorageError
from repositories.DocumentRepository import (
    DocumentRepository,
)
from schemas.pydantic.DocumentSchema import (
    DocumentResponse,
    DocumentUpdate,
)
from schemas.pydantic.StorageSchema import (
    StorageUsageResponse,
)
from orm.DocumentModel import Document as DocumentModel


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

    def _get_document_internal(
        self, document_id: int
    ) -> Optional[DocumentModel]:
        """Get document by ID for internal use.

        Args:
            document_id: ID of the document to retrieve

        Returns:
            Optional[DocumentModel]: Document if found, None otherwise
        """
        return self.repository.get_by_id(document_id)

    def _get_document_for_user(
        self, document_id: int, user_id: str
    ) -> Optional[DocumentModel]:
        """Get document by ID with user access check.

        Args:
            document_id: ID of the document to retrieve
            user_id: ID of the user making the request

        Returns:
            Optional[DocumentModel]: Document if found, None otherwise
        """
        return self.repository.get_by_id(
            document_id, user_id
        )

    def _generate_unique_name(
        self, user_id: str, filename: str
    ) -> str:
        """Generate a unique name for a document.

        Args:
            user_id: ID of the document owner
            filename: Original filename

        Returns:
            str: Generated unique name
        """
        # Remove file extension and non-alphanumeric characters
        base_name = "".join(
            c for c in filename.split(".")[0] if c.isalnum()
        )
        timestamp = str(int(datetime.now().timestamp()))
        # Remove hyphens from user_id and concatenate all parts
        clean_user_id = "".join(
            c for c in user_id if c.isalnum()
        )
        return f"{clean_user_id}{timestamp}{base_name}"

    def _validate_unique_name(
        self, unique_name: str
    ) -> None:
        """Validate unique name format.

        Args:
            unique_name: Unique name to validate

        Raises:
            HTTPException: If validation fails
        """
        # Check if string contains only alphanumeric chars and underscores
        if not all(
            c.isalnum() or c == "_" for c in unique_name
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="unique_name must be alphanumeric (underscore allowed)",
            )

    def _prepare_document_response(
        self, document: DocumentModel
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
        return DocumentResponse.model_validate(
            {
                "id": document.id,
                "user_id": document.user_id,
                "name": document.name,
                "mime_type": document.mime_type,
                "storage_url": document.storage_url,
                "size_bytes": document.size_bytes,
                "status": document.status,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
                "doc_metadata": document.doc_metadata,
                "unique_name": document.unique_name,
                "is_public": document.is_public,
            }
        )

    def create_document(
        self,
        name: str,
        mime_type: str,
        file_content: bytes,
        file_size: int,
        metadata: Optional[Dict[str, Any]] = None,
        is_public: bool = False,
        unique_name: Optional[str] = None,
        user_id: str = None,
    ) -> DocumentResponse:
        """Create a new document.

        Args:
            name: Name of the document
            mime_type: MIME type of the document
            file_content: Content of the document
            file_size: Size of the document in bytes
            metadata: Optional metadata for the document
            is_public: Whether the document is publicly accessible
            unique_name: Optional unique name for public access
            user_id: Optional user ID

        Returns:
            DocumentResponse: Created document

        Raises:
            HTTPException: If file size exceeds the maximum allowed size
        """
        # Validate file size
        max_size = DocumentData.MAX_DOCUMENT_SIZE
        if file_size > max_size:
            msg = (
                "File size exceeds maximum allowed size of "
                f"{max_size} bytes"
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=msg,
            )

        try:
            # Create document in database first
            document = DocumentModel(
                name=name,
                mime_type=mime_type,
                size_bytes=file_size,
                doc_metadata=metadata or {},
                is_public=is_public,
                unique_name=unique_name,
                user_id=user_id,
                status=DocumentStatus.ACTIVE,
                storage_url="",  # Will be updated after storage
            )
            document = self.repository.create(document)

            try:
                # Store file with final document ID
                stored_file = self.storage.store(
                    file_content,
                    str(document.id),
                    user_id,
                    mime_type,
                )

                # Update storage URL
                document.storage_url = stored_file.path
                self.repository.update(
                    document.id,
                    {"storage_url": stored_file.path},
                )
                self.repository.db.commit()
            except StorageError as e:
                # Clean up if storage fails
                self.repository.delete(document.id, user_id)
                self.repository.db.commit()
                msg = "Failed to store document: " + str(e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=msg,
                ) from e

            return self._prepare_document_response(document)
        except Exception as e:
            msg = "Failed to create document: " + str(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=msg,
            ) from e

    def get_document(
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
            document = self._get_document_internal(
                document_id
            )
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            # Check authorization
            if (
                document.user_id != user_id
                and not document.is_public
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this document",
                )

            return self._prepare_document_response(document)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve document: {str(e)}",
            ) from e

    def get_file_content(
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
        try:
            document = self._get_document_for_user(
                document_id, user_id
            )
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            # Get file content from storage
            content = self.storage.retrieve(
                file_id=str(document_id), user_id=user_id
            )
            return content
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get document content: {str(e)}",
            ) from e

    def get_document_content(
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
        document = self._get_document_for_user(
            document_id, user_id
        )
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        try:
            # Get file content from storage
            content = self.storage.retrieve(
                file_id=str(document_id), user_id=user_id
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

    def update_document(
        self,
        document_id: int,
        update_data: DocumentUpdate,
        user_id: str,
    ) -> Optional[DocumentResponse]:
        """Update a document.

        Args:
            document_id: ID of the document to update
            update_data: Updated document data
            user_id: ID of the user making the request

        Returns:
            Optional[DocumentResponse]: Updated document if found,
            None otherwise

        Raises:
            HTTPException: If document not found or update fails
        """
        try:
            # Get document
            document = self._get_document_for_user(
                document_id, user_id
            )
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            # Update document fields
            update_dict = update_data.model_dump(
                exclude_unset=True,
                by_alias=False,  # Don't use aliases when dumping
            )

            # Validate unique_name if provided
            if "unique_name" in update_dict:
                self._validate_unique_name(
                    update_dict["unique_name"]
                )

            # Update the document in the repository
            updated_doc = self.repository.update(
                document_id, update_dict
            )
            if not updated_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            # Commit the transaction
            self.repository.db.commit()

            # Prepare and return response
            return self._prepare_document_response(
                updated_doc
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update document: {str(e)}",
            ) from e

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
        try:
            document = self._get_document_internal(
                document_id
            )
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            # Check authorization
            if document.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to delete this document",
                )

            # Delete from database first
            self.repository.delete(document_id, user_id)
            self.repository.db.commit()

            # Then try to delete from storage
            try:
                self.storage.delete(
                    str(document_id), user_id
                )
            except (FileNotFoundError, StorageError):
                # Log the error but continue since the database record
                # is deleted
                # The file might have been already deleted or will be
                # cleaned up later
                pass

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document: {str(e)}",
            ) from e

    def list_documents(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10,
        name_pattern: Optional[str] = None,
    ) -> List[DocumentResponse]:
        """List documents for a user.

        Args:
            user_id: ID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return
            name_pattern: Optional pattern to filter documents by name

        Returns:
            List[DocumentResponse]: List of documents
        """
        documents = self.repository.list_documents(
            user_id=user_id,
            skip=skip,
            limit=limit,
            name_pattern=name_pattern,
        )
        return [
            self._prepare_document_response(doc)
            for doc in documents
        ]

    def get_storage_usage(
        self,
        user_id: str,
    ) -> StorageUsageResponse:
        """Get storage usage for a user.

        Args:
            user_id: ID of the user

        Returns:
            StorageUsageResponse: Storage usage details
        """
        total_size = self.repository.get_total_size_by_user(
            user_id
        )
        # Set a default storage limit of 1GB
        total_limit = 1024 * 1024 * 1024  # 1GB in bytes
        return StorageUsageResponse(
            used_bytes=total_size, total_bytes=total_limit
        )

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
        try:
            document = self._get_document_internal(
                document_id
            )
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            # Check authorization
            if document.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this document",
                )

            # Update document status
            try:
                updated_doc = self.repository.update_status(
                    document_id=document_id,
                    user_id=user_id,
                    new_status=new_status,
                )
                if not updated_doc:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Document not found",
                    )
                return self._prepare_document_response(
                    updated_doc
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to update document status: {str(e)}",
                ) from e
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update document status: {str(e)}",
            ) from e

    def get_public_document(
        self,
        unique_name: str,
    ) -> DocumentResponse:
        """Get a public document by its unique name.

        Args:
            unique_name: Unique name of the document

        Returns:
            DocumentResponse: Document if found and public

        Raises:
            HTTPException: If document not found or not public
        """
        try:
            # Get document by unique name
            document = self.repository.get_by_unique_name(
                unique_name
            )
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found",
                )

            # Check if document is public
            if not document.is_public:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Document is not public",
                )

            return self._prepare_document_response(document)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get public document: {str(e)}",
            ) from e

    def count_documents(self, user_id: str) -> int:
        """Count total documents for a user.

        Args:
            user_id: ID of the user

        Returns:
            int: Total number of documents
        """
        return self.repository.count_by_user(user_id)
