"""Integration tests for the document management system."""

import pytest
from fastapi import UploadFile, HTTPException, status
from io import BytesIO
from unittest.mock import MagicMock
from schemas.pydantic.DocumentSchema import DocumentUpdate
from domain.storage import (
    IStorageService,
    StoredFile,
    StorageStatus,
)
from infrastructure.storage.mock_sync import (
    MockStorageService,
)
from domain.document import DocumentStatus, DocumentData
from services.DocumentService import DocumentService
from orm.UserModel import User
from uuid import uuid4
from sqlalchemy.orm import Session
from typing import Generator, Optional
from datetime import datetime, UTC


def create_test_file(
    content: bytes = b"test content",
) -> UploadFile:
    """Create a test file for upload."""

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
def storage_service() -> IStorageService:
    """Create a mock storage service."""
    mock_service = MockStorageService()

    # Store the actual content that was passed in
    stored_content = {}

    def mock_store(
        file_data: bytes,
        file_id: str,
        user_id: str,
        mime_type: str,
    ) -> StoredFile:
        stored_content[file_id] = file_data
        return StoredFile(
            id=file_id,
            user_id=user_id,
            path=f"/test/{file_id}",
            size_bytes=len(file_data),
            mime_type=mime_type,
            status=StorageStatus.ACTIVE,
            created_at=datetime.now(UTC),
        )

    def mock_retrieve(
        file_id: str,
        user_id: str,
        owner_id: Optional[str] = None,
    ) -> BytesIO:
        """Mock retrieve implementation."""
        content = stored_content.get(
            file_id, b"test content"
        )
        return BytesIO(content)

    # Initialize storage
    stored_content = {}

    # Set up mock methods
    store = MagicMock(side_effect=mock_store)
    retrieve = MagicMock(side_effect=mock_retrieve)

    mock_service.store = store
    mock_service.retrieve = retrieve
    return mock_service


