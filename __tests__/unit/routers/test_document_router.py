"""Unit tests for DocumentRouter."""

import pytest
from unittest.mock import Mock
from fastapi import FastAPI, APIRouter
from starlette.testclient import TestClient
from starlette.datastructures import (
    UploadFile as StarletteUploadFile,
)
from fastapi import UploadFile as FastAPIUploadFile
from datetime import datetime
import json
from io import BytesIO
from fastapi.security import HTTPAuthorizationCredentials

from routers.v1.DocumentRouter import router
from services.DocumentService import DocumentService
from schemas.pydantic.DocumentSchema import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
)
from domain.document import DocumentStatus
from dependencies import get_current_user
from auth.bearer import CustomHTTPBearer
from orm.UserModel import User
from schemas.pydantic.StorageSchema import (
    StorageUsageResponse,
)


@pytest.fixture
def mock_storage():
    """Create a mock storage service."""
    storage = Mock()
    storage.upload_file = Mock()
    storage.delete_file = Mock()
    storage.get_file = Mock()
    storage.get_file_size = Mock()
    return storage


@pytest.fixture
def mock_service(mock_storage):
    """Create a mock DocumentService."""
    service = Mock()
    service.storage = mock_storage

    # Set up async methods
    async def async_create_document(*args, **kwargs):
        # Mock file read
        file = kwargs.get("file")
        if file:
            # Create a mock FastAPI UploadFile
            mock_file = Mock(spec=FastAPIUploadFile)
            mock_file.filename = file.filename
            mock_file.content_type = file.content_type
            mock_file.file = file.file
            kwargs["file"] = mock_file
        return service.create_document.return_value

    service.create_document = Mock(
        side_effect=async_create_document
    )

    async def async_get_user_documents(*args, **kwargs):
        return service.get_user_documents.return_value

    service.get_user_documents = Mock(
        side_effect=async_get_user_documents
    )

    async def async_get_document(*args, **kwargs):
        return service.get_document.return_value

    service.get_document = Mock(
        side_effect=async_get_document
    )

    async def async_update_document(*args, **kwargs):
        return service.update_document.return_value

    service.update_document = Mock(
        side_effect=async_update_document
    )

    async def async_update_document_status(*args, **kwargs):
        return service.update_document_status.return_value

    service.update_document_status = Mock(
        side_effect=async_update_document_status
    )

    async def async_delete_document(*args, **kwargs):
        return service.delete_document.return_value

    service.delete_document = Mock(
        side_effect=async_delete_document
    )

    async def async_get_user_storage_usage(*args, **kwargs):
        return service.get_user_storage_usage.return_value

    service.get_user_storage_usage = Mock(
        side_effect=async_get_user_storage_usage
    )

    async def async_get_public_document(*args, **kwargs):
        return service.get_public_document.return_value

    service.get_public_document = Mock(
        side_effect=async_get_public_document
    )

    async def async_get_public_document_content(
        *args, **kwargs
    ):
        return (
            service.get_public_document_content.return_value
        )

    service.get_public_document_content = Mock(
        side_effect=async_get_public_document_content
    )

    return service


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = Mock(spec=User)
    user.id = "test-user-id"  # Use string ID
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_auth_credentials():
    """Create mock auth credentials."""
    creds = Mock(spec=HTTPAuthorizationCredentials)
    creds.scheme = "Bearer"
    creds.credentials = "test-token"
    return creds


@pytest.fixture
def app(mock_service, mock_user, mock_auth_credentials):
    """Create a FastAPI test application."""
    app = FastAPI()

    # Create a v1 router
    v1_router = APIRouter(prefix="/v1")
    v1_router.include_router(router)
    app.include_router(v1_router)

    # Override dependencies
    app.dependency_overrides = {
        DocumentService: lambda: mock_service,
        get_current_user: lambda: mock_user,
        CustomHTTPBearer: lambda: lambda request: mock_auth_credentials,
    }
    return app


@pytest.mark.asyncio
async def test_upload_document(
    app, mock_service, mock_user
):
    """Test document upload endpoint."""
    # Prepare test data
    test_doc = DocumentResponse(
        id=1,
        user_id=mock_user.id,  # Now a string
        name="test.txt",
        storage_url="local://documents/test.txt",
        mime_type="text/plain",
        size_bytes=100,
        status=DocumentStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=None,
        is_public=False,
        metadata={},
        unique_name=None,
    )
    mock_service.create_document.return_value = test_doc

    # Create document data
    test_content = b"test content"
    test_file = BytesIO(test_content)
    test_file.name = "test.txt"

    # Create multipart form data
    files = {
        "file": ("test.txt", test_file, "text/plain"),
    }
    form = {
        "name": "test.txt",
        "mime_type": "text/plain",
        "metadata": json.dumps({"key": "value"}),
        "is_public": "false",
        "unique_name": "",
    }

    # Create test client
    client = TestClient(app)

    # Make request
    response = client.post(
        "/v1/docs/protected/upload",
        files=files,
        data=form,
        headers={"Authorization": "Bearer test-token"},
    )

    # Assert response
    assert response.status_code == 201
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert "data" in response_data
    assert "message" in response_data
    assert isinstance(response_data["data"], dict)
    assert response_data["data"]["id"] == 1
    assert response_data["data"]["name"] == "test.txt"

    # Verify service call
    mock_service.create_document.assert_called_once()
    call_args = mock_service.create_document.call_args[1]
    assert isinstance(call_args["document"], DocumentCreate)
    assert call_args["user_id"] == mock_user.id
    # The file will be a Starlette UploadFile in tests
    assert isinstance(
        call_args["file"],
        (FastAPIUploadFile, StarletteUploadFile),
    )


