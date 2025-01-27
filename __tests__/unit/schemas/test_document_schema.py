"""Test suite for document schemas."""

import pytest
from datetime import datetime, UTC
from pydantic import ValidationError

from schemas.pydantic.DocumentSchema import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentStatusUpdate,
)
from domain.document import DocumentStatus


def test_document_base_valid():
    """Test valid document base schema."""
    doc = DocumentBase(
        name="test.pdf",
        mime_type="application/pdf",
        metadata={"category": "test"},
        unique_name="test_doc_123",
        is_public=True,
    )
    assert doc.name == "test.pdf"
    assert doc.mime_type == "application/pdf"
    assert doc.doc_metadata == {"category": "test"}
    assert doc.unique_name == "test_doc_123"
    assert doc.is_public is True


def test_document_base_defaults():
    """Test document base schema defaults."""
    doc = DocumentBase(
        name="test.pdf",
        mime_type="application/pdf",
    )
    assert doc.doc_metadata is None
    assert doc.unique_name is None
    assert doc.is_public is False


def test_document_base_invalid_name():
    """Test invalid document name validation."""
    with pytest.raises(ValidationError) as exc:
        DocumentBase(
            name="",  # Empty name
            mime_type="application/pdf",
        )
    assert "name" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        DocumentBase(
            name="a" * 256,  # Too long
            mime_type="application/pdf",
        )
    assert "name" in str(exc.value)


def test_document_base_invalid_mime_type():
    """Test invalid MIME type validation."""
    invalid_mime_types = [
        "",  # Empty
        "invalid",  # No slash
        "INVALID/PDF",  # Uppercase
        "application/",  # No subtype
        "/pdf",  # No type
        "application/pdf!",  # Invalid character
    ]
    for mime_type in invalid_mime_types:
        with pytest.raises(ValidationError) as exc:
            DocumentBase(
                name="test.pdf",
                mime_type=mime_type,
            )
        assert "mime_type" in str(exc.value)


def test_document_base_invalid_unique_name():
    """Test invalid unique name validation."""
    invalid_names = [
        "test-doc",  # Hyphen not allowed
        "test doc",  # Space not allowed
        "test@doc",  # Special char not allowed
        "test/doc",  # Slash not allowed
        "test.doc",  # Period not allowed
        "test$doc",  # Dollar sign not allowed
        "a" * 129,  # Too long
    ]
    for name in invalid_names:
        with pytest.raises(ValidationError) as exc:
            DocumentBase(
                name="test.pdf",
                mime_type="application/pdf",
                unique_name=name,
            )
        assert "unique_name" in str(exc.value)


def test_document_base_valid_unique_name():
    """Test valid unique name validation."""
    valid_names = [
        "testdoc123",  # Alphanumeric
        "test_doc_123",  # With underscores
        "a_b_c",  # Multiple underscores
        "doc_123_test",  # Underscore with numbers
    ]
    for name in valid_names:
        doc = DocumentBase(
            name="test.pdf",
            mime_type="application/pdf",
            unique_name=name,
        )
        assert doc.unique_name == name


def test_document_create_to_domain():
    """Test conversion to domain model."""
    doc = DocumentCreate(
        name="test.pdf",
        mime_type="application/pdf",
        metadata={"category": "test"},
        unique_name="test_doc_123",
        is_public=True,
    )
    domain_doc = doc.to_domain(user_id="user123")
    assert domain_doc.name == "test.pdf"
    assert domain_doc.mime_type == "application/pdf"
    assert domain_doc.metadata == {"category": "test"}
    assert domain_doc.unique_name == "test_doc_123"
    assert domain_doc.is_public is True
    assert domain_doc.user_id == "user123"


def test_document_update_valid():
    """Test valid document update schema."""
    # Test partial update
    update = DocumentUpdate(name="new.pdf")
    assert update.name == "new.pdf"
    assert update.doc_metadata is None
    assert update.is_public is None
    assert update.unique_name is None

    # Test full update
    update = DocumentUpdate(
        name="new.pdf",
        metadata={"status": "updated"},
        is_public=True,
        unique_name="new_doc_123",
    )
    assert update.name == "new.pdf"
    assert update.doc_metadata == {"status": "updated"}
    assert update.is_public is True
    assert update.unique_name == "new_doc_123"


def test_document_status_update():
    """Test document status update schema."""
    update = DocumentStatusUpdate(
        status=DocumentStatus.ACTIVE
    )
    assert update.status == DocumentStatus.ACTIVE

    with pytest.raises(ValidationError):
        DocumentStatusUpdate(status="INVALID")


def test_document_response_valid():
    """Test valid document response schema."""
    now = datetime.now(UTC)
    response = DocumentResponse(
        id=1,
        user_id="user123",
        name="test.pdf",
        mime_type="application/pdf",
        storage_url="s3://bucket/test.pdf",
        size_bytes=1024,
        status=DocumentStatus.ACTIVE,
        created_at=now,
        updated_at=now,
        metadata={"category": "test"},
        unique_name="test_doc_123",
        is_public=True,
    )
    assert response.id == 1
    assert response.user_id == "user123"
    assert response.name == "test.pdf"
    assert response.mime_type == "application/pdf"
    assert response.storage_url == "s3://bucket/test.pdf"
    assert response.size_bytes == 1024
    assert response.status == DocumentStatus.ACTIVE
    assert response.created_at == now
    assert response.updated_at == now
    assert response.doc_metadata == {"category": "test"}
    assert response.unique_name == "test_doc_123"
    assert response.is_public is True


def test_document_response_invalid_size():
    """Test invalid document size validation."""
    now = datetime.now(UTC)
    with pytest.raises(ValidationError) as exc:
        DocumentResponse(
            id=1,
            user_id="user123",
            name="test.pdf",
            mime_type="application/pdf",
            storage_url="s3://bucket/test.pdf",
            size_bytes=-1,  # Negative size not allowed
            status=DocumentStatus.ACTIVE,
            created_at=now,
        )
    assert "size_bytes" in str(exc.value)
