"""Integration tests for the document management system."""

import pytest
from fastapi import UploadFile, HTTPException, status
from io import BytesIO
from unittest.mock import Mock
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
    mock_storage = Mock(spec=IStorageService)
    stored_content = {}

    def mock_store(file_data, file_id, user_id, mime_type):
        stored_content[file_id] = file_data
        return StoredFile(
            path=f"/test/{file_id}",
            size_bytes=len(file_data),
            mime_type=mime_type,
            status=StorageStatus.ACTIVE,
        )

    def mock_retrieve(file_id, user_id):
        if file_id not in stored_content:
            raise FileNotFoundError(
                f"File {file_id} not found"
            )
        content = stored_content[file_id]
        return BytesIO(content)

    def mock_delete(file_id, user_id):
        if file_id not in stored_content:
            raise FileNotFoundError(
                f"File {file_id} not found"
            )
        del stored_content[file_id]

    mock_storage.store = mock_store
    mock_storage.retrieve = mock_retrieve
    mock_storage.delete = mock_delete

    return mock_storage


@pytest.mark.integration
class TestDocumentIntegration:
    """Integration tests for document management system."""

    def test_create_and_retrieve_document(
        self,
        document_service: DocumentService,
        sample_user,
        storage_service: IStorageService,
    ):
        """Test creating and retrieving a document."""
        # Create document
        test_file = create_test_file()
        doc_create = DocumentCreate(
            name="Test Doc",
            mime_type="text/plain",
            metadata={"test": "data"},
            is_public=False,
        )

        created_doc = document_service.create_document(
            doc_create, sample_user.id, test_file
        )

        assert created_doc.name == "Test Doc"
        assert created_doc.mime_type == "text/plain"
        assert created_doc.metadata == {"test": "data"}
        assert created_doc.status == DocumentStatus.ACTIVE

        # Retrieve document
        retrieved_doc = document_service.get_document(
            created_doc.id, sample_user.id
        )
        assert retrieved_doc.id == created_doc.id
        assert retrieved_doc.name == created_doc.name

        # Get file content
        content = document_service.get_file_content(
            created_doc.id, sample_user.id
        )
        assert content.read() == b"test content"

    def test_update_document(
        self,
        document_service: DocumentService,
        sample_user,
        storage_service: IStorageService,
    ):
        """Test updating a document's metadata."""
        # Create document
        test_file = create_test_file()
        doc_create = DocumentCreate(
            name="Original Name",
            mime_type="text/plain",
            metadata={"original": "data"},
            is_public=False,
        )

        created_doc = document_service.create_document(
            doc_create, sample_user.id, test_file
        )

        # Update document
        doc_update = DocumentUpdate(
            name="Updated Name",
            metadata={"updated": "data"},
        )

        updated_doc = document_service.update_document(
            created_doc.id, doc_update, sample_user.id
        )

        assert updated_doc.name == "Updated Name"
        assert updated_doc.metadata == {"updated": "data"}

    def test_delete_document(
        self,
        document_service: DocumentService,
        sample_user,
        storage_service: IStorageService,
    ):
        """Test deleting a document."""
        # Create document
        test_file = create_test_file()
        doc_create = DocumentCreate(
            name="To Delete",
            mime_type="text/plain",
            is_public=False,
        )

        created_doc = document_service.create_document(
            doc_create, sample_user.id, test_file
        )

        # Delete document
        document_service.delete_document(
            created_doc.id, sample_user.id
        )

        # Verify document is deleted
        with pytest.raises(HTTPException) as exc:
            document_service.get_document(
                created_doc.id, sample_user.id
            )
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    def test_public_document_access(
        self,
        document_service: DocumentService,
        sample_user,
        another_user,
        storage_service: IStorageService,
    ):
        """Test public document access."""
        # Create public document
        test_file = create_test_file()
        doc_create = DocumentCreate(
            name="Public Doc",
            mime_type="text/plain",
            is_public=True,
            unique_name="public-doc-1",
        )

        created_doc = document_service.create_document(
            doc_create, sample_user.id, test_file
        )

        # Other user can access public document
        retrieved_doc = document_service.get_document(
            created_doc.id, another_user.id
        )
        assert retrieved_doc.id == created_doc.id
        assert retrieved_doc.is_public is True

    def test_document_list_and_filter(
        self,
        document_service: DocumentService,
        sample_user,
        storage_service: IStorageService,
    ):
        """Test listing and filtering documents."""
        # Create multiple documents
        for i in range(3):
            test_file = create_test_file()
            doc_create = DocumentCreate(
                name=f"Doc {i}",
                mime_type="text/plain",
                is_public=False,
            )
            document_service.create_document(
                doc_create, sample_user.id, test_file
            )

        # List all documents
        docs = document_service.list_documents(
            sample_user.id, skip=0, limit=10
        )
        assert len(docs) >= 3

        # Filter by mime type
        docs = document_service.list_documents(
            sample_user.id,
            skip=0,
            limit=10,
            mime_type="text/plain",
        )
        assert all(doc.mime_type == "text/plain" for doc in docs)

    def test_document_size_limits(
        self,
        document_service: DocumentService,
        sample_user,
        storage_service: IStorageService,
    ):
        """Test document size limits."""
        # Create large file
        large_content = b"x" * (DocumentData.MAX_DOCUMENT_SIZE + 1)
        large_file = create_test_file(large_content)

        # Attempt to create document with large file
        doc_create = DocumentCreate(
            name="Large Doc",
            mime_type="text/plain",
            is_public=False,
        )

        with pytest.raises(HTTPException) as exc:
            document_service.create_document(
                doc_create, sample_user.id, large_file
            )
        assert (
            exc.value.status_code
            == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )
