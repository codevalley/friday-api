# Testing Strategy

## Overview

The project implements a comprehensive testing strategy that covers all layers of the clean architecture. Tests are organized in the `__tests__` directory and use pytest as the test runner along with unittest for assertions.

## Test Structure

```
__tests__/
├── unit/
│   ├── test_models/
│   ├── test_services/
│   └── test_repositories/
├── integration/
│   ├── test_api/
│   └── test_database/
├── conftest.py
└── fixtures/
```

## Test Types

### 1. Unit Tests

```python
# __tests__/unit/test_services/test_book_service.py
class TestBookService:
    def test_create_book(self, mock_repository):
        # Arrange
        service = BookService(mock_repository)
        book_data = {"title": "Test Book"}
        
        # Act
        result = service.create_book(book_data)
        
        # Assert
        assert result.title == "Test Book"
        mock_repository.create.assert_called_once_with(book_data)
```

### 2. Integration Tests

```python
# __tests__/integration/test_api/test_book_routes.py
class TestBookRoutes:
    async def test_create_book(self, client, db_session):
        # Arrange
        book_data = {"title": "New Book", "description": "Test"}
        
        # Act
        response = await client.post("/api/v1/books", json=book_data)
        
        # Assert
        assert response.status_code == 200
        assert response.json()["title"] == "New Book"
```

## Test Configuration

### 1. Fixtures

```python
# __tests__/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def db_session():
    """Provides a clean database session for each test"""
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
def mock_repository():
    """Provides a mock repository for unit tests"""
    return Mock(spec=RepositoryMeta)
```

### 2. Environment Setup

```python
# .env.test
DATABASE_URL=sqlite:///./test.db
DEBUG_MODE=false
TESTING=true
```

## Testing Layers

### 1. Domain Layer Tests

```python
# __tests__/unit/test_models/test_book_model.py
def test_book_model_creation():
    book = BookModel(title="Test Book")
    assert book.title == "Test Book"
    assert book.authors == []
```

### 2. Service Layer Tests

```python
# __tests__/unit/test_services/test_author_service.py
async def test_get_author_not_found(service, mock_repository):
    mock_repository.get_by_id.return_value = None
    with pytest.raises(NotFoundException):
        await service.get_author(999)
```

### 3. Repository Layer Tests

```python
# __tests__/unit/test_repositories/test_book_repository.py
async def test_create_book(db_session):
    repository = BookRepository(db_session)
    book = await repository.create({"title": "Test"})
    assert book.id is not None
    assert book.title == "Test"
```

## Test Coverage

```ini
# .coveragerc
[run]
source = .
omit = 
    __tests__/*
    venv/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
```

## Best Practices

1. **Test Organization**
   - Clear test hierarchy
   - Separate unit and integration tests
   - Well-defined fixtures

2. **Test Isolation**
   - Independent test cases
   - Clean database state
   - Mocked external dependencies

3. **Coverage Goals**
   - High test coverage
   - Critical path testing
   - Edge case handling

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov-report xml --cov .

# Run specific test file
pytest __tests__/unit/test_services/test_book_service.py

# Run tests with specific marker
pytest -m "integration"
```

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: |
          pip install pipenv
          pipenv install --dev
      - name: Run tests
        run: |
          pipenv run pytest --cov-report xml --cov .
``` 