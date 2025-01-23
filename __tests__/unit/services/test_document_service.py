"""Test suite for DocumentService."""

from typing import Iterator
from datetime import datetime
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException

from domain.document import DocumentStatus
from domain.storage import (
    StorageError,
    StorageStatus,
    StoredFile,
    IStorageService,
)
from services.DocumentService import DocumentService
from repositories.DocumentRepository import (
    DocumentRepository,
)
from schemas.pydantic.DocumentSchema import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
)


def iter(items) -> Iterator[bytes]:
    """Create an iterator from a list of items."""
    for item in items:
        yield item


@pytest.fixture
def mock_repository(sample_document):
    """Create a mock document repository."""
    mock_repo = Mock(spec=DocumentRepository)
    mock_repo.get_by_id.return_value = sample_document

    # Set up create to return a new document
    mock_repo.create.return_value = sample_document

    # Set up update to return a new document
    mock_repo.update.return_value = sample_document

    # Set up update_status to update and return document
    def mock_update_status(document_id, new_status):
        doc = sample_document
        doc.status = new_status
        return doc

    mock_repo.update_status.side_effect = mock_update_status

    # Set up delete to do nothing
    def mock_delete(document_id):
        return None

    mock_repo.delete.side_effect = mock_delete

    # Set up get_total_size_by_user to return total size
    def mock_get_total_size_by_user(user_id):
        return 2048

    mock_repo.get_total_size_by_user.side_effect = (
        mock_get_total_size_by_user
    )

    # Mock the db attribute
    mock_repo.db = Mock()
    mock_repo.db.commit = Mock()

    return mock_repo


