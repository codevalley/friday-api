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
  - [ ] Domain model tests
  - [ ] Repository tests
  - [ ] Service tests
  - [ ] Storage tests
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

### Next Steps
1. Implement comprehensive test suite
2. Add response compression for large files
3. Implement concurrent access handling
4. Add support for more cloud storage providers
