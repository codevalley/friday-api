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

### EPIC 4: Convert to Synchronous Operations
This epic addresses the async/sync mismatch in the document feature implementation by converting to a fully synchronous approach (except for storage operations which remain async).

#### 1. Service Layer Updates [COMPLETED]
- [x] Convert DocumentService methods to synchronous
  - [x] Identify all async methods that need conversion:
    - create_document
    - get_document
    - get_document_content
    - get_public_document
    - get_public_document_content
    - update_document
    - update_document_status
    - delete_document
  - [x] Remove async/await from service methods
  - [x] Properly wrap async storage operations in sync context using asyncio.run()
  - [x] Update method signatures and return types
  - [x] Update error handling for sync context
- [x] Update service tests
  - [x] Convert async tests to sync where appropriate
  - [x] Update mocks and fixtures
  - [x] Add tests for storage operation wrapping
  - [x] Verify error propagation in sync context

#### Service Layer Changes Summary:
1. Converted all async methods to sync in DocumentService
2. Used asyncio.run() to handle async storage operations
3. Updated test suite to use sync mocks and removed async/await
4. Maintained existing functionality while making it sync
5. Properly handled error propagation in sync context
6. Updated Pydantic model usage to V2 standards
   - Replaced deprecated from_orm with model_validate
   - Using ConfigDict for model configuration

#### Next Steps:
1. Move on to router layer updates
2. Update router tests to match sync implementation
3. Implement integration tests

#### 2. Router Layer Updates
- [ ] Convert router endpoints to synchronous
  - [ ] Remove async/await from route handlers
  - [ ] Update endpoint signatures
  - [ ] Ensure proper error handling
  - [ ] Maintain FastAPI response models
- [ ] Update router tests
  - [ ] Convert async tests to sync
  - [ ] Update test client usage
  - [ ] Verify response models
  - [ ] Test error scenarios

#### 3. Integration Testing
- [ ] Update integration tests for sync operations
  - [ ] Convert async test cases to sync
  - [ ] Test full document lifecycle
  - [ ] Verify storage operations still work
  - [ ] Test error scenarios
- [ ] Performance testing
  - [ ] Compare sync vs async performance
  - [ ] Monitor storage operation impact
  - [ ] Verify no degradation in response times

#### 4. Documentation Updates
- [ ] Update API documentation
- [ ] Update code comments
- [ ] Document sync/async boundaries
- [ ] Update development guides

### Next Actions (Sync Conversion Focus)
1. Begin Router Updates
   - Start with core CRUD operations
   - Handle storage operations carefully
   - Update tests as we go
   - Verify each method works before moving on

2. Move to Integration Testing
   - Run full test suite
   - Fix any issues
   - Document performance impacts

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
