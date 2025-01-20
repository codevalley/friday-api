"""Unit tests for Document domain model."""

import pytest
from domain.document import DocumentData, DocumentStatus
from domain.exceptions import DocumentValidationError


def test_document_creation():
    """Test creating a valid document."""
    doc = DocumentData(
        name="Test Document",
        storage_url="/test/path",
        mime_type="text/plain",
        size_bytes=100,
        user_id="user123",
    )

    assert doc.name == "Test Document"
    assert doc.storage_url == "/test/path"
    assert doc.mime_type == "text/plain"
    assert doc.size_bytes == 100
    assert doc.user_id == "user123"
    assert doc.status == DocumentStatus.PENDING
    assert doc.metadata == {}
    assert not doc.is_public
    assert doc.unique_name is None


def test_document_validation():
    """Test document validation rules."""
    # Test empty name
    with pytest.raises(
        DocumentValidationError,
        match="name cannot be empty",
    ):
        DocumentData(
            name="",
            storage_url="/test/path",
            mime_type="text/plain",
            size_bytes=100,
            user_id="user123",
        )

    # Test empty storage_url
    with pytest.raises(
        DocumentValidationError,
        match="storage_url cannot be empty",
    ):
        DocumentData(
            name="Test Document",
            storage_url="",
            mime_type="text/plain",
            size_bytes=100,
            user_id="user123",
        )

    # Test negative size
    with pytest.raises(
        DocumentValidationError,
        match="size_bytes must be positive",
    ):
        DocumentData(
            name="Test Document",
            storage_url="/test/path",
            mime_type="text/plain",
            size_bytes=-1,
            user_id="user123",
        )


def test_unique_name_validation():
    """Test unique name format validation."""
    # Test invalid characters
    with pytest.raises(
        DocumentValidationError,
        match="unique_name must be alphanumeric",
    ):
        DocumentData(
            name="Test Document",
            storage_url="/test/path",
            mime_type="text/plain",
            size_bytes=100,
            user_id="user123",
            unique_name="test-doc",  # Contains hyphen
        )

    # Test valid unique name
    doc = DocumentData(
        name="Test Document",
        storage_url="/test/path",
        mime_type="text/plain",
        size_bytes=100,
        user_id="user123",
        unique_name="testdoc123",
    )
    assert doc.unique_name == "testdoc123"


def test_status_transitions():
    """Test document status transitions."""
    doc = DocumentData(
        name="Test Document",
        storage_url="/test/path",
        mime_type="text/plain",
        size_bytes=100,
        user_id="user123",
    )

    # Test valid transitions
    doc.update_status(DocumentStatus.ACTIVE)
    assert doc.status == DocumentStatus.ACTIVE

    doc.update_status(DocumentStatus.ARCHIVED)
    assert doc.status == DocumentStatus.ARCHIVED

    # Test invalid transition
    with pytest.raises(
        DocumentValidationError,
        match="Invalid status transition",
    ):
        doc.update_status(DocumentStatus.PENDING)


def test_public_access():
    """Test public access rules."""
    # Test public document requires unique name
    with pytest.raises(
        DocumentValidationError,
        match="Public documents must have a unique name",
    ):
        DocumentData(
            name="Test Document",
            storage_url="/test/path",
            mime_type="text/plain",
            size_bytes=100,
            user_id="user123",
            is_public=True,  # Public but no unique name
        )

    # Test valid public document
    doc = DocumentData(
        name="Test Document",
        storage_url="/test/path",
        mime_type="text/plain",
        size_bytes=100,
        user_id="user123",
        is_public=True,
        unique_name="testdoc123",
    )
    assert doc.is_public
    assert doc.unique_name == "testdoc123"


def test_metadata_validation():
    """Test metadata validation."""
    # Test invalid metadata type
    with pytest.raises(
        DocumentValidationError,
        match="metadata must be a dictionary",
    ):
        DocumentData(
            name="Test Document",
            storage_url="/test/path",
            mime_type="text/plain",
            size_bytes=100,
            user_id="user123",
            metadata="invalid",  # Should be a dict
        )

    # Test valid metadata
    doc = DocumentData(
        name="Test Document",
        storage_url="/test/path",
        mime_type="text/plain",
        size_bytes=100,
        user_id="user123",
        metadata={"key1": "value1", "key2": 123},
    )
    assert doc.metadata == {"key1": "value1", "key2": 123}


def test_can_access():
    """Test document access rules."""
    doc = DocumentData(
        name="Test Document",
        storage_url="/test/path",
        mime_type="text/plain",
        size_bytes=100,
        user_id="user123",
    )

    # Owner can access
    assert doc.can_access("user123")

    # Other users cannot access private document
    assert not doc.can_access("other_user")

    # Public document can be accessed by anyone
    doc.is_public = True
    doc.unique_name = "testdoc123"
    assert doc.can_access("other_user")


def test_can_modify():
    """Test document modification rules."""
    doc = DocumentData(
        name="Test Document",
        storage_url="/test/path",
        mime_type="text/plain",
        size_bytes=100,
        user_id="user123",
    )

    # Owner can modify
    assert doc.can_modify("user123")

    # Other users cannot modify
    assert not doc.can_modify("other_user")

    # Even if document is public, only owner can modify
    doc.is_public = True
    doc.unique_name = "testdoc123"
    assert doc.can_modify("user123")
    assert not doc.can_modify("other_user")
