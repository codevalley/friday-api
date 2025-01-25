"""Unit tests for local storage service."""

import os
import pytest
import tempfile
import shutil
from datetime import datetime

from domain.storage import (
    StorageStatus,
    StorageError,
    FileNotFoundError,
    StoragePermissionError,
)
from infrastructure.storage.local_sync import (
    LocalStorageService,
)


@pytest.fixture
def storage_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def storage_service(storage_dir):
    """Create a LocalStorageService instance for testing."""
    return LocalStorageService(storage_dir)


def test_store_and_retrieve(storage_service):
    """Test storing and retrieving a file."""
    # Test data
    file_data = b"Hello, World!"
    file_id = "test123"
    user_id = "user456"
    mime_type = "text/plain"

    # Store file
    stored = storage_service.store(
        file_data=file_data,
        file_id=file_id,
        user_id=user_id,
        mime_type=mime_type,
    )

    # Verify stored file metadata
    assert stored.id == file_id
    assert stored.user_id == user_id
    assert stored.mime_type == mime_type
    assert stored.size_bytes == len(file_data)
    assert stored.status == StorageStatus.ACTIVE
    assert isinstance(stored.created_at, datetime)

    # Retrieve and verify content
    retrieved = storage_service.retrieve(
        file_id=file_id,
        user_id=user_id,
    )
    assert retrieved.read() == file_data


def test_store_large_file(storage_service):
    """Test storing and retrieving a large file."""
    # Create 1MB of test data
    file_data = b"x" * (1024 * 1024)
    file_id = "large123"
    user_id = "user456"
    mime_type = "application/octet-stream"

    # Store file
    stored = storage_service.store(
        file_data=file_data,
        file_id=file_id,
        user_id=user_id,
        mime_type=mime_type,
    )

    # Verify size
    assert stored.size_bytes == len(file_data)

    # Retrieve and verify in chunks
    retrieved = storage_service.retrieve(
        file_id=file_id,
        user_id=user_id,
    )

    # Read in chunks and verify
    chunks = []
    while chunk := retrieved.read(8192):
        chunks.append(chunk)
    assert b"".join(chunks) == file_data


def test_delete_file(storage_service):
    """Test deleting a file."""
    # Store a file first
    file_data = b"Delete me"
    file_id = "delete123"
    user_id = "user456"

    storage_service.store(
        file_data=file_data,
        file_id=file_id,
        user_id=user_id,
        mime_type="text/plain",
    )

    # Delete the file
    storage_service.delete(
        file_id=file_id,
        user_id=user_id,
    )

    # Verify file is gone
    with pytest.raises(FileNotFoundError):
        storage_service.retrieve(
            file_id=file_id,
            user_id=user_id,
        )


def test_get_metadata(storage_service):
    """Test getting file metadata."""
    # Store a file first
    file_data = b"Test data"
    file_id = "meta123"
    user_id = "user456"
    mime_type = "text/plain"

    stored = storage_service.store(
        file_data=file_data,
        file_id=file_id,
        user_id=user_id,
        mime_type=mime_type,
    )

    # Get and verify metadata
    metadata = storage_service.get_metadata(
        file_id=file_id,
        user_id=user_id,
    )

    assert metadata.id == stored.id
    assert metadata.user_id == stored.user_id
    assert metadata.size_bytes == stored.size_bytes
    assert metadata.mime_type == stored.mime_type
    assert metadata.status == stored.status
    assert isinstance(metadata.created_at, datetime)


def test_file_not_found(storage_service):
    """Test handling of non-existent files."""
    with pytest.raises(FileNotFoundError):
        storage_service.retrieve(
            file_id="nonexistent",
            user_id="user123",
        )


def test_permission_error(storage_service):
    """Test permission checks."""
    # Store a file as one user
    file_data = b"Secret data"
    file_id = "secret123"
    owner_id = "owner123"
    other_user_id = "other456"

    storage_service.store(
        file_data=file_data,
        file_id=file_id,
        user_id=owner_id,
        mime_type="text/plain",
    )

    # Try to access as another user
    with pytest.raises(StoragePermissionError):
        storage_service.retrieve(
            file_id=file_id,
            user_id=other_user_id,
        )

    # Try to delete as another user
    with pytest.raises(StoragePermissionError):
        storage_service.delete(
            file_id=file_id,
            user_id=other_user_id,
        )


def test_storage_error_handling(
    storage_service, storage_dir
):
    """Test error handling for storage operations."""
    # Create user directory first
    user_dir = os.path.join(storage_dir, "user456")
    os.makedirs(user_dir, exist_ok=True)

    # Make user directory read-only
    os.chmod(user_dir, 0o444)

    try:
        with pytest.raises(StorageError):
            storage_service.store(
                file_data=b"test",
                file_id="test123",
                user_id="user456",
                mime_type="text/plain",
            )
    finally:
        # Restore permissions for cleanup
        os.chmod(user_dir, 0o755)


def test_public_file_access(storage_service):
    """Test accessing a file using owner_id (public file case)."""
    file_data = b"Public data"
    file_id = "public123"
    owner_id = "owner123"
    other_user_id = "other456"

    # Store as owner
    storage_service.store(
        file_data=file_data,
        file_id=file_id,
        user_id=owner_id,
        mime_type="text/plain",
    )

    # Access as other user with owner_id
    retrieved = storage_service.retrieve(
        file_id=file_id,
        user_id=other_user_id,
        owner_id=owner_id,
    )
    assert retrieved.read() == file_data