def test_list_documents(app, mock_service, mock_user):
    """Test document listing endpoint."""
    # Prepare test data
    test_docs = [
        DocumentResponse(
            id=1,
            user_id=mock_user.id,
            name="test1.txt",
            storage_url="local://documents/test1.txt",
            mime_type="text/plain",
            size_bytes=100,
            status=DocumentStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=None,
            is_public=False,
            metadata={},
            unique_name=None,
        ),
        DocumentResponse(
            id=2,
            user_id=mock_user.id,
            name="test2.txt",
            storage_url="local://documents/test2.txt",
            mime_type="text/plain",
            size_bytes=200,
            status=DocumentStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=None,
            is_public=False,
            metadata={},
            unique_name=None,
        ),
    ]
    mock_service.get_user_documents.return_value = test_docs

    # Create test client and make request
    client = TestClient(app)
    response = client.get(
        "/v1/docs/protected",
        params={"page": 1, "size": 10},
        headers={"Authorization": "Bearer test-token"},
    )

    # Assert response
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert "data" in response_data
    assert "message" in response_data
    assert isinstance(response_data["data"], list)
    assert len(response_data["data"]) == 2
    assert response_data["data"][0]["id"] == 1
    assert response_data["data"][0]["name"] == "test1.txt"
    assert response_data["data"][1]["id"] == 2
    assert response_data["data"][1]["name"] == "test2.txt"

    # Verify service call
    mock_service.get_user_documents.assert_called_once_with(
        user_id=mock_user.id,
        skip=0,  # (page-1) * size
        limit=10,
        status=None,
        mime_type=None,
    )


@pytest.mark.asyncio
async def test_get_document(app, mock_service, mock_user):
    """Test get document endpoint."""
    # Prepare test data
    test_doc = DocumentResponse(
        id=1,
        user_id=mock_user.id,
        name="test.txt",
        storage_url="local://documents/test.txt",
        mime_type="text/plain",
        size_bytes=100,
        status=DocumentStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=None,
        is_public=False,
        metadata={},
        unique_name=None,
    )
    mock_service.get_document.return_value = test_doc

    # Make request
    client = TestClient(app)
    response = client.get(
        "/v1/docs/protected/1",
        headers={"Authorization": "Bearer test-token"},
    )

    # Assert response
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert "data" in response_data
    assert "message" in response_data
    assert isinstance(response_data["data"], dict)
    assert response_data["data"]["id"] == 1
    assert response_data["data"]["name"] == "test.txt"
    assert (
        response_data["data"]["storage_url"]
        == "local://documents/test.txt"
    )

    # Verify service call
    mock_service.get_document.assert_called_once_with(
        document_id=1,
        user_id=mock_user.id,
    )


@pytest.mark.asyncio
async def test_update_document(
    app, mock_service, mock_user
):
    """Test update document endpoint."""
    # Prepare test data
    test_doc = DocumentResponse(
        id=1,
        user_id=mock_user.id,
        name="updated.txt",
        storage_url="local://documents/test.txt",
        mime_type="text/plain",
        size_bytes=100,
        status=DocumentStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=None,
        is_public=True,
        metadata={"key": "updated"},
        unique_name=None,
    )
    mock_service.update_document.return_value = test_doc

    # Make request
    update_data = {
        "name": "updated.txt",
        "is_public": True,
        "metadata": {"key": "updated"},
    }
    client = TestClient(app)
    response = client.patch(
        "/v1/docs/protected/1",
        json=update_data,
        headers={"Authorization": "Bearer test-token"},
    )

    # Assert response
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert "data" in response_data
    assert "message" in response_data
    assert isinstance(response_data["data"], dict)
    assert response_data["data"]["id"] == test_doc.id
    assert (
        response_data["data"]["user_id"] == test_doc.user_id
    )
    assert response_data["data"]["name"] == test_doc.name
    assert (
        response_data["data"]["storage_url"]
        == test_doc.storage_url
    )
    assert (
        response_data["data"]["mime_type"]
        == test_doc.mime_type
    )
    assert (
        response_data["data"]["size_bytes"]
        == test_doc.size_bytes
    )
    assert (
        response_data["data"]["status"]
        == test_doc.status.value
    )
    assert (
        response_data["data"]["is_public"]
        == test_doc.is_public
    )
    assert (
        response_data["data"]["metadata"]
        == test_doc.metadata
    )

    # Verify service call
    mock_service.update_document.assert_called_once()
    call_args = mock_service.update_document.call_args[1]
    assert call_args["document_id"] == 1
    assert call_args["user_id"] == mock_user.id
    assert isinstance(
        call_args["update_data"], DocumentUpdate
    )
    assert call_args["update_data"].name == "updated.txt"
    assert call_args["update_data"].is_public is True
    assert call_args["update_data"].metadata == {
        "key": "updated"
    }


