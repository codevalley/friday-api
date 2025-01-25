"""Mock storage implementation for testing."""

from datetime import datetime, UTC
from io import BytesIO
from typing import Dict, Optional, Tuple

from domain.storage import (
    IStorageService,
    StoragePermissionError,
    StorageStatus,
    StoredFile,
)


class MockStorageService(IStorageService):
    """Mock storage service for testing.

    This implementation stores files in memory and simulates
    file operations and error conditions.
    """

    def __init__(self):
        """Initialize mock storage."""
        # Dict mapping file keys to (content, metadata) tuples
        self._files: Dict[
            str, Tuple[bytes, StoredFile]
        ] = {}

    def _get_file_key(
        self, user_id: str, file_id: str
    ) -> str:
        """Get the key for a file.

        Args:
            user_id: ID of the user
            file_id: ID of the file

        Returns:
            str: Key for storing the file
        """
        return f"{user_id}/{file_id}"

    def _verify_user_access(
        self,
        user_id: str,
        owner_id: str,
        requesting_owner_id: Optional[str] = None,
    ) -> None:
        """Verify a user has access to a file.

        Args:
            user_id: ID of the requesting user
            owner_id: ID of the file owner
            requesting_owner_id: Optional owner ID being requested

        Raises:
            StoragePermissionError: If user lacks permission
        """
        # If owner_id is provided, user must match either user_id or owner_id
        if requesting_owner_id:
            if (
                user_id != requesting_owner_id
                and user_id != owner_id
            ):
                raise StoragePermissionError(
                    "Not authorized to access this file"
                )
        # Otherwise, user can only access their own files
        elif user_id != owner_id:
            raise StoragePermissionError(
                "Not authorized to access this file"
            )

    def store(
        self,
        file_data: bytes,
        file_id: str,
        user_id: str,
        mime_type: str,
    ) -> StoredFile:
        """Store a file in mock storage.

        Args:
            file_data: File content
            file_id: ID to store file under
            user_id: ID of file owner
            mime_type: MIME type of file

        Returns:
            StoredFile: Metadata about stored file
        """
        key = self._get_file_key(user_id, file_id)

        # Create metadata
        metadata = StoredFile(
            id=file_id,
            user_id=user_id,
            path=f"mock://{key}",
            size_bytes=len(file_data),
            mime_type=mime_type,
            status=StorageStatus.ACTIVE,
            created_at=datetime.now(UTC),
        )

        # Store file and metadata
        self._files[key] = (file_data, metadata)

        return metadata

    def retrieve(
        self,
        file_id: str,
        user_id: str,
        owner_id: Optional[str] = None,
    ) -> BytesIO:
        """Retrieve a file from mock storage.

        Args:
            file_id: ID of file to retrieve
            user_id: ID of requesting user
            owner_id: Optional owner ID

        Returns:
            BytesIO: File content

        Raises:
            FileNotFoundError: If file not found
            StoragePermissionError: If user lacks permission
        """
        key = self._get_file_key(
            owner_id if owner_id else user_id,
            file_id,
        )

        # If file not found in specified location, search all directories
        if key not in self._files:
            for other_key in self._files:
                if other_key.endswith(f"/{file_id}"):
                    metadata = self._files[other_key][1]
                    try:
                        self._verify_user_access(
                            user_id,
                            metadata.user_id,
                            owner_id,
                        )
                        return BytesIO(
                            self._files[other_key][0]
                        )
                    except StoragePermissionError:
                        continue
            raise FileNotFoundError(
                "The specified key does not exist."
            )

        # Get file data and metadata
        file_data, metadata = self._files[key]

        # Verify user has access
        self._verify_user_access(
            user_id,
            metadata.user_id,
            owner_id,
        )

        return BytesIO(file_data)

    def delete(
        self,
        file_id: str,
        user_id: str,
    ) -> None:
        """Delete a file from mock storage.

        Args:
            file_id: ID of file to delete
            user_id: ID of requesting user

        Raises:
            FileNotFoundError: If file not found
            StoragePermissionError: If user lacks permission
        """
        key = self._get_file_key(user_id, file_id)

        # If file not found in user's directory, search all directories
        if key not in self._files:
            for other_key in self._files:
                if other_key.endswith(f"/{file_id}"):
                    metadata = self._files[other_key][1]
                    if metadata.user_id != user_id:
                        raise StoragePermissionError(
                            "Not authorized to delete this file"
                        )
                    del self._files[other_key]
                    return
            raise FileNotFoundError(
                "The specified key does not exist."
            )

        # Delete the file
        del self._files[key]

    def get_metadata(
        self,
        file_id: str,
        user_id: str,
    ) -> StoredFile:
        """Get metadata for a file.

        Args:
            file_id: ID of file
            user_id: ID of requesting user

        Returns:
            StoredFile: File metadata

        Raises:
            FileNotFoundError: If file not found
            StoragePermissionError: If user lacks permission
        """
        key = self._get_file_key(user_id, file_id)

        # If file not found in user's directory, search all directories
        if key not in self._files:
            for other_key in self._files:
                if other_key.endswith(f"/{file_id}"):
                    metadata = self._files[other_key][1]
                    try:
                        self._verify_user_access(
                            user_id,
                            metadata.user_id,
                        )
                        return metadata
                    except StoragePermissionError:
                        continue
            raise FileNotFoundError(
                "The specified key does not exist."
            )

        return self._files[key][1]
