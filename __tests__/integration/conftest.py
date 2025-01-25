"""Test fixtures for integration tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.orm import Session

from repositories.DocumentRepository import (
    DocumentRepository,
)
from services.DocumentService import DocumentService
from infrastructure.storage.local import LocalStorageService
from domain.storage import IStorageService


@pytest.fixture
def local_storage_service() -> LocalStorageService:
    """Create a mocked local storage service."""
    storage = MagicMock(spec=LocalStorageService)

    # Create a mock store object that returns actual values
    mock_store = MagicMock()
    mock_store.path = "/test/path/file.txt"
    mock_store.size_bytes = 1024

    # Mock async methods with proper async return values
    storage.get = AsyncMock(return_value=b"test content")
    storage.put = AsyncMock(return_value=mock_store)
    storage.store = AsyncMock(return_value=mock_store)
    storage.delete = AsyncMock(return_value=True)

    return storage


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
