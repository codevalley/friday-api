"""S3-compatible storage implementation."""

import os
from typing import Optional, Dict, Any

import aioboto3
from botocore.config import Config

from domain.storage import (
    IStorageService,
    StoredFile,
    StorageError,
)


class S3StorageService(IStorageService):
    """Storage service implementation for S3-compatible storage.

    Attributes:
        bucket_name: Name of the S3 bucket
        endpoint_url: Optional endpoint URL for S3-compatible services
        access_key: AWS access key ID
        secret_key: AWS secret access key
        region: AWS region
    """

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "us-east-1",
    ):
        """Initialize S3 storage service.

        Args:
            bucket_name: Name of the S3 bucket
            endpoint_url: Optional endpoint URL for S3-compatible services
            access_key: AWS access key ID (optional, defaults to env var)
            secret_key: AWS secret access key (optional, defaults to env var)
            region: AWS region (optional, defaults to us-east-1)
        """
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.access_key = access_key or os.getenv(
            "AWS_ACCESS_KEY_ID"
        )
        self.secret_key = secret_key or os.getenv(
            "AWS_SECRET_ACCESS_KEY"
        )
        self.region = region

        if not self.access_key or not self.secret_key:
            raise StorageError("AWS credentials not found")

        # Configure S3 client with reasonable defaults
        self.config = Config(
            region_name=self.region,
            signature_version="s3v4",
            retries={"max_attempts": 3},
            connect_timeout=5,
            read_timeout=10,
        )

        # Create session for aioboto3
        self.session = aioboto3.Session()

    async def store_file(
        self,
        file_path: str,
        content: bytes,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StoredFile:
        """Store a file in S3.

        Args:
            file_path: Path where to store the file
            content: File content as bytes
            metadata: Optional metadata to store with the file

        Returns:
            StoredFile: Information about the stored file

        Raises:
            StorageError: If file cannot be stored
        """
        try:
            async with self.session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=self.config,
            ) as s3:
                # Store the file
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=file_path,
                    Body=content,
                    Metadata=metadata or {},
                )

                # Get file info
                response = await s3.head_object(
                    Bucket=self.bucket_name,
                    Key=file_path,
                )

                return StoredFile(
                    path=file_path,
                    size=response["ContentLength"],
                    created_at=response["LastModified"],
                    metadata=metadata or {},
                )

        except Exception as e:
            raise StorageError(
                f"Failed to store file: {str(e)}"
            ) from e

    async def retrieve_file(self, file_path: str) -> bytes:
        """Retrieve a file from S3.

        Args:
            file_path: Path to the file

        Returns:
            bytes: File content

        Raises:
            StorageError: If file cannot be retrieved
        """
        try:
            async with self.session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=self.config,
            ) as s3:
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=file_path,
                )
                return await response["Body"].read()

        except Exception as e:
            raise StorageError(
                f"Failed to retrieve file: {str(e)}"
            ) from e

    async def delete_file(self, file_path: str) -> None:
        """Delete a file from S3.

        Args:
            file_path: Path to the file to delete

        Raises:
            StorageError: If file cannot be deleted
        """
        try:
            async with self.session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=self.config,
            ) as s3:
                await s3.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_path,
                )

        except Exception as e:
            raise StorageError(
                f"Failed to delete file: {str(e)}"
            ) from e

    async def get_metadata(
        self, file_path: str
    ) -> StoredFile:
        """Get metadata for a file in S3.

        Args:
            file_path: Path to the file

        Returns:
            StoredFile: File metadata

        Raises:
            StorageError: If metadata cannot be retrieved
        """
        try:
            async with self.session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=self.config,
            ) as s3:
                response = await s3.head_object(
                    Bucket=self.bucket_name,
                    Key=file_path,
                )

                return StoredFile(
                    path=file_path,
                    size=response["ContentLength"],
                    created_at=response["LastModified"],
                    metadata=response.get("Metadata", {}),
                )

        except Exception as e:
            raise StorageError(
                f"Failed to get metadata: {str(e)}"
            ) from e

    async def get_public_url(
        self, file_path: str, expires_in: int = 3600
    ) -> str:
        """Get a pre-signed URL for public access.

        Args:
            file_path: Path to the file
            expires_in: URL expiration time in seconds

        Returns:
            str: Pre-signed URL for file access

        Raises:
            StorageError: If URL cannot be generated
        """
        try:
            async with self.session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=self.config,
            ) as s3:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": self.bucket_name,
                        "Key": file_path,
                    },
                    ExpiresIn=expires_in,
                )
                return url

        except Exception as e:
            raise StorageError(
                f"Failed to generate public URL: {str(e)}"
            ) from e
