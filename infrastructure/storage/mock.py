"""Mock storage service for testing."""

from datetime import datetime
from typing import AsyncIterator, Dict, Optional, Tuple

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

    async def store(
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

    async def retrieve(
        self,
        file_id: str,
        user_id: str,
        owner_id: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        """Retrieve a file from memory.

        Args:
            file_id: ID of the file to retrieve
            user_id: ID of the user requesting the file
            owner_id: Optional ID of the file owner (for public files)

        Returns:
            AsyncIterator[bytes]: File content stream

        Raises:
            FileNotFoundError: If file does not exist
            StoragePermissionError: If user cannot access file
        """
        self._check_failure(user_id)

        # If owner_id is provided, use that for lookup
        lookup_user_id = owner_id if owner_id else user_id
        key = (lookup_user_id, file_id)

        if key not in self._files:
            raise FileNotFoundError(
                f"File not found: {file_id}"
            )

        file_data, _ = self._files[key]
        yield file_data

    async def delete(
        self,
        file_id: str,
        user_id: str,
    ) -> None:
        """Delete a file from memory.

        Args:
            file_id: ID of the file to delete
            user_id: ID of the user requesting deletion

        Raises:
            FileNotFoundError: If file does not exist
            StoragePermissionError: If user cannot delete file
        """
        self._check_failure(user_id)

        key = (user_id, file_id)
        if key not in self._files:
            raise FileNotFoundError(
                f"File not found: {file_id}"
            )

        del self._files[key]

    async def get_metadata(
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
                f"File not found: {file_id}"
            )

        _, stored_file = self._files[key]
        return stored_file
