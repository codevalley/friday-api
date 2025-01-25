"""Integration tests for the document management system."""

import pytest
from fastapi import UploadFile, HTTPException, status
from io import BytesIO
from unittest.mock import AsyncMock
from schemas.pydantic.DocumentSchema import (
    DocumentCreate,
    DocumentUpdate,
)
from domain.storage import (
    StoredFile,
    IStorageService,
    StorageStatus,
)
from services.DocumentService import DocumentService
from datetime import datetime


def create_test_file(
    content: bytes = b"test content",
) -> UploadFile:
    """Create a test file for upload."""
    file = BytesIO(content)
    file.seek(0)  # Reset file pointer to beginning

    # Create a custom file-like object that simulates a real file upload
    class FileWithLen(BytesIO):
        def __len__(self):
            return len(content)

    test_file = FileWithLen(content)
    test_file.seek(0)

    return UploadFile(
        filename="test.txt",
        file=test_file,
        headers={"content-type": "text/plain"},
    )


@pytest.fixture
def storage_service():
    """Mock storage service."""
    mock_storage = AsyncMock(spec=IStorageService)
    stored_content = {}

    async def mock_store(
        file_data, file_id, user_id, mime_type
    ):
        stored_content[file_id] = file_data
        return StoredFile(
            id=file_id,
            user_id=user_id,
            path=f"test/{file_id}",
            size_bytes=len(file_data),
            mime_type=mime_type,
            status=StorageStatus.ACTIVE,
            created_at=datetime.now(),
        )

    async def mock_retrieve(
        file_id, user_id, owner_id=None
    ):
        if file_id not in stored_content:
            raise FileNotFoundError(
                f"File {file_id} not found"
            )
        file = BytesIO(stored_content[file_id])
        file.seek(0)  # Reset file pointer to beginning
        return file

    async def mock_delete(file_id, user_id):
        if file_id not in stored_content:
            raise FileNotFoundError(
                f"File {file_id} not found"
            )
        del stored_content[file_id]

    async def mock_get_metadata(file_id, user_id):
        if file_id not in stored_content:
            raise FileNotFoundError(
                f"File {file_id} not found"
            )
        content = stored_content[file_id]
        return StoredFile(
            id=file_id,
            user_id=user_id,
            path=f"test/{file_id}",
            size_bytes=len(content),
            mime_type="text/plain",
            status=StorageStatus.ACTIVE,
            created_at=datetime.now(),
        )

    mock_storage.store = AsyncMock(side_effect=mock_store)
    mock_storage.retrieve = AsyncMock(
        side_effect=mock_retrieve
    )
    mock_storage.delete = AsyncMock(side_effect=mock_delete)
    mock_storage.get_metadata = AsyncMock(
        side_effect=mock_get_metadata
    )
    return mock_storage


