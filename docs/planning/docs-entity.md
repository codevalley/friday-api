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

### EPIC 2: Storage System Implementation
- [x] Design storage abstraction layer
- [x] Implement local filesystem backend
- [x] Add S3-compatible backend

### EPIC 3: Testing Suite (Current Priority)
- [x] Unit Tests
  - [x] Domain model tests
    - [x] Document creation and validation
    - [x] Status transitions
    - [x] Public access rules
    - [x] Metadata validation
    - [x] Access control
  - [x] Repository tests
    - [x] CRUD operations
    - [x] User-specific queries
    - [x] Status management
    - [x] Public access queries
  - [x] Service tests
    - [x] Business logic validation
    - [x] Authorization checks
    - [x] Error handling
    - [x] Public access logic
    - [x] Storage integration
  - [x] Storage tests
    - [x] Local storage implementation
    - [x] Mock storage for testing
    - [x] S3 storage implementation
- [ ] Integration Tests
  - [ ] API endpoint tests
    - [ ] Document upload/download flow
    - [ ] Document management operations
    - [ ] Error scenarios
  - [ ] Storage integration tests
    - [ ] File operations
    - [ ] Cleanup procedures
  - [ ] Public access tests
    - [ ] Access control
    - [ ] URL generation and validation

### EPIC 4: Convert to Synchronous Operations [MOSTLY COMPLETE]

#### 1. Service Layer Updates [COMPLETED ✓]
- [x] Convert DocumentService methods to synchronous
- [x] Update service tests
- [x] Handle async storage operations properly
- [x] Update error handling

#### 2. Router Layer Updates [COMPLETED ✓]
- [x] Convert router endpoints to synchronous
- [x] Update endpoint signatures
- [x] Ensure proper error handling
- [x] Maintain FastAPI response models
- [x] Update router tests

#### 3. Integration Testing [IN PROGRESS]
- [ ] Complete end-to-end document lifecycle tests
  - [ ] Upload flow
  - [ ] Download flow
  - [ ] Update operations
  - [ ] Delete operations
  - [ ] Public access flows
- [ ] Storage integration verification
  - [ ] Test file storage operations
  - [ ] Verify cleanup procedures
  - [ ] Test concurrent access patterns
- [ ] Error scenario testing
  - [ ] Invalid uploads
  - [ ] Permission errors
  - [ ] Storage failures
  - [ ] Cleanup failures

#### 4. Documentation & Cleanup [NEXT UP]
- [ ] Update API documentation
  - [ ] Document new endpoint structures
  - [ ] Update request/response examples
  - [ ] Document error scenarios
- [ ] Code cleanup
  - [ ] Remove unused async/await
  - [ ] Standardize error handling
  - [ ] Clean up imports
- [ ] Update development guides
  - [ ] Document testing approach
  - [ ] Add troubleshooting guide
  - [ ] Update setup instructions

### Next Actions (Priority Order)
1. Complete Integration Tests
   - Focus on document lifecycle flows
   - Add error scenario coverage
   - Test storage operations thoroughly

2. Documentation Updates
   - Update API documentation
   - Add integration test guide
   - Document common issues/solutions

3. Final Review & Cleanup
   - Code review for consistency
   - Remove any remaining async/await
   - Update type hints
   - Verify error handling

4. Performance Verification
   - Load testing
   - Concurrent operation testing
   - Storage operation benchmarks

### Future Enhancements
1. Performance Testing
   - Load testing for concurrent uploads
   - Storage backend benchmarks
   - API endpoint performance
2. Security Testing
   - Access control testing
   - File validation
   - Rate limiting
3. Additional Storage Backends
   - Azure Blob Storage
   - Google Cloud Storage