@pytest.mark.asyncio
async def test_update_document_status(
    app, mock_service, mock_user
):
    """Test update document status endpoint."""
    # Prepare test data
    test_doc = DocumentResponse(
        id=1,
        user_id=mock_user.id,
        name="test.txt",
        storage_url="local://documents/test.txt",
        mime_type="text/plain",
        size_bytes=100,
        status=DocumentStatus.ARCHIVED,
        created_at=datetime.now(),
        updated_at=None,
        is_public=False,
        metadata={},
        unique_name=None,
    )
    mock_service.update_document_status.return_value = (
        test_doc
    )

    # Make request
    client = TestClient(app)
    response = client.patch(
        "/v1/docs/protected/1/status",
        json={"status": "archived"},
        headers={"Authorization": "Bearer test-token"},
    )

    # Assert response
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert "data" in response_data
    assert "message" in response_data
    assert isinstance(response_data["data"], dict)
    assert response_data["data"]["id"] == test_doc.id
    assert (
        response_data["data"]["user_id"] == test_doc.user_id
    )
    assert response_data["data"]["name"] == test_doc.name
    assert (
        response_data["data"]["storage_url"]
        == test_doc.storage_url
    )
    assert (
        response_data["data"]["mime_type"]
        == test_doc.mime_type
    )
    assert (
        response_data["data"]["size_bytes"]
        == test_doc.size_bytes
    )
    assert (
        response_data["data"]["status"]
        == test_doc.status.value
    )
    assert (
        response_data["data"]["is_public"]
        == test_doc.is_public
    )

    # Verify service call
    mock_service.update_document_status.assert_called_once_with(
        document_id=1,
        user_id=mock_user.id,
        new_status=DocumentStatus.ARCHIVED,
    )


@pytest.mark.asyncio
async def test_delete_document(
    app, mock_service, mock_user
):
    """Test delete document endpoint."""
    # Make request
    client = TestClient(app)
    response = client.delete(
        "/v1/docs/protected/1",
        headers={"Authorization": "Bearer test-token"},
    )

    # Assert response
    assert response.status_code == 204
    assert response.content == b""  # No content for 204

    # Verify service call
    mock_service.delete_document.assert_called_once_with(
        document_id=1,
        user_id=mock_user.id,
    )


@pytest.mark.asyncio
async def test_get_storage_usage(
    app, mock_service, mock_user
):
    """Test get storage usage endpoint."""
    # Prepare test data
    mock_service.get_user_storage_usage.return_value = (
        1024  # 1KB
    )

    # Make request
    client = TestClient(app)
    response = client.get(
        "/v1/docs/protected/storage-usage",
        headers={"Authorization": "Bearer test-token"},
    )

    # Debug print
    print("Response content:", response.content)
    print("Response status:", response.status_code)
    if response.status_code == 422:
        print("Validation error:", response.json())

    # Assert response
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert "data" in response_data
    assert "message" in response_data
    assert isinstance(response_data["data"], dict)
    assert response_data["data"]["usage_bytes"] == 1024

    # Verify response model
    StorageUsageResponse.model_validate(
        response_data["data"]
    )

    # Verify service call
    mock_service.get_user_storage_usage.assert_called_once_with(
        user_id=mock_user.id,
    )


@pytest.mark.asyncio
async def test_get_public_document(app, mock_service):
    """Test get public document endpoint."""
    # Prepare test data
    test_doc = DocumentResponse(
        id=1,
        user_id="user-123",  # Use string ID
        name="test.txt",
        storage_url="local://documents/test.txt",
        mime_type="text/plain",
        size_bytes=100,
        status=DocumentStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=None,
        is_public=True,
        metadata={},
        unique_name=None,
    )
    mock_service.get_public_document.return_value = test_doc

    # Make request
    client = TestClient(app)
    response = client.get("/v1/docs/public/1")

    # Assert response
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert "data" in response_data
    assert "message" in response_data
    assert isinstance(response_data["data"], dict)
    assert response_data["data"]["id"] == test_doc.id
    assert (
        response_data["data"]["user_id"] == test_doc.user_id
    )
    assert response_data["data"]["name"] == test_doc.name
    assert (
        response_data["data"]["storage_url"]
        == test_doc.storage_url
    )
    assert (
        response_data["data"]["mime_type"]
        == test_doc.mime_type
    )
    assert (
        response_data["data"]["size_bytes"]
        == test_doc.size_bytes
    )
    assert (
        response_data["data"]["status"]
        == test_doc.status.value
    )
    assert (
        response_data["data"]["is_public"]
        == test_doc.is_public
    )

    # Verify service call
    mock_service.get_public_document.assert_called_once_with(
        document_id=1,
    )