@pytest.mark.integration
class TestDocumentIntegration:
    """Integration tests for document management system."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_document(
        self,
        document_service: DocumentService,
        sample_user,
        storage_service: IStorageService,
    ):
        """Test creating and retrieving a document."""
        # Create document
        doc_create = DocumentCreate(
            name="Test Document",
            metadata={"description": "Test Description"},
            is_public=False,
            mime_type="text/plain",
        )
        test_file = create_test_file()

        created_doc = (
            await document_service.create_document(
                document=doc_create,
                user_id=sample_user.id,
                file=test_file,
            )
        )

        # Verify document was created
        assert created_doc.name == "Test Document"
        assert created_doc.user_id == sample_user.id

        # Retrieve document
        retrieved_doc = await document_service.get_document(
            document_id=created_doc.id,
            user_id=sample_user.id,
        )
        assert retrieved_doc.name == created_doc.name
        assert (
            retrieved_doc.doc_metadata
            == created_doc.doc_metadata
        )

        # Verify file content
        file_content = (
            await document_service.get_document_content(
                document_id=created_doc.id,
                user_id=sample_user.id,
            )
        )
        assert file_content.read() == b"test content"

    @pytest.mark.asyncio
    async def test_update_document(
        self,
        document_service: DocumentService,
        sample_user,
        storage_service: IStorageService,
    ):
        """Test updating a document's metadata."""
        # Create initial document
        doc_create = DocumentCreate(
            name="Original Name",
            metadata={
                "description": "Original Description"
            },
            is_public=False,
            mime_type="text/plain",
        )
        test_file = create_test_file()
        created_doc = (
            await document_service.create_document(
                document=doc_create,
                user_id=sample_user.id,
                file=test_file,
            )
        )

        # Update document
        doc_update = DocumentUpdate(
            name="Updated Name",
            metadata={"description": "Updated Description"},
            is_public=True,
        )
        updated_doc = (
            await document_service.update_document(
                document_id=created_doc.id,
                document=doc_update,
                user_id=sample_user.id,
            )
        )

        assert updated_doc.name == "Updated Name"
        assert (
            updated_doc.doc_metadata.get("description")
            == "Updated Description"
        )
        assert updated_doc.is_public is True

        # Verify file content remains unchanged
        file_content = (
            await document_service.get_document_content(
                document_id=created_doc.id,
                user_id=sample_user.id,
            )
        )
        assert file_content.read() == b"test content"

    @pytest.mark.asyncio
    async def test_delete_document(
        self,
        document_service: DocumentService,
        sample_user,
        storage_service: IStorageService,
    ):
        """Test deleting a document."""
        # Create document
        doc_create = DocumentCreate(
            name="To Be Deleted",
            metadata={
                "description": "This document will be deleted"
            },
            is_public=False,
            mime_type="text/plain",
        )
        test_file = create_test_file()
        created_doc = (
            await document_service.create_document(
                document=doc_create,
                user_id=sample_user.id,
                file=test_file,
            )
        )

        # Delete document
        await document_service.delete_document(
            document_id=created_doc.id,
            user_id=sample_user.id,
        )

        # Verify document is deleted
        with pytest.raises(HTTPException) as exc_info:
            await document_service.get_document(
                document_id=created_doc.id,
                user_id=sample_user.id,
            )
        assert (
            exc_info.value.status_code
            == status.HTTP_404_NOT_FOUND
        )

        # Verify file is deleted from storage
        with pytest.raises(HTTPException) as exc_info:
            await document_service.get_document_content(
                document_id=created_doc.id,
                user_id=sample_user.id,
            )
        assert (
            exc_info.value.status_code
            == status.HTTP_404_NOT_FOUND
        )

    @pytest.mark.asyncio
    async def test_public_document_access(
        self,
        document_service: DocumentService,
        sample_user,
        another_user,
        storage_service: IStorageService,
    ):
        """Test public document access."""
        # Create public document
        doc_create = DocumentCreate(
            name="Public Document",
            metadata={
                "description": "This is a public document"
            },
            is_public=True,
            mime_type="text/plain",
        )
        test_file = create_test_file()
        created_doc = (
            await document_service.create_document(
                document=doc_create,
                user_id=sample_user.id,
                file=test_file,
            )
        )

        # Verify another user can access the document
        retrieved_doc = await document_service.get_document(
            document_id=created_doc.id,
            user_id=another_user.id,
        )
        assert retrieved_doc.name == created_doc.name

        # Verify another user can access the file content
        file_content = (
            await document_service.get_document_content(
                document_id=created_doc.id,
                user_id=another_user.id,
            )
        )
        assert file_content.read() == b"test content"

    @pytest.mark.asyncio
    async def test_document_list_and_filter(
        self,
        document_service: DocumentService,
        sample_user,
        storage_service: IStorageService,
    ):
        """Test listing and filtering documents."""
        # Create multiple documents
        doc_names = ["Doc1", "Doc2", "Doc3"]
        for name in doc_names:
            doc_create = DocumentCreate(
                name=name,
                metadata={
                    "description": f"Description for {name}"
                },
                is_public=False,
                mime_type="text/plain",
            )
            test_file = create_test_file(
                content=f"Content for {name}".encode()
            )
            await document_service.create_document(
                document=doc_create,
                user_id=sample_user.id,
                file=test_file,
            )

        # List all documents
        documents = await document_service.list_documents(
            user_id=sample_user.id, skip=0, limit=10
        )
        assert (
            len(documents) >= 3
        )  # May include documents from other tests

        # Test filtering by name
        filtered_docs = (
            await document_service.list_documents(
                user_id=sample_user.id,
                skip=0,
                limit=10,
                filters={"name": "Doc1"},
            )
        )
        assert len(filtered_docs) == 1
        assert filtered_docs[0].name == "Doc1"

    @pytest.mark.asyncio
    async def test_document_size_limits(
        self,
        document_service: DocumentService,
        sample_user,
        storage_service: IStorageService,
    ):
        """Test document size limits."""
        # Test with a valid size document (1MB)
        valid_content = b"x" * (1024 * 1024)  # 1MB
        doc_create = DocumentCreate(
            name="Valid Size Document",
            metadata={
                "description": "This is a valid size document"
            },
            is_public=False,
            mime_type="application/octet-stream",
        )
        test_file = create_test_file(content=valid_content)

        created_doc = (
            await document_service.create_document(
                document=doc_create,
                user_id=sample_user.id,
                file=test_file,
            )
        )

        # Verify file content for valid size
        file_content = (
            await document_service.get_document_content(
                document_id=created_doc.id,
                user_id=sample_user.id,
            )
        )
        assert len(file_content.read()) == len(
            valid_content
        )

        # Test with an oversized document (150MB)
        oversized_content = b"x" * (
            150 * 1024 * 1024
        )  # 150MB
        doc_create = DocumentCreate(
            name="Oversized Document",
            metadata={
                "description": "This document exceeds size limits"
            },
            is_public=False,
            mime_type="application/octet-stream",
        )
        test_file = create_test_file(
            content=oversized_content
        )

        with pytest.raises(HTTPException) as exc_info:
            await document_service.create_document(
                document=doc_create,
                user_id=sample_user.id,
                file=test_file,
            )
        assert (
            exc_info.value.status_code
            == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )
