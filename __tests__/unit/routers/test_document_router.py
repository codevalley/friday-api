"""Unit tests for DocumentRouter."""

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
import json
from io import BytesIO
from fastapi.security import HTTPAuthorizationCredentials

from routers.v1.DocumentRouter import (
    router,
    get_document_service,
    auth_scheme,
)
from domain.document import DocumentStatus
from dependencies import get_current_user


@pytest.fixture
def app(test_db_session, document_service, sample_user):
    """Create FastAPI test application with real database session."""
    app = FastAPI()
    app.include_router(
        router
    )  # Router already has /v1/docs prefix

    def override_get_document_service():
        return document_service

    def override_get_current_user():
        return sample_user

    app.dependency_overrides[
        get_document_service
    ] = override_get_document_service
    app.dependency_overrides[
        get_current_user
    ] = override_get_current_user
    app.dependency_overrides[
        auth_scheme
    ] = lambda: HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="test-token"
    )

    return TestClient(app)


def test_upload_document(
    app, document_service, sample_user
):
    """Test document upload endpoint."""
    # Create test file data
    file_content = b"test content"
    files = {
        "file": (
            "test.txt",
            BytesIO(file_content),
            "text/plain",
        )
    }
    data = {
        "name": "Test Doc",
        "mime_type": "text/plain",
        "metadata": json.dumps({"test": "data"}),
        "is_public": "false",
        "unique_name": "doc1",
    }

    # Make request with auth header
    response = app.post(
        "/v1/docs/upload",  # Updated path
        files=files,
        data=data,
        headers={"Authorization": "Bearer test-token"},
    )

    # Print error details if response is not successful
    if response.status_code != 201:
        print(f"Error Response: {response.text}")
        print(f"Status Code: {response.status_code}")

    # Verify response
    assert response.status_code == 201
    result = response.json()
    assert result["data"]["name"] == "Test Doc"
    assert result["data"]["mime_type"] == "text/plain"
    assert result["data"]["metadata"] == {"test": "data"}


def test_list_documents(app, document_service, sample_user):
    """Test document listing endpoint."""
    response = app.get(
        "/v1/docs/",  # Updated path
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    result = response.json()
    assert "data" in result
    assert "items" in result["data"]
    assert isinstance(result["data"]["items"], list)
    assert "total" in result["data"]
    assert "page" in result["data"]
    assert "size" in result["data"]
    assert "pages" in result["data"]
    assert "message" in result
    assert result["error"] is None


def test_get_document(
    app, document_service, sample_user, sample_document
):
    """Test get document endpoint."""
    response = app.get(
        f"/v1/docs/{sample_document.id}",  # Updated path
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["data"]["id"] == sample_document.id
    assert result["data"]["name"] == sample_document.name


def test_update_document(
    app, document_service, sample_user, sample_document
):
    """Test update document endpoint."""
    data = {
        "name": "Updated Doc",
        "metadata": {"updated": "data"},
        "is_public": True,
        "unique_name": "updated_doc",
    }

    response = app.put(
        f"/v1/docs/{sample_document.id}",  # Updated path
        json=data,
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["data"]["name"] == "Updated Doc"
    assert result["data"]["metadata"] == {"updated": "data"}
    assert result["data"]["is_public"] is True
    assert result["data"]["unique_name"] == "updated_doc"


def test_update_document_status(
    app, document_service, sample_user, sample_document
):
    """Test update document status endpoint."""
    data = {"status": DocumentStatus.ACTIVE.value}

    response = app.put(
        f"/v1/docs/{sample_document.id}/status",  # Updated path
        json=data,
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    result = response.json()
    assert (
        result["data"]["status"]
        == DocumentStatus.ACTIVE.value
    )


def test_delete_document(
    app, document_service, sample_user, sample_document
):
    """Test delete document endpoint."""
    response = app.delete(
        f"/v1/docs/{sample_document.id}",  # Updated path
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["data"] is None
    assert (
        result["message"] == "Document deleted successfully"
    )


def test_get_storage_usage(
    app, document_service, sample_user
):
    """Test get storage usage endpoint."""
    response = app.get(
        "/v1/docs/storage/usage",  # Updated path
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    result = response.json()
    assert isinstance(result["data"]["used_bytes"], int)
    assert isinstance(result["data"]["total_bytes"], int)


def test_get_public_document(
    app, document_service, sample_public_document
):
    """Test get public document endpoint."""
    response = app.get(
        f"/v1/docs/public/{sample_public_document.unique_name}"  # Updated path
    )

    assert response.status_code == 200
    result = response.json()
    assert result["data"]["id"] == sample_public_document.id
    assert (
        result["data"]["name"]
        == sample_public_document.name
    )