@pytest.fixture
def test_user(
    test_db_session: Session,
) -> Generator[User, None, None]:
    """Create a test user."""
    user = User(
        username="test_user",
        key_id=str(uuid4()),
        user_secret="test_secret",
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    yield user
    test_db_session.delete(user)
    test_db_session.commit()


@pytest.fixture
def another_user(
    test_db_session: Session,
) -> Generator[User, None, None]:
    """Create another test user."""
    user = User(
        username="another_user",
        key_id=str(uuid4()),
        user_secret="test_secret",
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    yield user
    test_db_session.delete(user)
    test_db_session.commit()


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
        file_content = test_file.file.read()
        file_size = len(file_content)
        test_file.file.seek(0)

        created_doc = document_service.create_document(
            name="Test Doc",
            mime_type="text/plain",
            file_content=file_content,
            file_size=file_size,
            metadata={"test": "data"},
            is_public=False,
            user_id=sample_user.id,
        )

        assert created_doc.name == "Test Doc"
        assert created_doc.mime_type == "text/plain"
        assert created_doc.doc_metadata == {"test": "data"}
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
        file_content = test_file.file.read()
        file_size = len(file_content)
        test_file.file.seek(0)

        created_doc = document_service.create_document(
            name="Original Name",
            mime_type="text/plain",
            file_content=file_content,
            file_size=file_size,
            metadata={"original": "data"},
            is_public=False,
            user_id=sample_user.id,
        )

        # Update document
        doc_update = DocumentUpdate(
            name="Updated Name",
            doc_metadata={"updated": "data"},
        )

        updated_doc = document_service.update_document(
            created_doc.id, doc_update, sample_user.id
        )

        assert updated_doc.name == "Updated Name"
        assert updated_doc.doc_metadata == {
            "updated": "data"
        }

    def test_delete_document(
        self,
        document_service: DocumentService,
        sample_user,
        storage_service: IStorageService,
    ):
        """Test deleting a document."""
        # Create document
        test_file = create_test_file()
        file_content = test_file.file.read()
        file_size = len(file_content)
        test_file.file.seek(0)

        created_doc = document_service.create_document(
            name="To Delete",
            mime_type="text/plain",
            file_content=file_content,
            file_size=file_size,
            is_public=False,
            user_id=sample_user.id,
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
        assert (
            exc.value.status_code
            == status.HTTP_404_NOT_FOUND
        )

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
        file_content = test_file.file.read()
        file_size = len(file_content)
        test_file.file.seek(0)

        created_doc = document_service.create_document(
            name="Public Doc",
            mime_type="text/plain",
            file_content=file_content,
            file_size=file_size,
            is_public=True,
            unique_name="public_doc_1",
            user_id=sample_user.id,
        )

        # Other user can access public document
        retrieved_doc = document_service.get_document(
            created_doc.id, another_user.id
        )
        assert retrieved_doc.id == created_doc.id
        assert retrieved_doc.name == created_doc.name
        assert retrieved_doc.is_public is True

        # Get file content as other user
        content = document_service.get_file_content(
            created_doc.id, another_user.id
        )
        assert content.read() == b"test content"

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
            file_content = test_file.file.read()
            file_size = len(file_content)
            test_file.file.seek(0)

            document_service.create_document(
                name=f"Doc {i}",
                mime_type="text/plain",
                file_content=file_content,
                file_size=file_size,
                is_public=False,
                user_id=sample_user.id,
            )

        # List all documents
        docs = document_service.list_documents(
            user_id=sample_user.id,
            skip=0,
            limit=10,
        )
        assert len(docs) >= 3

        # Filter by name
        filtered_docs = document_service.list_documents(
            user_id=sample_user.id,
            skip=0,
            limit=10,
            name_pattern="Doc 1",
        )
        assert len(filtered_docs) == 1
        assert filtered_docs[0].name == "Doc 1"

    def test_document_size_limits(
        self,
        document_service: DocumentService,
        sample_user,
        storage_service: IStorageService,
    ):
        """Test document size limits."""
        # Create large file
        large_content = b"x" * (
            DocumentData.MAX_DOCUMENT_SIZE + 1
        )
        large_file = create_test_file(large_content)
        file_content = large_file.file.read()
        file_size = len(file_content)
        large_file.file.seek(0)

        # Attempt to create document with large file
        with pytest.raises(HTTPException) as exc:
            document_service.create_document(
                name="Large Doc",
                mime_type="text/plain",
                file_content=file_content,
                file_size=file_size,
                is_public=False,
                user_id=sample_user.id,
            )
        assert (
            exc.value.status_code
            == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )

    def test_get_document_content(
        self,
        document_service: DocumentService,
        sample_user,
        storage_service: IStorageService,
    ):
        """Test getting document content."""
        # Create test document
        content = b"test content"
        test_file = create_test_file(content)
        doc = document_service.create_document(
            name=test_file.filename,
            mime_type="text/plain",
            file_content=content,
            file_size=len(content),
            user_id=sample_user.id,
        )

        # Get document content
        result = document_service.get_document_content(
            document_id=doc.id,
            user_id=sample_user.id,
        )
        assert result.getvalue() == content

    def test_get_document_content_not_found(
        self,
        document_service: DocumentService,
        sample_user,
    ):
        """Test getting content of non-existent document."""
        with pytest.raises(HTTPException) as exc_info:
            document_service.get_document_content(
                document_id=999,
                user_id=sample_user.id,
            )
        assert (
            exc_info.value.status_code
            == status.HTTP_404_NOT_FOUND
        )

    def test_get_document_content_unauthorized(
        self,
        document_service: DocumentService,
        sample_user,
        another_user,
        storage_service: IStorageService,
    ):
        """Test getting document content without authorization."""
        # Create document for sample_user
        content = b"Test document content"
        test_file = create_test_file(content)
        doc = document_service.create_document(
            name=test_file.filename,
            mime_type="text/plain",
            file_content=content,
            file_size=len(content),
            user_id=sample_user.id,
        )

        # Try to get document content as another_user
        with pytest.raises(HTTPException) as exc_info:
            document_service.get_document_content(
                document_id=doc.id,
                user_id=another_user.id,
            )
        assert (
            exc_info.value.status_code
            == status.HTTP_403_FORBIDDEN
        )

    def test_get_public_document_content(
        self,
        document_service: DocumentService,
        sample_user,
        another_user,
        storage_service: IStorageService,
    ):
        """Test getting content of a public document."""
        # Create public document
        content = b"Public document content"
        test_file = create_test_file(content=content)
        file_content = (
            test_file.file.read()
        )  # Read the actual file content
        test_file.file.seek(
            0
        )  # Reset file pointer for future reads

        doc = document_service.create_document(
            name=test_file.filename,
            mime_type="text/plain",
            file_content=file_content,  # Use the actual file content
            file_size=len(file_content),
            user_id=sample_user.id,
            is_public=True,
            unique_name="public_test",
        )

        # Get document content as another_user
        result = document_service.get_document_content(
            document_id=doc.id,
            user_id=another_user.id,
            owner_id=sample_user.id,  # Pass the owner_id for public documents
        )
        assert (
            result.getvalue() == file_content
        )  # Compare with the actual file content
