"""Test fixtures for integration tests."""

import pytest
from sqlalchemy.orm import Session

from repositories.DocumentRepository import (
    DocumentRepository,
)
from services.DocumentService import DocumentService
from infrastructure.storage.mock_sync import (
    MockStorageService,
)
from domain.storage import IStorageService


@pytest.fixture
def storage_service() -> IStorageService:
    """Create a mock storage service."""
    return MockStorageService()


@pytest.fixture
def document_service(
    storage_service: IStorageService,
    test_db_session: Session,
) -> DocumentService:
    """Create a document service with mocked dependencies."""
    repository = DocumentRepository(test_db_session)
    return DocumentService(
        repository=repository, storage=storage_service
    )
