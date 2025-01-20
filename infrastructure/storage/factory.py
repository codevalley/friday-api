"""Factory for creating storage service instances."""

import os
from typing import Optional

from domain.storage import IStorageService
from .local import LocalStorageService
from .mock import MockStorageService


class StorageFactory:
    """Factory for creating storage service instances.

    This factory creates and caches storage service instances based on
    configuration. It follows the singleton pattern to ensure only one
    instance of each backend type exists.
    """

    _instance: Optional[IStorageService] = None

    @classmethod
    def create_storage_service(
        cls,
        backend: str = "local",
        base_path: Optional[str] = None,
    ) -> IStorageService:
        """Create or get a storage service instance.

        Args:
            backend: Storage backend type (local, mock)
            base_path: Base path for file storage (for local backend)

        Returns:
            IStorageService: Storage service instance

        Raises:
            ValueError: If backend type is unknown
        """
        if cls._instance is None:
            if backend == "local":
                if base_path is None:
                    base_path = os.getenv(
                        "STORAGE_PATH",
                        os.path.abspath("./storage"),
                    )
                cls._instance = LocalStorageService(base_path)
            elif backend == "mock":
                cls._instance = MockStorageService()
            else:
                raise ValueError(f"Unknown storage backend: {backend}")

        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the factory, clearing any cached instances.

        This is mainly useful for testing when you want to create
        a fresh instance with different configuration.
        """
        cls._instance = None
