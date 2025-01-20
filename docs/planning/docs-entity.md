# Document Management System

This document outlines the implementation approach for the Document Management System, which will handle document storage, retrieval, and metadata management in our application.

## Key Design Decisions

### Storage Abstraction
- Implement a storage abstraction layer to decouple storage implementation from business logic
- Support multiple storage backends (local filesystem initially, cloud storage in future)
- Use URL-based addressing for document locations
- Handle storage operations asynchronously when appropriate

### Document States
```python
class DocumentStatus(str, Enum):
    PENDING = "pending"      # Document is being uploaded
    ACTIVE = "active"        # Document is available
    ARCHIVED = "archived"    # Document is archived (soft-deleted)
    ERROR = "error"          # Error in document processing
```

### Storage Interface
```python
class StorageBackend(Protocol):
    async def store(self, file: UploadFile, user_id: str) -> str:
        """Store a file and return its URL"""
        ...

    async def retrieve(self, url: str, user_id: str) -> BytesIO:
        """Retrieve a file by its URL"""
        ...

    async def delete(self, url: str, user_id: str) -> None:
        """Delete a file"""
        ...
```

## Implementation Stages

### Stage 1: Core Document Entity
1. Create document domain model with basic metadata
   - Created DocumentData class with validation and data conversion methods
   - Added DocumentStatus enum for state management
   - Added document-related exceptions
2. Implement database schema and ORM
   - Created Document ORM model with SQLAlchemy
   - Added relationship to User model
   - Set up proper indexes and constraints
3. Set up basic CRUD operations
   - Created DocumentRepository with standard CRUD operations
   - Added user-specific document queries
   - Added status management and storage URL lookup
   - Added utility for tracking user storage usage
4. Create API endpoints
   - Created Pydantic schemas for requests/responses
   - Added DocumentService for business logic
   - Created DocumentRouter with endpoints for:
     - Document upload and creation
     - Listing and filtering documents
     - Updating document metadata and status
     - Deleting documents
     - Getting storage usage statistics

### Stage 2: Storage System
1. Design storage domain model
   - Created IStorageService interface
   - Added StoredFile domain model
   - Added domain-specific exceptions
   - Defined storage status states
2. Implement storage infrastructure
   - Created LocalStorageService implementation
   - Added MockStorageService for testing
   - Implemented StorageFactory following DI principles
   - Added async file operations
3. Add storage configuration
   - Environment variable support
   - Factory pattern for backend creation
   - Testing utilities
4. Integrate with document metadata
   - Update document service to use IStorageService
   - Add file upload/download handlers
   - Implement file cleanup on document deletion

### Stage 3: Advanced Features
1. Add mime-type detection and validation
2. Implement file size limits and quotas
3. Add document versioning support
4. Implement bulk operations

---

## Tasks & Progress

### EPIC 1: Document Entity Implementation

#### 1. Domain Layer 
- [x] Create `DocumentData` class with:
  - Basic metadata (name, storage_url, mime_type, size_bytes)
  - User ownership
  - Status tracking
  - Optional metadata dictionary
  - Timestamps (created_at, updated_at)
  - Public access fields (unique_name, is_public)
- [x] Implement validation logic
  - Field presence and format validation
  - Status transition validation
  - User ownership validation
  - Unique name format validation
- [x] Add domain exceptions
  - DocumentValidationError
  - DocumentStatusError
  - DocumentStorageError

#### 2. Database Layer 
- [x] Create Document ORM model
  - SQLAlchemy model with proper columns
  - Relationship with User model
  - Conversion methods to/from domain model
- [x] Add indexes for efficient queries
  - User ID index
  - Status index
  - Unique name index
  - Public access index
- [x] Set up cascade deletes for cleanup

#### 3. Repository Layer 
- [x] Implement CRUD operations
- [x] Add user-specific queries
- [x] Add status management
- [x] Add public access queries

#### 4. Service Layer 
- [x] Create DocumentService
- [x] Implement business logic
- [x] Add authorization checks
- [x] Handle error cases
- [x] Implement public access logic

#### 5. API Layer 
- [x] Create Pydantic schemas
- [x] Implement API endpoints
  - [x] Document upload
  - [x] Document retrieval (by ID and unique name)
  - [x] Document update
  - [x] Document deletion
  - [x] Public access endpoints
- [x] Add file upload handling
- [x] Add filtering and pagination
- [ ] Add response compression
- [ ] Handle concurrent access

#### 6. Storage Layer 
- [x] Create storage domain model
  - IStorageService interface
  - StoredFile domain model
  - Storage-specific exceptions
- [x] Implement storage infrastructure
  - LocalStorageService for file system
  - MockStorageService for testing
  - S3StorageService for cloud storage
  - StorageFactory for DI
- [x] Integrate with DocumentService
  - Async file operations
  - Error handling
  - File cleanup on deletion
