"""Tests for S3 storage implementation."""

import json
from datetime import datetime, timezone
from io import BytesIO

import boto3
import pytest
from botocore.stub import Stubber

from domain.storage import (
    FileNotFoundError,
    StorageError,
    StorageStatus,
    StoredFile,
)
from infrastructure.storage.s3_sync import S3StorageService


@pytest.fixture
def s3_client():
    """Create a stubbed S3 client for testing."""
    client = boto3.client(
        "s3",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )
    return client


@pytest.fixture
def storage(s3_client):
    """Create an S3 storage service for testing."""
    storage = S3StorageService(
        bucket_name="test-bucket",
        client=s3_client,
    )
    storage.client = s3_client
    return storage


@pytest.fixture
def s3_stubber(s3_client):
    """Create a stubber for S3 client responses."""
    return Stubber(s3_client)


@pytest.fixture
def test_file():
    """Create a test file for storage operations."""
    return b"Hello, World!"


def test_store_file(storage, s3_stubber, test_file):
    """Test storing a file."""
    # Expected S3 requests
    s3_stubber.add_response(
        "put_object",
        {},
        {
            "Bucket": "test-bucket",
            "Key": "user1/test.txt",
            "Body": test_file,
            "ContentType": "text/plain",
        },
    )

    metadata = {
        "user_id": "user1",
        "mime_type": "text/plain",
        "created_at": "2025-01-25T17:08:44.982014+00:00",
    }
    s3_stubber.add_response(
        "put_object",
        {},
        {
            "Bucket": "test-bucket",
            "Key": "user1/test.txt.meta",
            "Body": json.dumps(metadata).encode(),
            "ContentType": "application/json",
        },
    )

    s3_stubber.add_response(
        "head_object",
        {
            "ContentLength": len(test_file),
            "LastModified": datetime(
                2025, 1, 25, 17, 8, 44, tzinfo=timezone.utc
            ),
        },
        {
            "Bucket": "test-bucket",
            "Key": "user1/test.txt",
        },
    )

    s3_stubber.activate()

    # Store a file
    stored = storage.store(
        file_data=test_file,
        file_id="test.txt",
        user_id="user1",
        mime_type="text/plain",
    )

    # Verify file was stored correctly
    assert stored.id == "test.txt"
    assert stored.user_id == "user1"
    assert stored.path == "user1/test.txt"
    assert stored.size_bytes == len(test_file)
    assert stored.mime_type == "text/plain"
    assert stored.created_at == datetime.fromisoformat(
        "2025-01-25T17:08:44.982014+00:00"
    )

    s3_stubber.assert_no_pending_responses()


def test_retrieve_file(storage, s3_stubber, test_file):
    """Test retrieving a file."""
    # Expected S3 requests for metadata
    s3_stubber.add_response(
        "get_object",
        {
            "Body": BytesIO(
                json.dumps(
                    {
                        "user_id": "user1",
                        "mime_type": "text/plain",
                        "created_at": "2025-01-25T17:08:44.982014+00:00",
                    }
                ).encode()
            ),
            "ContentLength": len(test_file),
            "LastModified": datetime(
                2025, 1, 25, 17, 8, 44, tzinfo=timezone.utc
            ),
        },
        {
            "Bucket": "test-bucket",
            "Key": "user1/test.txt.meta",
        },
    )

    # Expected S3 request for file content
    s3_stubber.add_response(
        "get_object",
        {
            "Body": BytesIO(test_file),
            "ContentType": "text/plain",
        },
        {
            "Bucket": "test-bucket",
            "Key": "user1/test.txt",
        },
    )

    s3_stubber.activate()

    # Retrieve the file
    file_obj = storage.retrieve(
        file_id="test.txt",
        user_id="user1",
    )

    # Read the file content
    content = file_obj.read()
    assert content == test_file

    s3_stubber.assert_no_pending_responses()


def test_retrieve_file_with_owner(
    storage, s3_stubber, test_file
):
    """Test retrieving a file with owner specified."""
    # Expected S3 requests for metadata
    s3_stubber.add_response(
        "get_object",
        {
            "Body": BytesIO(
                json.dumps(
                    {
                        "user_id": "user1",
                        "mime_type": "text/plain",
                        "created_at": "2025-01-25T17:08:44.982014+00:00",
                    }
                ).encode()
            ),
            "ContentLength": len(test_file),
            "LastModified": datetime(
                2025, 1, 25, 17, 8, 44, tzinfo=timezone.utc
            ),
        },
        {
            "Bucket": "test-bucket",
            "Key": "user1/test.txt.meta",
        },
    )

    # Expected S3 request for file content
    s3_stubber.add_response(
        "get_object",
        {
            "Body": BytesIO(test_file),
            "ContentType": "text/plain",
        },
        {
            "Bucket": "test-bucket",
            "Key": "user1/test.txt",
        },
    )

    s3_stubber.activate()

    # Retrieve file
    file_obj = storage.retrieve(
        file_id="test.txt",
        user_id="user2",
        owner_id="user1",
    )

    # Verify file content
    assert file_obj.read() == test_file

    s3_stubber.assert_no_pending_responses()


