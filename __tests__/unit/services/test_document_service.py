"""Test suite for DocumentService."""

from typing import Iterator
from datetime import datetime
import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from io import BytesIO

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
    DocumentUpdate,
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
    def mock_update_status(
        document_id, new_status, user_id
    ):
        doc = sample_document
        doc.status = new_status
        return doc

    mock_repo.update_status.side_effect = mock_update_status

    # Set up delete to do nothing
    def mock_delete(document_id, user_id):
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
    mock_storage = Mock(spec=IStorageService)
    stored_file = StoredFile(
        id="test-file-id",
        user_id="test-user-id",
        path="/test/path/file.pdf",
        size_bytes=2048,
        mime_type="application/pdf",
        status=StorageStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_storage.store = Mock(return_value=stored_file)
    mock_storage.retrieve.return_value = BytesIO(
        b"test content"
    )
    mock_storage.delete.return_value = None
    return mock_storage


@pytest.fixture
def document_service(mock_repository, mock_storage):
    """Create a document service with mocked dependencies."""
    return DocumentService(
        repository=mock_repository, storage=mock_storage
    )


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    doc = Mock()
    doc.id = 1
    doc.user_id = "test-user"
    doc.name = "test.pdf"
    doc.mime_type = "application/pdf"
    doc.storage_url = "/test/path/file.pdf"
    doc.size_bytes = 2048
    doc.status = DocumentStatus.ACTIVE
    doc.created_at = datetime.now()
    doc.updated_at = datetime.now()
    doc.doc_metadata = {}  # Empty dict for metadata
    doc.unique_name = (
        "test_doc"  # Using underscore instead of hyphen
    )
    doc.is_public = False
    return doc


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

        # Test
        result = document_service.create_document(
            name="test.pdf",
            mime_type="application/pdf",
            file_content=b"test content",
            file_size=len(b"test content"),
            metadata={},
            is_public=False,
            user_id="test-user",
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

        # Test
        with pytest.raises(HTTPException) as exc:
            document_service.create_document(
                name="test.pdf",
                mime_type="application/pdf",
                file_content=b"test content",
                file_size=len(b"test content"),
                metadata={},
                is_public=False,
                user_id="test-user",
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
        assert content.read() == b"test content"

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
            doc_metadata={"key": "value"}
        )

        # Mock the update to return updated sample document
        updated_doc = sample_document
        updated_doc.doc_metadata = {"key": "value"}
        mock_repository.update.return_value = updated_doc

        # Test
        result = document_service.update_document(
            document_id=1,
            user_id="test-user",
            update_data=update_data,
        )

        # Assert
        assert result.id == sample_document.id
        assert (
            result.doc_metadata == update_data.doc_metadata
        )
        mock_repository.get_by_id.assert_called_once_with(
            1, "test-user"
        )
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
        mock_repository.delete.assert_called_once_with(
            1, "test-user"
        )

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

    def test_get_storage_usage(
        self,
        document_service,
        mock_repository,
    ):
        """Test getting user's storage usage."""
        # Setup
        expected_size = 2048
        mock_repository.get_total_size_by_user.return_value = (
            expected_size
        )

        # Test
        usage = document_service.get_storage_usage(
            user_id="test-user"
        )

        # Assert
        assert usage.used_bytes == expected_size
        assert (
            usage.total_bytes == 1024 * 1024 * 1024
        )  # 1GB
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
        sample_document.unique_name = "test_doc123"
        mock_repository.get_by_unique_name.return_value = (
            sample_document
        )

        # Test
        result = document_service.get_public_document(
            unique_name="test_doc123"
        )

        # Assert
        assert result.id == sample_document.id
        assert result.is_public is True
        mock_repository.get_by_unique_name.assert_called_once_with(
            "test_doc123"
        )

    def test_get_public_document_not_found(
        self,
        document_service,
        mock_repository,
    ):
        """Test getting a nonexistent public document."""
        # Setup
        mock_repository.get_by_unique_name.return_value = (
            None
        )

        # Test
        with pytest.raises(HTTPException) as exc:
            document_service.get_public_document(
                unique_name="nonexistent"
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
        sample_document.unique_name = "test-doc"
        mock_repository.get_by_unique_name.return_value = (
            sample_document
        )

        # Test
        with pytest.raises(HTTPException) as exc:
            document_service.get_public_document(
                unique_name="test-doc"
            )
        assert exc.value.status_code == 403

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

    def test_count_documents(
        self,
        document_service,
        mock_repository,
    ):
        """Test counting documents for a user."""
        # Setup
        mock_repository.count_by_user.return_value = 5
        user_id = "test-user"

        # Test
        result = document_service.count_documents(user_id)

        # Assert
        assert result == 5
        mock_repository.count_by_user.assert_called_once_with(
            user_id
        )

    def test_validate_unique_name_valid(
        self,
        document_service,
    ):
        """Test validating a valid unique name."""
        # Test with valid names
        document_service._validate_unique_name("test_doc")
        document_service._validate_unique_name("test123")
        document_service._validate_unique_name("a_b_c_123")

    def test_validate_unique_name_invalid(
        self,
        document_service,
    ):
        """Test validating invalid unique names."""
        invalid_names = [
            "test-doc",  # Contains hyphen
            "test doc",  # Contains space
            "test@doc",  # Contains special char
            "test/doc",  # Contains slash
        ]

        for name in invalid_names:
            with pytest.raises(HTTPException) as exc:
                document_service._validate_unique_name(name)
            assert exc.value.status_code == 400
            assert (
                "unique_name must contain only letters, numbers, and underscores"  # noqa: E501
                == exc.value.detail
            )
