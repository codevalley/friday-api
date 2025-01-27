"""Local storage service implementation."""

import os
import json
from datetime import datetime
from typing import BinaryIO, Optional
from io import BytesIO

from domain.storage import (
    StorageStatus,
    StorageError,
    FileNotFoundError,
    StoragePermissionError,
    StoredFile,
)


class LocalStorageService:
    """Local storage service implementation."""

    def __init__(self, base_dir: str):
        """Initialize local storage service.

        Args:
            base_dir: Base directory for storing files
        """
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _get_file_path(
        self, file_id: str, user_id: str
    ) -> str:
        """Get the full path for a file.

        Args:
            file_id: File ID
            user_id: User ID

        Returns:
            Full path to the file
        """
        return os.path.join(self.base_dir, user_id, file_id)

    def _get_metadata_path(
        self, file_id: str, user_id: str
    ) -> str:
        """Get the full path for a file's metadata.

        Args:
            file_id: File ID
            user_id: User ID

        Returns:
            Full path to the metadata file
        """
        return os.path.join(
            self.base_dir, user_id, f"{file_id}.meta"
        )

    def _check_permission(
        self,
        file_id: str,
        user_id: str,
        owner_id: Optional[str] = None,
    ) -> str:
        """Check if user has permission to access file.

        Args:
            file_id: File ID
            user_id: User ID attempting access
            owner_id: Optional owner ID for public files

        Returns:
            The ID of the file owner

        Raises:
            FileNotFoundError: If file doesn't exist
            StoragePermissionError: If user doesn't have permission
        """
        try:
            # Get the directory containing the file (user_id)
            file_owner = next(
                d
                for d in os.listdir(self.base_dir)
                if os.path.exists(
                    os.path.join(self.base_dir, d, file_id)
                )
            )
        except (StopIteration, FileNotFoundError):
            raise FileNotFoundError(
                f"File {file_id} not found"
            )

        # Allow access if:
        # 1. User is the file owner OR
        # 2. There's an owner_id specified (public document)
        if user_id != file_owner and owner_id is None:
            raise StoragePermissionError(
                "Not authorized to access this document"
            )

        return file_owner

    def store(
        self,
        file_data: bytes,
        file_id: str,
        user_id: str,
        mime_type: str,
    ) -> StoredFile:
        """Store a file.

        Args:
            file_data: File content as bytes
            file_id: File ID
            user_id: User ID
            mime_type: MIME type of the file

        Returns:
            StoredFile object with metadata

        Raises:
            StorageError: If file cannot be stored
        """
        file_path = self._get_file_path(file_id, user_id)
        metadata_path = self._get_metadata_path(
            file_id, user_id
        )
        os.makedirs(
            os.path.dirname(file_path), exist_ok=True
        )

        try:
            with open(file_path, "wb") as f:
                f.write(file_data)

            # Store metadata
            metadata = {
                "mime_type": mime_type,
                "created_at": datetime.utcnow().isoformat(),
            }
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)

        except OSError as e:
            raise StorageError(
                f"Failed to store file: {str(e)}"
            )

        return StoredFile(
            id=file_id,
            user_id=user_id,
            path=file_path,
            size_bytes=len(file_data),
            mime_type=mime_type,
            status=StorageStatus.ACTIVE,
            created_at=datetime.utcnow(),
        )

    def retrieve(
        self,
        file_id: str,
        user_id: str,
        owner_id: Optional[str] = None,
    ) -> BinaryIO:
        """Retrieve a file.

        Args:
            file_id: File ID
            user_id: User ID
            owner_id: Optional owner ID for public files

        Returns:
            File-like object containing the file data

        Raises:
            FileNotFoundError: If file doesn't exist
            StoragePermissionError: If user doesn't have permission
            StorageError: If file cannot be retrieved
        """
        # Check permissions and get file owner
        file_owner = self._check_permission(
            file_id, user_id, owner_id
        )

        try:
            # Use the owner's directory to get the file
            file_path = self._get_file_path(
                file_id, file_owner
            )

            # Read file content and return as BytesIO
            with open(file_path, "rb") as f:
                content = f.read()
            return BytesIO(content)
        except OSError as e:
            raise StorageError(
                f"Failed to retrieve file: {str(e)}"
            )

    def delete(
        self,
        file_id: str,
        user_id: str,
        owner_id: Optional[str] = None,
    ) -> dict:
        """Delete a file.

        Args:
            file_id: File ID
            user_id: User ID
            owner_id: Optional owner ID for public files

        Returns:
            dict: Success response

        Raises:
            FileNotFoundError: If file doesn't exist
            StoragePermissionError: If user doesn't have permission
            StorageError: If file cannot be deleted
        """
        self._check_permission(file_id, user_id, owner_id)
        try:
            file_owner = next(
                d
                for d in os.listdir(self.base_dir)
                if os.path.exists(
                    os.path.join(self.base_dir, d, file_id)
                )
            )
            file_path = self._get_file_path(
                file_id, file_owner
            )
            metadata_path = self._get_metadata_path(
                file_id, file_owner
            )

            # Delete both file and metadata
            os.remove(file_path)
            if os.path.exists(metadata_path):
                os.remove(metadata_path)

            # Remove user directory if empty
            user_dir = os.path.dirname(file_path)
            if not os.listdir(user_dir):
                os.rmdir(user_dir)

            return {
                "status": "success",
                "message": "File deleted successfully",
            }

        except OSError as e:
            raise StorageError(
                f"Failed to delete file: {str(e)}"
            )

    def get_metadata(
        self,
        file_id: str,
        user_id: str,
        owner_id: Optional[str] = None,
    ) -> StoredFile:
        """Get file metadata.

        Args:
            file_id: File ID
            user_id: User ID
            owner_id: Optional owner ID for public files

        Returns:
            StoredFile object with metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            StoragePermissionError: If user doesn't have permission
            StorageError: If metadata cannot be retrieved
        """
        self._check_permission(file_id, user_id, owner_id)
        try:
            file_owner = next(
                d
                for d in os.listdir(self.base_dir)
                if os.path.exists(
                    os.path.join(self.base_dir, d, file_id)
                )
            )
            file_path = self._get_file_path(
                file_id, file_owner
            )
            metadata_path = self._get_metadata_path(
                file_id, file_owner
            )
            stats = os.stat(file_path)

            # Load metadata if available
            mime_type = "application/octet-stream"
            created_at = datetime.fromtimestamp(
                stats.st_ctime
            )
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    mime_type = metadata.get(
                        "mime_type", mime_type
                    )
                    created_at = datetime.fromisoformat(
                        metadata.get(
                            "created_at",
                            created_at.isoformat(),
                        )
                    )

            return StoredFile(
                id=file_id,
                user_id=file_owner,
                path=file_path,
                size_bytes=stats.st_size,
                mime_type=mime_type,
                status=StorageStatus.ACTIVE,
                created_at=created_at,
            )
        except OSError as e:
            raise StorageError(
                f"Failed to get metadata: {str(e)}"
            )