@pytest.fixture
def mock_storage():
    """Create a mock storage service."""
    mock_storage = AsyncMock(spec=IStorageService)
    mock_storage.store = AsyncMock(
        return_value=StoredFile(
            id="test-file-id",
            user_id="test-user-id",
            path="/test/path/file.pdf",
            size_bytes=2048,
            mime_type="application/pdf",
            status=StorageStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    )

    class AsyncIterator:
        def __init__(self, content):
            self.content = content
            self.current = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.current < len(self.content):
                chunk = self.content[self.current]
                self.current += 1
                return chunk
            raise StopAsyncIteration

    async def mock_retrieve(*args, **kwargs):
        return AsyncIterator([b"test content"])

    mock_storage.retrieve = AsyncMock(
        side_effect=mock_retrieve
    )
    mock_storage.get = AsyncMock(
        return_value=b"test content"
    )
    mock_storage.delete = AsyncMock()
    return mock_storage


@pytest.fixture
def document_service(mock_repository, mock_storage):
    """Create a document service with mocked dependencies."""
    return DocumentService(
        db=mock_repository, storage_service=mock_storage
    )


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    mock_doc = Mock()
    mock_doc.id = 1
    mock_doc.name = "test.pdf"
    mock_doc.mime_type = "application/pdf"
    mock_doc.metadata = {}
    mock_doc.unique_name = "test123"
    mock_doc.size_bytes = 100
    mock_doc.status = DocumentStatus.ACTIVE
    mock_doc.created_at = datetime.now()
    mock_doc.updated_at = datetime.now()
    mock_doc.user_id = "test-user"
    mock_doc.is_public = False
    mock_doc.storage_url = "test/path/file.txt"
    return mock_doc


class TestDocumentService:
    """Test cases for DocumentService."""

    def test_create_document(
        self,
        document_service,
        mock_storage,
        mock_repository,
        sample_document,
    ):
        """Test creating a new document."""
        # Setup
        mock_repository.create.return_value = (
            sample_document
        )
        mock_repository.update.return_value = (
            sample_document
        )

        # Create a mock file
        mock_file = AsyncMock()
        mock_file.read = AsyncMock(
            return_value=b"test content"
        )
        mock_file.filename = "test.pdf"

        # Test
        result = document_service.create_document(
            document=DocumentCreate(
                name="test.pdf",
                mime_type="application/pdf",
                metadata={},
                is_public=False,
            ),
            user_id="test-user",
            file=mock_file,
        )

        # Assert
        assert result.id == sample_document.id
        assert result.name == "test.pdf"
        assert result.user_id == "test-user"
        mock_storage.store.assert_called_once()
        mock_repository.create.assert_called_once()
        mock_repository.update.assert_called_once()
        mock_repository.db.commit.assert_called_once()

    def test_create_document_storage_error(
        self,
        document_service,
        mock_storage,
    ):
        """Test handling storage errors during document creation."""
        # Setup
        mock_storage.store.side_effect = StorageError(
            "Failed to store file"
        )

        # Create a mock file
        mock_file = Mock()
        mock_file.read = Mock(return_value=b"test content")
        mock_file.filename = "test.pdf"

        # Test
        with pytest.raises(HTTPException) as exc:
            document_service.create_document(
                document=DocumentCreate(
                    name="test.pdf",
                    mime_type="application/pdf",
                    metadata={},
                    is_public=False,
                ),
                user_id="test-user",
                file=mock_file,
            )
        assert exc.value.status_code == 500

    def test_get_document_not_found(
        self, document_service, mock_repository
    ):
        """Test getting a nonexistent document."""
        # Setup
        mock_repository.get_by_id.return_value = None

        # Test
        with pytest.raises(HTTPException) as exc:
            document_service.get_document(
                document_id=999, user_id="test-user"
            )
        assert exc.value.status_code == 404

    def test_get_document_unauthorized(
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
            document_service.get_document(
                document_id=1, user_id="different-user"
            )
        assert exc.value.status_code == 403

    def test_get_document_content(
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

        # Test
        content = document_service.get_document_content(
            document_id=1, user_id=sample_document.user_id
        )

        # Assert
        assert content == b"test content"
        mock_storage.retrieve.assert_called_once()
        mock_repository.get_by_id.assert_called_once_with(1)

    def test_get_document_content_not_found(
        self,
        document_service,
        mock_repository,
        mock_storage,
        sample_document,
    ):
        """Test handling missing document content."""
        # Setup
        mock_repository.get_by_id.return_value = None

        # Test
        with pytest.raises(HTTPException) as exc:
            document_service.get_document_content(
                document_id=999, user_id="test-user"
            )
        assert exc.value.status_code == 404

    def test_update_document(
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

        # Mock the update to return a document with valid data
        def mock_update(doc_id, update_dict):
            # Create a dictionary with all required fields
            doc_dict = {
                "id": sample_document.id,
                "user_id": sample_document.user_id,
                "name": update_dict.get(
                    "name", sample_document.name
                ),
                "mime_type": sample_document.mime_type,
                "unique_name": sample_document.unique_name,
                "storage_url": sample_document.storage_url,
                "size_bytes": sample_document.size_bytes,
                "status": sample_document.status,
                "created_at": sample_document.created_at,
                "updated_at": sample_document.updated_at,
                "metadata": update_dict.get(
                    "metadata", sample_document.metadata
                ),
                "is_public": update_dict.get(
                    "is_public", sample_document.is_public
                ),
            }
            # Convert the dictionary to a DocumentResponse
            return DocumentResponse.model_validate(doc_dict)

        mock_repository.update.side_effect = mock_update

        # Test
        result = document_service.update_document(
            document_id=1,
            user_id="test-user",
            update_data=update_data,
        )

        # Assert
        assert result.id == sample_document.id
        assert result.metadata == update_data.metadata
        mock_repository.get_by_id.assert_called_once_with(1)
        mock_repository.update.assert_called_once()
        mock_repository.db.commit.assert_called_once()

    def test_update_document_status(
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

        # Test
        result = document_service.update_document_status(
            document_id=1,
            user_id="test-user",
            new_status=new_status,
        )

        # Assert
        assert result.status == new_status
        assert mock_repository.update_status.call_count == 1

    def test_update_document_status_unauthorized(
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
            document_service.update_document_status(
                document_id=1,
                user_id="wrong-user",
                new_status=DocumentStatus.ARCHIVED,
            )
        assert exc.value.status_code == 403

    def test_delete_document(
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
        document_service.delete_document(
            document_id=1,
            user_id="test-user",
        )

        # Assert
        mock_storage.delete.assert_called_once()
        mock_repository.delete.assert_called_once_with(1)

    def test_delete_document_not_found(
        self,
        document_service,
        mock_repository,
    ):
        """Test deleting a nonexistent document."""
        # Setup
        mock_repository.get_by_id.return_value = None

        # Test
        with pytest.raises(HTTPException) as exc:
            document_service.delete_document(
                document_id=999,
                user_id="test-user",
            )
        assert exc.value.status_code == 404

    def test_delete_document_unauthorized(
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
            document_service.delete_document(
                document_id=1,
                user_id="wrong-user",
            )
        assert exc.value.status_code == 403

    def test_get_user_storage_usage(
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

    def test_get_public_document(
        self,
        document_service,
        mock_repository,
        sample_document,
    ):
        """Test getting a public document."""
        # Setup
        sample_document.is_public = True
        mock_repository.get_by_id.return_value = (
            sample_document
        )

        # Test
        result = document_service.get_public_document(
            document_id=1
        )

        # Assert
        assert result.id == sample_document.id
        assert result.is_public is True

    def test_get_public_document_not_found(
        self,
        document_service,
        mock_repository,
    ):
        """Test getting a nonexistent public document."""
        # Setup
        mock_repository.get_by_id.return_value = None

        # Test
        with pytest.raises(HTTPException) as exc:
            document_service.get_public_document(
                document_id=999
            )
        assert exc.value.status_code == 404

    def test_get_private_document_as_public(
        self,
        document_service,
        mock_repository,
        sample_document,
    ):
        """Test attempting to get a private document as public."""
        # Setup
        sample_document.is_public = False
        mock_repository.get_by_id.return_value = (
            sample_document
        )

        # Test
        with pytest.raises(HTTPException) as exc:
            document_service.get_public_document(
                document_id=1
            )
        assert exc.value.status_code == 403

    def test_get_public_document_content(
        self,
        document_service,
        mock_repository,
        mock_storage,
        sample_document,
    ):
        """Test getting public document content."""
        # Setup
        sample_document.is_public = True
        mock_repository.get_by_id.return_value = (
            sample_document
        )

        class AsyncIterator:
            def __init__(self, content):
                self.content = content
                self.current = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.current < len(self.content):
                    chunk = self.content[self.current]
                    self.current += 1
                    return chunk
                raise StopAsyncIteration

        async def mock_retrieve(*args, **kwargs):
            return AsyncIterator([b"test content"])

        mock_storage.retrieve = AsyncMock(
            side_effect=mock_retrieve
        )

        # Test
        (
            result,
            content,
        ) = document_service.get_public_document_content(
            document_id=1
        )

        # Assert
        assert content == b"test content"
        assert result.id == sample_document.id
        assert result.is_public is True
        mock_storage.retrieve.assert_called_once()
        mock_repository.get_by_id.assert_called_once_with(1)

    def test_get_private_document_as_owner(
        self,
        document_service,
        mock_repository,
        mock_storage,
        sample_document,
    ):
        """Test owner accessing their private document."""
        # Setup
        sample_document.is_public = False
        mock_repository.get_by_id.return_value = (
            sample_document
        )

        # Test
        result = document_service.get_document(
            document_id=1, user_id=sample_document.user_id
        )

        # Assert
        assert result.id == sample_document.id
        assert result.user_id == sample_document.user_id

    def test_get_public_document_as_non_owner(
        self,
        document_service,
        mock_repository,
        mock_storage,
        sample_document,
    ):
        """Test non-owner accessing a public document."""
        # Setup
        sample_document.is_public = True
        mock_repository.get_by_id.return_value = (
            sample_document
        )

        # Test
        result = document_service.get_document(
            document_id=1, user_id="different-user"
        )

        # Assert
        assert result.id == sample_document.id
        assert result.is_public is True
