"""S3 storage implementation."""

from datetime import datetime, timezone
from typing import AsyncIterator
import boto3
from botocore.exceptions import ClientError

from domain.storage import (
    IStorageService,
    StoredFile,
    StorageStatus,
    StorageError,
    FileNotFoundError,
    StoragePermissionError,
)


class S3StorageService(IStorageService):
    """S3 storage implementation."""

    def __init__(self, bucket_name: str, endpoint_url: str = None):
        """Initialize S3 storage.
        
        Args:
            bucket_name: S3 bucket name
            endpoint_url: Optional endpoint URL for testing
        """
        self.bucket_name = bucket_name
        self.s3 = boto3.client("s3", endpoint_url=endpoint_url)

    def _get_object_key(self, file_id: str, user_id: str) -> str:
        """Get S3 object key for a file.
        
        Args:
            file_id: File ID
            user_id: User ID
            
        Returns:
            str: S3 object key
        """
        return f"{user_id}/{file_id}"

    async def store(
        self,
        file_data: bytes,
        file_id: str,
        user_id: str,
        mime_type: str,
    ) -> StoredFile:
        """Store a file in S3."""
        object_key = self._get_object_key(file_id, user_id)
        
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_data,
                ContentType=mime_type,
            )

            return StoredFile(
                id=file_id,
                user_id=user_id,
                path=f"s3://{self.bucket_name}/{object_key}",
                size_bytes=len(file_data),
                mime_type=mime_type,
                status=StorageStatus.ACTIVE,
                created_at=datetime.now(timezone.utc),
            )
        except ClientError as e:
            raise StorageError(f"Failed to store file in S3: {str(e)}")

    async def retrieve(
        self,
        file_id: str,
        user_id: str,
    ) -> AsyncIterator[bytes]:
        """Retrieve a file from S3."""
        object_key = self._get_object_key(file_id, user_id)
        
        try:
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )
            yield response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {file_id}")
            raise StorageError(f"Failed to retrieve file from S3: {str(e)}")

    async def delete(
        self,
        file_id: str,
        user_id: str,
    ) -> None:
        """Delete a file from S3."""
        object_key = self._get_object_key(file_id, user_id)
        
        try:
            self.s3.delete_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {file_id}")
            raise StorageError(f"Failed to delete file from S3: {str(e)}")

    async def get_metadata(
        self,
        file_id: str,
        user_id: str,
    ) -> StoredFile:
        """Get metadata for a file in S3."""
        object_key = self._get_object_key(file_id, user_id)
        
        try:
            response = self.s3.head_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )
            
            return StoredFile(
                id=file_id,
                user_id=user_id,
                path=f"s3://{self.bucket_name}/{object_key}",
                size_bytes=response["ContentLength"],
                mime_type=response.get("ContentType", "application/octet-stream"),
                status=StorageStatus.ACTIVE,
                created_at=response["LastModified"].replace(tzinfo=timezone.utc),
                updated_at=response["LastModified"].replace(tzinfo=timezone.utc),
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"File not found: {file_id}")
            raise StorageError(f"Failed to get metadata from S3: {str(e)}")
