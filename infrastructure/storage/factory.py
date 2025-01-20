"""Factory for creating storage service instances."""

import os

from domain.storage import IStorageService
from infrastructure.storage.local import LocalStorageService
from infrastructure.storage.mock import MockStorageService
from infrastructure.storage.s3 import S3StorageService


class StorageFactory:
    """Factory for creating storage service instances."""

    @staticmethod
    def create_storage_service(
        storage_type: str = None,
    ) -> IStorageService:
        """Create a storage service instance.

        Args:
            storage_type: Type of storage service to create (local, mock, s3)
                        Defaults to value from STORAGE_BACKEND env var

        Returns:
            IStorageService: Storage service instance

        Raises:
            ValueError: If storage type invalid or required config is missing
        """
        storage_type = storage_type or os.getenv(
            "STORAGE_BACKEND", "local"
        )

        if storage_type == "local":
            storage_path = os.getenv("STORAGE_PATH")
            if not storage_path:
                raise ValueError(
                    "STORAGE_PATH environment variable is required"
                )
            return LocalStorageService(storage_path)

        elif storage_type == "mock":
            return MockStorageService()

        elif storage_type == "s3":
            bucket_name = os.getenv("S3_BUCKET_NAME")
            if not bucket_name:
                raise ValueError(
                    "S3_BUCKET_NAME environment variable is required"
                )

            return S3StorageService(
                bucket_name=bucket_name,
                endpoint_url=os.getenv("S3_ENDPOINT_URL"),
                access_key=os.getenv("AWS_ACCESS_KEY_ID"),
                secret_key=os.getenv(
                    "AWS_SECRET_ACCESS_KEY"
                ),
                region=os.getenv("AWS_REGION", "us-east-1"),
            )

        else:
            raise ValueError(
                f"Invalid storage type: {storage_type}"
            )
