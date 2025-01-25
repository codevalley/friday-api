"""Mock storage service for testing."""

from datetime import datetime
from typing import Dict, Optional, Tuple
from io import BytesIO

from domain.storage import (
    IStorageService,
    StoredFile,
    StorageStatus,
    FileNotFoundError,
    StoragePermissionError,
)


class MockStorageService(IStorageService):
    """In-memory storage service for testing.

    This implementation stores files in memory and provides
    methods to simulate various error conditions.
    """

    def __init__(self):
        """Initialize the mock storage service."""
        self._files: Dict[
            Tuple[str, str], Tuple[bytes, StoredFile]
        ] = {}
        self._should_fail = False
        self._fail_for_user: Optional[str] = None

    def set_should_fail(self, should_fail: bool) -> None:
        """Set whether operations should fail.

        Args:
            should_fail: If True, all operations will fail
        """
        self._should_fail = should_fail

    def set_fail_for_user(
        self, user_id: Optional[str]
    ) -> None:
        """Set a specific user to fail for.

        Args:
            user_id: User ID to fail for, or None to clear
        """
        self._fail_for_user = user_id

    def _check_failure(self, user_id: str) -> None:
        """Check if operation should fail.

        Args:
            user_id: ID of the user performing the operation

        Raises:
            StorageError: If operation should fail
        """
        if (
            self._should_fail
            or user_id == self._fail_for_user
        ):
            raise StoragePermissionError(
                "Simulated failure"
            )

    def store(
        self,
        file_data: bytes,
        file_id: str,
        user_id: str,
        mime_type: str,
    ) -> StoredFile:
        """Store a file in memory.

        Args:
            file_data: Raw file content
            file_id: ID of the file
            user_id: ID of the file owner
            mime_type: MIME type of the file

        Returns:
            StoredFile: Metadata about the stored file

        Raises:
            StorageError: If storage fails
        """
        self._check_failure(user_id)

        stored_file = StoredFile(
            id=file_id,
            user_id=user_id,
            path=f"mock://{user_id}/{file_id}",
            size_bytes=len(file_data),
            mime_type=mime_type,
            status=StorageStatus.ACTIVE,
            created_at=datetime.utcnow(),
        )
        self._files[(user_id, file_id)] = (
            file_data,
            stored_file,
        )
        return stored_file

    def retrieve(
        self,
        file_id: str,
        user_id: str,
        owner_id: Optional[str] = None,
    ) -> BytesIO:
        """Retrieve a file from memory.

        Args:
            file_id: ID of the file to retrieve
            user_id: ID of the user requesting the file
            owner_id: Optional ID of the file owner (for public files)

        Returns:
            BytesIO: File-like object containing file content

        Raises:
            FileNotFoundError: If file does not exist
            StoragePermissionError: If user lacks permission
        """
        self._check_failure(user_id)

        # For public files, use owner_id as key if provided
        lookup_user = owner_id if owner_id else user_id
        key = (lookup_user, file_id)

        if key not in self._files:
            raise FileNotFoundError(
                f"File {file_id} not found"
            )

        file_data, stored_file = self._files[key]

        # Check if user has permission
        if user_id != stored_file.user_id and not owner_id:
            raise StoragePermissionError(
                "User does not have permission to access file"
            )

        return BytesIO(file_data)

    def delete(
        self,
        file_id: str,
        user_id: str,
    ) -> None:
        """Delete a file from memory.

        Args:
            file_id: ID of the file to delete
            user_id: ID of the file owner

        Raises:
            FileNotFoundError: If file does not exist
            StoragePermissionError: If user lacks permission
        """
        self._check_failure(user_id)

        key = (user_id, file_id)
        if key not in self._files:
            raise FileNotFoundError(
                f"File {file_id} not found"
            )

        _, stored_file = self._files[key]

        # Check if user has permission
        if user_id != stored_file.user_id:
            raise StoragePermissionError(
                "User does not have permission to delete file"
            )

        del self._files[key]

    def get_metadata(
        self,
        file_id: str,
        user_id: str,
    ) -> StoredFile:
        """Get metadata about a stored file.

        Args:
            file_id: ID of the file
            user_id: ID of the user requesting metadata

        Returns:
            StoredFile: File metadata

        Raises:
            FileNotFoundError: If file does not exist
            StoragePermissionError: If user cannot access file
        """
        self._check_failure(user_id)

        key = (user_id, file_id)
        if key not in self._files:
            raise FileNotFoundError(
                f"File {file_id} not found"
            )

        _, stored_file = self._files[key]
        return stored_file