def test_delete_file(storage, s3_stubber):
    """Test deleting a file."""
    # Expected S3 requests for metadata
    s3_stubber.add_response(
        "list_objects_v2",
        {
            "CommonPrefixes": [
                {"Prefix": "user1/"},
                {"Prefix": "user2/"},
            ],
        },
        {
            "Bucket": "test-bucket",
            "Delimiter": "/",
        },
    )

    s3_stubber.add_response(
        "head_object",
        {
            "ContentLength": 100,
            "ContentType": "text/plain",
            "LastModified": datetime(
                2025, 1, 25, 17, 8, 44, tzinfo=timezone.utc
            ),
        },
        {
            "Bucket": "test-bucket",
            "Key": "user1/test.txt",
        },
    )

    metadata = {
        "user_id": "user1",
        "mime_type": "text/plain",
        "created_at": "2025-01-25T17:08:44.982014+00:00",
    }
    metadata_json = json.dumps(metadata).encode()

    s3_stubber.add_response(
        "get_object",
        {
            "Body": BytesIO(metadata_json),
        },
        {
            "Bucket": "test-bucket",
            "Key": "user1/test.txt.meta",
        },
    )

    s3_stubber.add_response(
        "delete_object",
        {},
        {
            "Bucket": "test-bucket",
            "Key": "user1/test.txt",
        },
    )

    s3_stubber.add_response(
        "delete_object",
        {},
        {
            "Bucket": "test-bucket",
            "Key": "user1/test.txt.meta",
        },
    )

    s3_stubber.activate()

    # Delete file
    storage.delete(
        file_id="test.txt",
        user_id="user1",
    )

    s3_stubber.assert_no_pending_responses()


def test_get_metadata(storage, s3_stubber, test_file):
    """Test getting file metadata."""
    # Expected S3 requests
    s3_stubber.add_response(
        "list_objects_v2",
        {
            "CommonPrefixes": [
                {"Prefix": "user1/"},
                {"Prefix": "user2/"},
            ],
        },
        {
            "Bucket": "test-bucket",
            "Delimiter": "/",
        },
    )

    s3_stubber.add_response(
        "head_object",
        {
            "ContentLength": len(test_file),
            "LastModified": datetime(
                2025, 1, 25, 17, 8, 44, tzinfo=timezone.utc
            ),
        },
        {
            "Bucket": "test-bucket",
            "Key": "user1/test.txt",
        },
    )

    metadata = {
        "user_id": "user1",
        "mime_type": "text/plain",
        "created_at": "2025-01-25T17:08:44.982014+00:00",
    }
    s3_stubber.add_response(
        "get_object",
        {
            "Body": BytesIO(json.dumps(metadata).encode()),
            "ContentLength": len(json.dumps(metadata)),
            "LastModified": datetime(
                2025, 1, 25, 17, 8, 44, tzinfo=timezone.utc
            ),
        },
        {
            "Bucket": "test-bucket",
            "Key": "user1/test.txt.meta",
        },
    )

    s3_stubber.activate()

    # Get metadata
    stored = storage.get_metadata(
        file_id="test.txt",
        user_id="user1",
    )

    # Verify metadata
    assert isinstance(stored, StoredFile)
    assert stored.id == "test.txt"
    assert stored.user_id == "user1"
    assert stored.path == "user1/test.txt"
    assert stored.size_bytes == len(test_file)
    assert stored.mime_type == "text/plain"
    assert stored.status == StorageStatus.ACTIVE
    assert stored.created_at == datetime.fromisoformat(
        "2025-01-25T17:08:44.982014+00:00"
    )

    s3_stubber.assert_no_pending_responses()


def test_file_not_found(storage, s3_stubber):
    """Test file not found error."""
    # Expected S3 requests
    s3_stubber.add_client_error(
        "get_object",
        service_error_code="NoSuchKey",
        service_message="The specified key does not exist.",
        http_status_code=404,
        expected_params={
            "Bucket": "test-bucket",
            "Key": "user1/nonexistent.txt.meta",
        },
    )

    s3_stubber.activate()

    with pytest.raises(FileNotFoundError):
        storage.retrieve(
            file_id="nonexistent.txt",
            user_id="user1",
        )

    s3_stubber.assert_no_pending_responses()


def test_s3_errors(storage, s3_stubber):
    """Test handling of S3 errors."""
    # Expected S3 requests
    s3_stubber.add_client_error(
        "put_object",
        "InternalError",
        {"Message": "Internal error"},
        500,
        expected_params={
            "Bucket": "test-bucket",
            "Key": "user1/test.txt",
            "Body": b"test",
            "ContentType": "text/plain",
        },
    )

    s3_stubber.activate()

    with pytest.raises(StorageError):
        storage.store(
            file_data=b"test",
            file_id="test.txt",
            user_id="user1",
            mime_type="text/plain",
        )

    s3_stubber.assert_no_pending_responses()
