"""Test DocumentRepository class."""

import pytest
from unittest.mock import Mock
from datetime import datetime, timezone

from domain.document import DocumentStatus
from repositories.DocumentRepository import (
    DocumentRepository,
)
from orm.DocumentModel import Document


@pytest.fixture
def document_repository(test_db_session):
    """Create DocumentRepository instance with test database session."""
    return DocumentRepository(db=test_db_session)


@pytest.fixture
def mock_document():
    """Create a mock document for testing."""
    doc = Mock(spec=Document)
    doc.id = 1
    doc.name = "Test Document"
    doc.storage_url = "/test/path/document.pdf"
    doc.mime_type = "application/pdf"
    doc.size_bytes = 1024
    doc.user_id = "test-user"
    doc.status = DocumentStatus.ACTIVE
    doc.is_public = False
    doc.unique_name = None
    doc.created_at = datetime.now(timezone.utc)
    doc.updated_at = None
    return doc


class TestDocumentRepository:
    """Test suite for DocumentRepository."""

    def test_create_document(
        self, document_repository, sample_user
    ):
        """Test creating a document."""
        doc = document_repository.create(
            name="test.pdf",
            storage_url="/test/path/test.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            user_id=sample_user.id,
        )

        assert doc.id is not None
        assert doc.name == "test.pdf"
        assert doc.storage_url == "/test/path/test.pdf"
        assert doc.mime_type == "application/pdf"
        assert doc.size_bytes == 1024
        assert doc.user_id == sample_user.id
        assert doc.status == DocumentStatus.PENDING
        assert doc.is_public is False
        assert doc.unique_name is None
        assert doc.created_at is not None
        assert doc.updated_at is not None

    def test_create_public_document(
        self, document_repository, sample_user
    ):
        """Test creating a public document with unique name."""
        doc = document_repository.create(
            name="public.pdf",
            storage_url="/public/path/public.pdf",
            mime_type="application/pdf",
            size_bytes=2048,
            user_id=sample_user.id,
            is_public=True,
            unique_name="test-doc",
        )

        assert doc.id is not None
        assert doc.name == "public.pdf"
        assert doc.is_public is True
        assert doc.unique_name == "test-doc"
        assert doc.status == DocumentStatus.PENDING

    def test_get_document_by_id(
        self, document_repository, mock_document, mock_db
    ):
        """Test retrieving a document by ID."""
        # Setup mock
        document_repository.db = mock_db
        query = mock_db.query.return_value
        query.filter.return_value.first.return_value = (
            mock_document
        )

        # Test
        doc = document_repository.get(mock_document.id)

        assert doc is not None
        assert doc.id == mock_document.id
        assert doc.name == mock_document.name
        assert doc.storage_url == mock_document.storage_url

    def test_get_document_by_user(
        self, document_repository, mock_document, mock_db
    ):
        """Test retrieving a document by user ID."""
        # Setup mock
        document_repository.db = mock_db
        document_repository.get_by_owner = (
            lambda id, user_id: mock_document
        )

        # Test
        doc = document_repository.get_by_user(
            mock_document.id, mock_document.user_id
        )

        assert doc is not None
        assert doc.id == mock_document.id
        assert doc.user_id == mock_document.user_id

    def test_list_documents(
        self, document_repository, sample_user
    ):
        """Test listing documents for a user."""
        # Create test documents
        for i in range(3):
            document_repository.create(
                name=f"doc{i}.pdf",
                storage_url=f"/test/path/doc{i}.pdf",
                mime_type="application/pdf",
                size_bytes=1024,
                user_id=sample_user.id,
            )

        # Get documents
        docs = document_repository.list_documents(
            user_id=sample_user.id,
            skip=0,
            limit=10,
        )

        assert len(docs) == 3
        assert all(
            isinstance(doc, Document) for doc in docs
        )
        assert all(
            doc.user_id == sample_user.id for doc in docs
        )

    def test_update_document_status(
        self, document_repository, mock_document, mock_db
    ):
        """Test updating document status."""
        # Setup mock
        document_repository.db = mock_db
        query = mock_db.query.return_value
        filter_result = query.filter.return_value
        filter_result.filter.return_value.first.return_value = (
            mock_document
        )

        # Test
        updated = document_repository.update_status(
            mock_document.id,
            mock_document.user_id,
            DocumentStatus.ACTIVE,
        )

        assert updated is not None
        assert updated.status == DocumentStatus.ACTIVE
        assert updated.updated_at is not None

    def test_get_by_unique_name(
        self, document_repository, mock_document, mock_db
    ):
        """Test retrieving a public document by unique name."""
        # Setup mock
        document_repository.db = mock_db
        mock_document.is_public = True
        mock_document.unique_name = "test-doc"
        query = mock_db.query.return_value
        query.filter.return_value.first.return_value = (
            mock_document
        )

        # Test
        doc = document_repository.get_by_unique_name(
            "test-doc"
        )

        assert doc is not None
        assert doc.unique_name == "test-doc"
        assert doc.is_public is True

    def test_delete_document(
        self, document_repository, mock_document, mock_db
    ):
        """Test deleting a document."""
        # Setup mock
        document_repository.db = mock_db
        document_repository.get_by_owner = (
            lambda id, user_id: mock_document
        )

        # Test
        result = document_repository.delete(
            mock_document.id, mock_document.user_id
        )

        assert result is True
        mock_db.delete.assert_called_once_with(
            mock_document
        )
        mock_db.commit.assert_called_once()

    def test_get_nonexistent_document(
        self, document_repository, mock_db
    ):
        """Test retrieving a nonexistent document."""
        # Setup mock
        query = mock_db.query.return_value
        query.filter.return_value.first.return_value = None

        # Test
        doc = document_repository.get(999)
        assert doc is None

    def test_update_nonexistent_document(
        self, document_repository, mock_db
    ):
        """Test updating status of a nonexistent document."""
        # Setup mock
        query = mock_db.query.return_value
        filter_result = query.filter.return_value
        filter_result.filter.return_value.first.return_value = (
            None
        )

        # Test
        updated = document_repository.update_status(
            999,
            "test-user",
            DocumentStatus.ACTIVE,
        )
        assert updated is None

    def test_user_isolation(
        self, document_repository, mock_document, mock_db
    ):
        """Test that users can't access each other's documents."""
        # Setup mock
        query = mock_db.query.return_value
        filter_result = query.filter.return_value
        filter_result.filter.return_value.first.return_value = (
            None
        )

        # Test
        doc = document_repository.get_by_user(
            mock_document.id, "wrong-user-id"
        )
        assert doc is None

        # List documents for another user
        docs = document_repository.list_documents(
            user_id="wrong-user-id",
            skip=0,
            limit=10,
        )
        assert len(docs) == 0
