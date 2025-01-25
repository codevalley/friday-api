"""Mock storage implementation for testing."""

from datetime import datetime, UTC
from io import BytesIO
from typing import Dict, Optional, Tuple

from domain.storage import (
    IStorageService,
    StoragePermissionError,
    StorageStatus,
    StoredFile,
    FileNotFoundError,
)


class MockStorageService(IStorageService):
    """Mock storage service for testing.

    This implementation stores files in memory and simulates
    file operations and error conditions.
    """

    def __init__(self):
        """Initialize mock storage."""
        # Dict mapping file keys to (content, metadata) tuples
        self._files: Dict[str, Tuple[bytes, StoredFile]] = (
            {}
        )

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
        found_file = False
        permission_error = None

        # First try with provided owner_id
        if owner_id:
            key = self._get_file_key(owner_id, file_id)
            if key in self._files:
                found_file = True
                file_data, metadata = self._files[key]
                try:
                    self._verify_user_access(
                        user_id,
                        metadata.user_id,
                        owner_id,
                    )
                    return BytesIO(file_data)
                except StoragePermissionError as e:
                    permission_error = e

        # Then try with user_id
        key = self._get_file_key(user_id, file_id)
        if key in self._files:
            found_file = True
            file_data, metadata = self._files[key]
            try:
                self._verify_user_access(
                    user_id,
                    metadata.user_id,
                )
                return BytesIO(file_data)
            except StoragePermissionError as e:
                permission_error = e

        # Finally search all directories
        for other_key in self._files:
            if other_key.endswith(f"/{file_id}"):
                found_file = True
                file_data, metadata = self._files[other_key]
                try:
                    self._verify_user_access(
                        user_id,
                        metadata.user_id,
                        owner_id,
                    )
                    return BytesIO(file_data)
                except StoragePermissionError as e:
                    permission_error = e

        # If we found a file but had permission errors, raise the last one
        if found_file and permission_error:
            raise permission_error

        raise FileNotFoundError(
            "The specified key does not exist."
        )

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
        found_file = False
        permission_error = None

        # First try user's directory
        key = self._get_file_key(user_id, file_id)
        if key in self._files:
            found_file = True
            metadata = self._files[key][1]
            try:
                self._verify_user_access(
                    user_id,
                    metadata.user_id,
                )
                del self._files[key]
                return
            except StoragePermissionError as e:
                permission_error = e

        # Then search all directories
        for other_key in self._files:
            if other_key.endswith(f"/{file_id}"):
                found_file = True
                metadata = self._files[other_key][1]
                try:
                    self._verify_user_access(
                        user_id,
                        metadata.user_id,
                    )
                    del self._files[other_key]
                    return
                except StoragePermissionError as e:
                    permission_error = e

        # If we found a file but had permission errors, raise the last one
        if found_file and permission_error:
            raise permission_error

        raise FileNotFoundError(
            "The specified key does not exist."
        )

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
        found_file = False
        permission_error = None

        # First try user's directory
        key = self._get_file_key(user_id, file_id)
        if key in self._files:
            found_file = True
            metadata = self._files[key][1]
            try:
                self._verify_user_access(
                    user_id,
                    metadata.user_id,
                )
                return metadata
            except StoragePermissionError as e:
                permission_error = e

        # Then search all directories
        for other_key in self._files:
            if other_key.endswith(f"/{file_id}"):
                found_file = True
                metadata = self._files[other_key][1]
                try:
                    self._verify_user_access(
                        user_id,
                        metadata.user_id,
                    )
                    return metadata
                except StoragePermissionError as e:
                    permission_error = e

        # If we found a file but had permission errors, raise the last one
        if found_file and permission_error:
            raise permission_error

        raise FileNotFoundError(
            "The specified key does not exist."
        )