- [x] Add storage configuration
  - Environment variables
  - File size limits
  - Allowed MIME types

### EPIC 2: Storage System Implementation 
- [x] Design storage abstraction layer
- [x] Implement local filesystem backend
- [x] Add S3-compatible backend
- [ ] Add Azure Blob Storage backend
- [ ] Add Google Cloud Storage backend

### EPIC 3: Testing Suite
- [ ] Unit Tests
  - [x] Domain model tests
    - [x] Document creation and validation
    - [x] Status transitions
    - [x] Public access rules
    - [x] Metadata validation
    - [x] Access control
  - [ ] Repository tests
  - [ ] Service tests
  - [x] Storage tests
    - [x] Local storage implementation
    - [x] Mock storage for testing
    - [x] S3 storage implementation
- [ ] Integration Tests
  - [ ] API endpoint tests
  - [ ] Storage integration tests
  - [ ] Public access tests

### EPIC 4: Documentation 
- [x] API Documentation
  - [x] Endpoint descriptions
  - [x] Request/response schemas
  - [x] Authentication requirements
- [x] Storage Configuration
  - [x] Environment variables
  - [x] S3 setup guide
  - [x] Local storage setup
- [x] Development Guide
  - [x] Project structure
  - [x] Database setup
  - [x] Testing guide

### EPIC 5: Testing Implementation

#### 1. Test Infrastructure Setup
##### Environment Configuration
- [x] Update `__tests__/conftest.py`
  - [x] Add storage fixtures:
    ```python
    @pytest.fixture
    def storage_service():
        """Create a mock storage service for testing."""
        return Mock(spec=IStorageService)

    @pytest.fixture
    def local_storage_service(tmp_path):
        """Create a real local storage service for integration tests."""
        return LocalStorageService(base_path=tmp_path)

    @pytest.fixture
    def s3_storage_service():
        """Create a mocked S3 storage service using moto."""
        with mock_s3():
            # Set up mock S3
            s3 = boto3.client('s3')
            s3.create_bucket(Bucket='test-bucket')
            yield S3StorageService(
                bucket_name='test-bucket',
                endpoint_url='http://localhost:4566'
            )
    ```
  - [x] Add document fixtures:
    ```python
    @pytest.fixture
    def sample_document(test_db_session, sample_user):
        """Create a sample document for testing."""
        doc = Document(
            name="Test Document",
            storage_url="/test/path",
            mime_type="text/plain",
            size_bytes=100,
            user_id=sample_user.id,
            status="ACTIVE"
        )
        test_db_session.add(doc)
        test_db_session.commit()
        return doc

    @pytest.fixture
    def sample_public_document(test_db_session, sample_user):
        """Create a sample public document."""
        doc = Document(
            name="Public Document",
            storage_url="/public/path",
            mime_type="text/plain",
            size_bytes=100,
            user_id=sample_user.id,
            status="ACTIVE",
            is_public=True,
            unique_name="test-doc"
        )
        test_db_session.add(doc)
        test_db_session.commit()
        return doc
    ```

##### Test Dependencies
- [x] Add to `setup.py`:
  ```python
  install_requires=[
      # ... existing dependencies ...
      "moto[s3]>=4.0.0",  # For S3 mocking
      "pytest-asyncio>=0.14.0",  # Already included
      "pytest-env>=1.0.0",  # For environment variables
  ]
  ```

##### Test Files Setup
- [x] Create test file structure:
  ```
  __tests__/
  ├── fixtures/
  │   └── test_files/
  │       ├── test.txt
  │       └── test.pdf
  ├── integration/
  │   ├── test_storage_integration.py
  │   └── test_document_integration.py
  └── unit/
      ├── domain/
      │   └── test_document.py
      ├── infrastructure/
      │   └── test_storage.py
      ├── repositories/
      │   └── test_document_repository.py
      ├── routers/
      │   └── test_document_router.py
      └── services/
          └── test_document_service.py
  ```

### Next Actions
1. Start with domain model tests in `__tests__/unit/domain/test_document.py`
2. Create test file structure
3. Add storage and document fixtures to `__tests__/conftest.py`

### Dependencies
From `setup.py`:
- pytest-asyncio (already included)
- httpx (already included)
New additions needed:
- moto[s3] for S3 mocking
- localstack for S3 integration
- pytest-env for environment variables

### Test Implementation Steps
1. Infrastructure Setup (1-2 days)
   - Update configuration
   - Create fixtures
   - Set up mocks

2. Unit Tests (2-3 days)
   - Start with domain tests
   - Add repository tests
   - Implement service tests
   - Create router tests

3. Integration Tests (2-3 days)
   - Storage integration
   - Document flow tests
   - Error scenario tests

4. E2E Tests (1-2 days)
   - Update test_flow.sh
   - Test all scenarios
   - Document test cases
