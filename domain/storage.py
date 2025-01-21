"""Domain models and interfaces for storage functionality."""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import AsyncIterator, Optional, Protocol


class StorageStatus(str, Enum):
    """Status of a stored file."""

    PENDING = "pending"  # File is being uploaded
    ACTIVE = "active"  # File is available
    ERROR = "error"  # Error occurred during storage


@dataclass
class StoredFile:
    """Domain model representing a stored file.

    This model contains metadata about a file in storage, separate
    from any document-specific metadata.
    """

    id: str
    user_id: str
    path: str
    size_bytes: int
    mime_type: str
    status: StorageStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None


class StorageError(Exception):
    """Base exception for storage-related errors."""

    pass


class FileNotFoundError(StorageError):
    """Raised when a requested file does not exist."""

    pass


class StoragePermissionError(StorageError):
    """Raised when user does not have permission to access a file."""

    pass


class IStorageService(Protocol):
    """Interface for storage operations.

    This interface defines the contract for storage implementations,
    following the dependency inversion principle.
    """

    @abstractmethod
    async def store(
        self,
        file_data: bytes,
        file_id: str,
        user_id: str,
        mime_type: str,
    ) -> StoredFile:
        """Store a file.

        Args:
            file_data: Raw file content
            file_id: Unique identifier for the file
            user_id: ID of the user who owns the file
            mime_type: MIME type of the file

        Returns:
            StoredFile: Metadata about the stored file

        Raises:
            StorageError: If file storage fails
        """
        ...

    @abstractmethod
    async def retrieve(
        self,
        file_id: str,
        user_id: str,
        owner_id: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        """Retrieve a file's content.

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
        ...

    @abstractmethod
    async def delete(
        self,
        file_id: str,
        user_id: str,
    ) -> None:
        """Delete a file.

        Args:
            file_id: ID of the file to delete
            user_id: ID of the user requesting deletion

        Raises:
            FileNotFoundError: If file does not exist
            StoragePermissionError: If user cannot delete file
            StorageError: If deletion fails
        """
        ...

    @abstractmethod
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
        ...
