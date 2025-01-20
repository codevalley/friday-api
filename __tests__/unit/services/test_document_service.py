"""Test suite for DocumentService."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone, UTC
from fastapi import HTTPException, UploadFile
from typing import AsyncIterator
from fastapi import status

from domain.document import DocumentStatus
from domain.storage import (
    StorageError,
    StorageStatus,
    StoredFile,
    IStorageService,
    FileNotFoundError,
)
from services.DocumentService import DocumentService
from repositories.DocumentRepository import (
    DocumentRepository,
)
from schemas.pydantic.DocumentSchema import (
    DocumentCreate,
    DocumentUpdate,
)


async def async_iter(items) -> AsyncIterator[bytes]:
    """Create an async iterator from a list of items."""
    for item in items:
        yield item


@pytest.fixture
def mock_repository():
    """Create mock document repository."""
    mock_doc = Mock()
    mock_doc.id = 1
    mock_doc.name = "test.pdf"
    mock_doc.storage_url = "/test/path/test.pdf"
    mock_doc.mime_type = "application/pdf"
    mock_doc.size_bytes = 2048
    mock_doc.status = DocumentStatus.PENDING
    mock_doc.metadata = (
        {}
    )  # Fix: Ensure metadata is a valid dict
    mock_doc.user_id = "test-user"
    mock_doc.created_at = datetime.now(UTC)
    mock_doc.updated_at = datetime.now(UTC)
    mock_doc.unique_name = "testdoc"
    mock_doc.is_public = True

    mock_repo = Mock(spec=DocumentRepository)
    mock_repo.db = Mock()
    mock_repo.db.commit = Mock()
    mock_repo.get_by_id.return_value = mock_doc
    mock_repo.get_by_user.return_value = mock_doc
    mock_repo.create.return_value = mock_doc
    mock_repo.update_status.return_value = mock_doc
    return mock_repo


@pytest.fixture
def mock_storage():
    """Create mock storage service."""
    storage = AsyncMock(spec=IStorageService)

    async def mock_retrieve(*args, **kwargs):
        yield b"test content"

    # Fix: Set the mock's side effect to the async generator function
    storage.retrieve = mock_retrieve
    return storage


@pytest.fixture
def document_service(mock_repository, mock_storage):
    """Create document service instance."""
    service = DocumentService(
        db=mock_repository.db,
        storage=mock_storage,
    )
    service.repository = mock_repository  # Replace the auto-created repository
    return service


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    doc = Mock()
    doc.id = 1
    doc.name = "test.pdf"
    doc.storage_url = "/test/path/test.pdf"
    doc.mime_type = "application/pdf"
    doc.size_bytes = 2048
    doc.status = DocumentStatus.PENDING
    doc.metadata = (
        {}
    )  # Fix: Use metadata instead of doc_metadata
    doc.user_id = "test-user"
    doc.created_at = datetime.now(UTC)
    doc.updated_at = datetime.now(UTC)
    doc.unique_name = "testdoc"
    doc.is_public = True
    return doc


@pytest.fixture
def sample_stored_file():
    """Create a sample stored file for testing."""
    return StoredFile(
        id="test-file-id",
        user_id="test-user-id",
        path="/test/path/file.pdf",
        size_bytes=2048,
        mime_type="application/pdf",
        status=StorageStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestDocumentService:
    """Test cases for DocumentService."""

    @pytest.mark.asyncio
    async def test_create_document(
        self,
        document_service,
        mock_storage,
        mock_repository,
        sample_stored_file,
        sample_document,
    ):
        """Test creating a new document."""
        # Setup
        document = DocumentCreate(
            name="test.pdf",
            mime_type="application/pdf",
            metadata={},  # Ensure metadata is a valid dict
        )
        file = Mock(spec=UploadFile)
        file.read = AsyncMock(return_value=b"test content")
        mock_storage.store.return_value = sample_stored_file
        mock_repository.create.return_value = (
            mock_repository.get_by_id.return_value
        )

        # Test
        result = await document_service.create_document(
            document=document,
            user_id="test-user",
            file=file,
        )

        # Assert
        assert result.id == 1
        assert result.name == "test.pdf"
        assert (
            result.metadata == {}
        )  # Verify metadata is a dict
        mock_storage.store.assert_called_once()
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_document_storage_error(
        self,
        document_service,
        mock_storage,
    ):
        """Test handling storage errors during document creation."""
        # Setup
        document = DocumentCreate(
            name="test.pdf",
            mime_type="application/pdf",
            metadata={},
        )
        file = Mock(spec=UploadFile)
        file.read = AsyncMock(return_value=b"test content")
        mock_storage.store.side_effect = StorageError(
            "Failed to store file"
        )

        # Test
        with pytest.raises(HTTPException) as exc:
            await document_service.create_document(
                document=document,
                user_id="test-user",
                file=file,
            )
        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_document_not_found(
        self, document_service, mock_repository
    ):
        """Test getting a nonexistent document."""
        # Setup
        mock_repository.get_by_id.return_value = None

        # Test
        with pytest.raises(HTTPException) as exc:
            await document_service.get_document(
                document_id=999,
                user_id="test-user",
            )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_document_unauthorized(
        self,
        document_service,
        mock_repository,
        sample_document,
    ):
        """Test getting a document without authorization."""
        # Setup
        mock_repository.get_by_id.return_value = (
            sample_document
        )

        # Test
        with pytest.raises(HTTPException) as exc:
            await document_service.get_document(
                document_id=1,
                user_id="wrong-user",
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_document_content(
        self,
        document_service,
        mock_repository,
        mock_storage,
        sample_document,
    ):
        """Test retrieving document content."""
        # Setup
        mock_repository.get_by_id.return_value = (
            sample_document
        )

        async def mock_retrieve(*args, **kwargs):
            yield b"test content"

        mock_storage.retrieve = mock_retrieve

        # Test
        content = (
            await document_service.get_document_content(
                document_id=1,
                user_id="test-user",
            )
        )

        assert content == b"test content"

    @pytest.mark.asyncio
    async def test_get_document_content_not_found(
        self,
        document_service,
        mock_repository,
        mock_storage,
        sample_document,
    ):
        """Test handling missing document content."""
        # Setup
        mock_repository.get_by_id.return_value = (
            sample_document
        )

        async def mock_retrieve_error(*args, **kwargs):
            raise FileNotFoundError(
                "File not found"
            )  # Using domain.storage.FileNotFoundError
            yield b""  # Never reached but needed for async generator syntax

        mock_storage.retrieve = mock_retrieve_error

        # Test
        with pytest.raises(HTTPException) as exc:
            await document_service.get_document_content(
                document_id=1,
                user_id="test-user",
            )
        assert (
            exc.value.status_code
            == status.HTTP_404_NOT_FOUND
        )
        assert (
            exc.value.detail == "Document content not found"
        )

    @pytest.mark.asyncio
    async def test_update_document(
        self,
        document_service,
        mock_repository,
        sample_document,
    ):
        """Test updating document metadata."""
        # Setup
        mock_repository.get_by_id.return_value = (
            sample_document
        )
        update_data = DocumentUpdate(
            metadata={"key": "value"}
        )

        # Test
        result = await document_service.update_document(
            document_id=1,
            user_id="test-user",
            update_data=update_data,
        )

        # Assert
        assert result.id == sample_document.id
        assert result.metadata == update_data.metadata
        mock_repository.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document_status(
        self,
        document_service,
        mock_repository,
        sample_document,
    ):
        """Test updating document status."""
        # Setup
        mock_repository.get_by_id.return_value = (
            sample_document
        )
        new_status = DocumentStatus.ARCHIVED

        # Fix: Update the mock document's status when update_status is called
        def update_status(document_id, new_status):
            doc = sample_document
            doc.status = new_status
            return doc

        mock_repository.update_status.side_effect = (
            update_status
        )

        # Test
        result = (
            await document_service.update_document_status(
                document_id=1,
                user_id="test-user",
                new_status=new_status,
            )
        )

        # Assert
        assert result.status == new_status
        assert mock_repository.update_status.call_count == 1

    @pytest.mark.asyncio
    async def test_update_document_status_unauthorized(
        self,
        document_service,
        mock_repository,
        sample_document,
    ):
        """Test updating status without authorization."""
        # Setup
        mock_repository.get_by_id.return_value = (
            sample_document
        )

        # Test
        with pytest.raises(HTTPException) as exc:
            await document_service.update_document_status(
                document_id=1,
                user_id="wrong-user",
                new_status=DocumentStatus.ARCHIVED,
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_document(
        self,
        document_service,
        mock_repository,
        mock_storage,
        sample_document,
    ):
        """Test deleting a document."""
        # Setup
        mock_repository.get_by_id.return_value = (
            sample_document
        )

        # Test
        await document_service.delete_document(
            document_id=1,
            user_id="test-user",
        )

        # Assert
        mock_storage.delete.assert_called_once()
        mock_repository.delete.assert_called_once_with(
            sample_document
        )

    @pytest.mark.asyncio
    async def test_delete_document_not_found(
        self,
        document_service,
        mock_repository,
    ):
        """Test deleting a nonexistent document."""
        # Setup
        mock_repository.get_by_id.return_value = None

        # Test
        with pytest.raises(HTTPException) as exc:
            await document_service.delete_document(
                document_id=999,
                user_id="test-user",
            )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_document_unauthorized(
        self,
        document_service,
        mock_repository,
        sample_document,
    ):
        """Test deleting a document without authorization."""
        # Setup
        mock_repository.get_by_id.return_value = (
            sample_document
        )

        # Test
        with pytest.raises(HTTPException) as exc:
            await document_service.delete_document(
                document_id=1,
                user_id="wrong-user",
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_user_storage_usage(
        self,
        document_service,
        mock_repository,
    ):
        """Test getting user's storage usage."""
        # Setup
        mock_repository.get_total_size_by_user.return_value = (
            2048
        )

        # Test
        usage = document_service.get_user_storage_usage(
            user_id="test-user"
        )

        # Assert
        assert usage == 2048
        mock_repository.get_total_size_by_user.assert_called_once_with(
            "test-user"
        )
