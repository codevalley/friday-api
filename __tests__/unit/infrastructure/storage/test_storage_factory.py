"""Unit tests for StorageFactory."""

import os
import pytest
from unittest.mock import patch, MagicMock

from infrastructure.storage.factory import StorageFactory
from infrastructure.storage.local_sync import (
    LocalStorageService,
)
from infrastructure.storage.mock_sync import (
    MockStorageService,
)
from infrastructure.storage.s3_sync import S3StorageService


@pytest.fixture
def clean_env():
    """Remove storage-related env vars for clean testing."""
    storage_vars = [
        "STORAGE_BACKEND",
        "STORAGE_PATH",
        "S3_BUCKET_NAME",
        "S3_ENDPOINT_URL",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
    ]
    # Store original values
    original_values = {}
    for var in storage_vars:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value


def test_default_storage_type(clean_env):
    """Test default storage type is local."""
    with pytest.raises(ValueError) as exc:
        StorageFactory.create_storage_service()
    assert (
        "STORAGE_PATH environment variable is required"
        in str(exc.value)
    )


def test_local_storage_creation(clean_env):
    """Test creating local storage service."""
    os.environ["STORAGE_PATH"] = "/tmp/test"
    service = StorageFactory.create_storage_service("local")
    assert isinstance(service, LocalStorageService)
    assert service.base_dir == "/tmp/test"


def test_local_storage_missing_path(clean_env):
    """Test local storage creation fails without path."""
    with pytest.raises(ValueError) as exc:
        StorageFactory.create_storage_service("local")
    assert (
        "STORAGE_PATH environment variable is required"
        in str(exc.value)
    )


def test_mock_storage_creation(clean_env):
    """Test creating mock storage service."""
    service = StorageFactory.create_storage_service("mock")
    assert isinstance(service, MockStorageService)


@patch("boto3.client")
def test_s3_storage_creation(mock_boto3_client, clean_env):
    """Test creating S3 storage service."""
    # Setup environment
    os.environ["S3_BUCKET_NAME"] = "test-bucket"
    os.environ["S3_ENDPOINT_URL"] = "http://localhost:4566"
    os.environ["AWS_ACCESS_KEY_ID"] = "test-key"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test-secret"
    os.environ["AWS_REGION"] = "us-west-2"

    # Create mock client
    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client

    service = StorageFactory.create_storage_service("s3")

    assert isinstance(service, S3StorageService)
    assert service.bucket_name == "test-bucket"
    assert service.client == mock_client

    # Verify boto3 client was created with correct params
    mock_boto3_client.assert_called_once_with(
        "s3",
        endpoint_url="http://localhost:4566",
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret",
        region_name="us-west-2",
    )


def test_s3_storage_missing_bucket(clean_env):
    """Test S3 storage creation fails without bucket name."""
    with pytest.raises(ValueError) as exc:
        StorageFactory.create_storage_service("s3")
    assert (
        "S3_BUCKET_NAME environment variable is required"
        in str(exc.value)
    )


@patch("builtins.__import__")
def test_s3_storage_missing_boto3(mock_import, clean_env):
    """Test that creating S3 storage fails when boto3 is not installed."""

    def mock_import_fn(name, *args, **kwargs):
        if name == "boto3":
            raise ImportError("No module named 'boto3'")
        return __import__(name, *args, **kwargs)

    mock_import.side_effect = mock_import_fn

    with pytest.raises(ValueError) as exc_info:
        StorageFactory.create_storage_service("s3")

    assert (
        "boto3 package is required for S3 storage"
        in str(exc_info.value)
    )


def test_invalid_storage_type(clean_env):
    """Test creating storage with invalid type."""
    with pytest.raises(ValueError) as exc:
        StorageFactory.create_storage_service("invalid")
    assert "Invalid storage type: invalid" in str(exc.value)


def test_storage_type_from_env(clean_env):
    """Test storage type is read from environment variable."""
    os.environ["STORAGE_BACKEND"] = "mock"
    service = StorageFactory.create_storage_service()
    assert isinstance(service, MockStorageService)


def test_s3_default_region(clean_env):
    """Test S3 storage uses default region when not specified."""
    os.environ["S3_BUCKET_NAME"] = "test-bucket"

    with patch("boto3.client") as mock_boto3_client:
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        service = StorageFactory.create_storage_service(  # noqa: F841
            "s3"
        )

        # Verify default region was used
        mock_boto3_client.assert_called_once()
        call_kwargs = mock_boto3_client.call_args[1]
        assert call_kwargs["region_name"] == "us-east-1"
