"""Tests for mock storage implementation."""

import pytest
from io import BytesIO

from domain.storage import (
    StoredFile,
    StorageStatus,
    FileNotFoundError,
    StoragePermissionError,
)
from infrastructure.storage.mock_sync import (
    MockStorageService,
)


@pytest.fixture
def storage():
    """Create a mock storage service for testing."""
    return MockStorageService()


def test_store_and_retrieve(storage):
    """Test storing and retrieving a file."""
    test_file = b"test content"
    file_id = "test.txt"
    user_id = "user1"

    # Store file and verify metadata
    stored = storage.store(
        file_data=test_file,
        file_id=file_id,
        user_id=user_id,
        mime_type="text/plain",
    )
    assert isinstance(stored, StoredFile)
    assert stored.id == file_id
    assert stored.user_id == user_id
    assert stored.mime_type == "text/plain"
    assert stored.status == StorageStatus.ACTIVE

    # Retrieve file and verify content
    retrieved = storage.retrieve(
        file_id=file_id,
        user_id=user_id,
    )
    assert isinstance(retrieved, BytesIO)
    assert retrieved.read() == test_file


def test_store_and_delete(storage):
    """Test storing and deleting a file."""
    test_file = b"test content"
    file_id = "test.txt"
    user_id = "user1"

    # Store file and verify metadata
    stored = storage.store(
        file_data=test_file,
        file_id=file_id,
        user_id=user_id,
        mime_type="text/plain",
    )
    assert isinstance(stored, StoredFile)
    assert stored.id == file_id
    assert stored.user_id == user_id

    # Delete file
    storage.delete(file_id=file_id, user_id=user_id)

    # Verify file is deleted
    with pytest.raises(FileNotFoundError):
        storage.retrieve(file_id=file_id, user_id=user_id)


def test_retrieve_nonexistent(storage):
    """Test retrieving a nonexistent file."""
    with pytest.raises(FileNotFoundError):
        storage.retrieve(
            file_id="nonexistent.txt",
            user_id="user1",
        )


def test_unauthorized_access(storage):
    """Test unauthorized access to a file."""
    test_file = b"test content"
    file_id = "test.txt"
    owner_id = "user1"
    other_user = "user2"

    # Store file and verify owner
    stored = storage.store(
        file_data=test_file,
        file_id=file_id,
        user_id=owner_id,
        mime_type="text/plain",
    )
    assert isinstance(stored, StoredFile)
    assert stored.user_id == owner_id

    # Try to access with wrong user
    with pytest.raises(StoragePermissionError):
        storage.retrieve(
            file_id=file_id, user_id=other_user
        )


def test_get_metadata(storage):
    """Test getting file metadata."""
    test_file = b"test content"
    file_id = "test.txt"
    user_id = "user1"
    mime_type = "text/plain"

    # Store file and verify metadata
    stored = storage.store(
        file_data=test_file,
        file_id=file_id,
        user_id=user_id,
        mime_type=mime_type,
    )
    assert isinstance(stored, StoredFile)
    assert stored.mime_type == mime_type
    assert stored.size_bytes == len(test_file)

    # Get metadata and verify
    metadata = storage.get_metadata(
        file_id=file_id,
        user_id=user_id,
    )
    assert metadata.id == file_id
    assert metadata.user_id == user_id
    assert metadata.mime_type == mime_type
    assert metadata.size_bytes == len(test_file)


def test_delete_nonexistent(storage):
    """Test deleting a nonexistent file."""
    with pytest.raises(FileNotFoundError):
        storage.delete(
            file_id="nonexistent.txt",
            user_id="user1",
        )
