"""Local filesystem implementation of storage service."""

import os
import aiofiles
import aiofiles.os
from datetime import datetime
from typing import AsyncIterator, Optional

from domain.storage import (
    IStorageService,
    StoredFile,
    StorageStatus,
    StorageError,
    FileNotFoundError,
    StoragePermissionError,
)


class LocalStorageService(IStorageService):
    """Storage service that uses the local filesystem.

    This implementation stores files in a local directory structure,
    organizing them by user ID for isolation.
    """

    def __init__(self, base_path: str):
        """Initialize the local storage service.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = os.path.abspath(base_path)

    def _get_file_path(
        self, user_id: str, file_id: str
    ) -> str:
        """Get the filesystem path for a file.

        Args:
            user_id: ID of the file owner
            file_id: ID of the file

        Returns:
            str: Absolute path where the file should be stored
        """
        # Store files in user-specific directories to prevent conflicts
        return os.path.join(
            self.base_path, user_id, file_id
        )

    async def store(
        self,
        file_data: bytes,
        file_id: str,
        user_id: str,
        mime_type: str,
    ) -> StoredFile:
        """Store a file in the local filesystem.

        Args:
            file_data: Raw file content
            file_id: ID of the file
            user_id: ID of the file owner
            mime_type: MIME type of the file

        Returns:
            StoredFile: Metadata about the stored file

        Raises:
            StorageError: If file storage fails
        """
        path = self._get_file_path(user_id, file_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        try:
            async with aiofiles.open(path, "wb") as f:
                await f.write(file_data)

            return StoredFile(
                id=file_id,
                user_id=user_id,
                path=path,
                size_bytes=len(file_data),
                mime_type=mime_type,
                status=StorageStatus.ACTIVE,
                created_at=datetime.utcnow(),
            )
        except Exception as e:
            raise StorageError(
                f"Failed to store file: {str(e)}"
            ) from e

    async def retrieve(
        self,
        file_id: str,
        user_id: str,
        owner_id: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        """Retrieve a file from the local filesystem.

        Args:
            file_id: ID of the file to retrieve
            user_id: ID of the user requesting the file
            owner_id: Optional ID of the file owner (for public files)

        Returns:
            AsyncIterator[bytes]: File content stream

        Raises:
            FileNotFoundError: If file does not exist
            StoragePermissionError: If user cannot access file
            StorageError: If retrieval fails
        """
        # If owner_id is provided, use that for the path lookup
        lookup_user_id = owner_id if owner_id else user_id
        path = self._get_file_path(lookup_user_id, file_id)

        if not os.path.isfile(path):
            raise FileNotFoundError(
                f"File not found: {file_id}"
            )

        # If owner_id is provided, we're accessing a public file
        # Otherwise, ensure user can only access their own files
        if not owner_id and not path.startswith(
            os.path.join(self.base_path, user_id)
        ):
            raise StoragePermissionError(
                "Not authorized to access this file"
            )

        try:
            async with aiofiles.open(path, "rb") as f:
                while chunk := await f.read(8192):
                    yield chunk
        except Exception as e:
            raise StorageError(
                f"Failed to retrieve file: {str(e)}"
            ) from e

    async def delete(
        self,
        file_id: str,
        user_id: str,
    ) -> None:
        """Delete a file from the local filesystem.

        Args:
            file_id: ID of the file to delete
            user_id: ID of the user requesting deletion

        Raises:
            FileNotFoundError: If file does not exist
            StoragePermissionError: If user cannot delete file
            StorageError: If deletion fails
        """
        path = self._get_file_path(user_id, file_id)

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"File not found: {file_id}"
            )

        # Ensure user can only delete their own files
        if not path.startswith(
            os.path.join(self.base_path, user_id)
        ):
            raise StoragePermissionError(
                "Not authorized to delete this file"
            )

        try:
            await aiofiles.os.remove(path)

            # Try to remove empty parent directories
            parent_dir = os.path.dirname(path)
            try:
                while (
                    parent_dir.startswith(
                        os.path.join(
                            self.base_path, user_id
                        )
                    )
                    and len(os.listdir(parent_dir)) == 0
                ):
                    os.rmdir(parent_dir)
                    parent_dir = os.path.dirname(parent_dir)
            except OSError:
                # Ignore errors while cleaning up empty directories
                pass
        except Exception as e:
            raise StorageError(
                f"Failed to delete file: {str(e)}"
            ) from e

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
            StorageError: If metadata retrieval fails
        """
        path = self._get_file_path(user_id, file_id)

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"File not found: {file_id}"
            )

        # Ensure user can only access their own files
        if not path.startswith(
            os.path.join(self.base_path, user_id)
        ):
            raise StoragePermissionError(
                "Not authorized to access this file"
            )

        try:
            stats = os.stat(path)
            return StoredFile(
                id=file_id,
                user_id=user_id,
                path=path,
                size_bytes=stats.st_size,
                mime_type="application/octet-stream",  # Default MIME type
                status=StorageStatus.ACTIVE,
                created_at=datetime.fromtimestamp(
                    stats.st_ctime
                ),
                updated_at=datetime.fromtimestamp(
                    stats.st_mtime
                ),
            )
        except Exception as e:
            raise StorageError(
                f"Failed to get file metadata: {str(e)}"
            ) from e
