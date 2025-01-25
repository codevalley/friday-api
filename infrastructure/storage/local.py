"""Local filesystem implementation of storage service."""

import os
from datetime import datetime
from io import BytesIO
from typing import Optional
import json

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

    def _get_metadata_path(
        self, user_id: str, file_id: str
    ) -> str:
        """Get the filesystem path for a file's metadata.

        Args:
            user_id: ID of the file owner
            file_id: ID of the file

        Returns:
            str: Absolute path where the file's metadata should be stored
        """
        # Store metadata in a separate file
        return (
            f"{self._get_file_path(user_id, file_id)}.meta"
        )

    def _verify_user_access(
        self,
        path: str,
        user_id: str,
        owner_id: Optional[str] = None,
    ) -> None:
        """Verify a user has access to a file path.

        Args:
            path: Path to verify
            user_id: ID of the user requesting access
            owner_id: Optional ID of the file owner (for public files)

        Raises:
            StoragePermissionError: If user cannot access the path
        """
        # If owner_id is provided, user must be the owner
        if owner_id and user_id != owner_id:
            raise StoragePermissionError(
                "Not authorized to access this file"
            )
        # Otherwise, ensure user can only access their own files
        elif not owner_id and not path.startswith(
            os.path.join(self.base_path, user_id)
        ):
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

        try:
            os.makedirs(
                os.path.dirname(path), exist_ok=True
            )

            with open(path, "wb") as f:
                f.write(file_data)

            # Store metadata in a separate file
            meta_path = self._get_metadata_path(
                user_id, file_id
            )
            metadata = {
                "mime_type": mime_type,
                "owner_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
            }
            with open(meta_path, "w") as f:
                json.dump(metadata, f)

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

    def retrieve(
        self,
        file_id: str,
        user_id: str,
        owner_id: Optional[str] = None,
    ) -> BytesIO:
        """Retrieve a file from the local filesystem.

        Args:
            file_id: ID of the file to retrieve
            user_id: ID of the user requesting the file
            owner_id: Optional ID of the file owner (for public files)

        Returns:
            BytesIO: File-like object containing file content

        Raises:
            FileNotFoundError: If file does not exist
            StoragePermissionError: If user cannot access file
            StorageError: If retrieval fails
        """
        # If owner_id is provided, use that for the path lookup
        lookup_user_id = owner_id if owner_id else user_id

        # Try to find the file's metadata in owner's directory
        metadata_path = self._get_metadata_path(
            lookup_user_id, file_id
        )
        actual_owner_id = None

        # If metadata not found in user's directory, search all directories
        if not os.path.isfile(metadata_path):
            for dir_name in os.listdir(self.base_path):
                other_metadata_path = os.path.join(
                    self.base_path,
                    dir_name,
                    f"{file_id}.meta",
                )
                if os.path.isfile(other_metadata_path):
                    with open(
                        other_metadata_path, "r"
                    ) as f:
                        metadata = json.load(f)
                        if "owner_id" in metadata:
                            actual_owner_id = metadata[
                                "owner_id"
                            ]
                            metadata_path = (
                                other_metadata_path
                            )
                            break

        # If we found metadata, check permissions
        if os.path.isfile(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                if "owner_id" in metadata:
                    actual_owner_id = metadata["owner_id"]
                    if (
                        user_id != actual_owner_id
                        and not owner_id
                    ):
                        raise StoragePermissionError(
                            "Not authorized to access this file"
                        )
                    path = self._get_file_path(
                        actual_owner_id, file_id
                    )
                    if os.path.isfile(path):
                        try:
                            # Read file in chunks to handle large files
                            buffer = BytesIO()
                            with open(path, "rb") as f:
                                while chunk := f.read(8192):
                                    buffer.write(chunk)
                            buffer.seek(0)
                            return buffer
                        except Exception as e:
                            raise StorageError(
                                f"Failed to retrieve file: {str(e)}"
                            ) from e
        raise FileNotFoundError(
            f"File not found: {file_id}"
        )

    def delete(
        self,
        file_id: str,
        user_id: str,
    ) -> None:
        """Delete a file and its metadata.

        Args:
            file_id: ID of file to delete
            user_id: ID of requesting user

        Raises:
            FileNotFoundError: If file not found
            StoragePermissionError: If user lacks permission
            StorageError: If deletion fails
        """
        # First find the metadata to determine the owner
        metadata = self.get_metadata(file_id, user_id)
        if not metadata:
            raise FileNotFoundError(
                f"File not found: {file_id}"
            )

        # Get the actual file path using the owner's ID
        path = self._get_file_path(
            metadata.user_id, file_id
        )
        meta_path = self._get_metadata_path(
            metadata.user_id, file_id
        )

        # Check permissions using the owner ID from metadata
        self._verify_user_access(
            path, user_id, metadata.user_id
        )

        try:
            # Delete the file
            os.remove(path)

            # Remove metadata file if it exists
            if os.path.exists(meta_path):
                os.remove(meta_path)

            # Try to remove empty parent directories
            parent_dir = os.path.dirname(path)
            try:
                while (
                    parent_dir.startswith(
                        os.path.join(
                            self.base_path, metadata.user_id
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
            StorageError: If metadata retrieval fails
        """
        # Search through all user directories
        for dir_name in os.listdir(self.base_path):
            dir_path = os.path.join(
                self.base_path, dir_name
            )
            if not os.path.isdir(dir_path):
                continue

            path = self._get_file_path(dir_name, file_id)
            if not os.path.exists(path):
                continue

            # Found the file, now check permissions
            self._verify_user_access(
                path, user_id, dir_name
            )

            try:
                stat = os.stat(path)

                # Read MIME type from metadata file
                meta_path = self._get_metadata_path(
                    dir_name, file_id
                )
                mime_type = (
                    "application/octet-stream"  # Default
                )
                if os.path.exists(meta_path):
                    with open(meta_path, "r") as f:
                        metadata = json.load(f)
                        mime_type = metadata.get(
                            "mime_type", mime_type
                        )

                return StoredFile(
                    id=file_id,
                    user_id=dir_name,  # Use actual owner's ID
                    path=path,
                    size_bytes=stat.st_size,
                    mime_type=mime_type,
                    status=StorageStatus.ACTIVE,
                    created_at=datetime.fromtimestamp(
                        stat.st_ctime
                    ),
                    updated_at=datetime.fromtimestamp(
                        stat.st_mtime
                    ),
                )
            except Exception as e:
                raise StorageError(
                    f"Failed to get metadata: {str(e)}"
                ) from e

        raise FileNotFoundError(
            f"File not found: {file_id}"
        )
