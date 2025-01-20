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
1. ✅ Create document domain model with basic metadata
   - Created DocumentData class with validation and data conversion methods
   - Added DocumentStatus enum for state management
   - Added document-related exceptions
2. ✅ Implement database schema and ORM
   - Created Document ORM model with SQLAlchemy
   - Added relationship to User model
   - Set up proper indexes and constraints
3. ✅ Set up basic CRUD operations
   - Created DocumentRepository with standard CRUD operations
   - Added user-specific document queries
   - Added status management and storage URL lookup
   - Added utility for tracking user storage usage
4. ✅ Create API endpoints
   - Created Pydantic schemas for requests/responses
   - Added DocumentService for business logic
   - Created DocumentRouter with endpoints for:
     - Document upload and creation
     - Listing and filtering documents
     - Updating document metadata and status
     - Deleting documents
     - Getting storage usage statistics

### Stage 2: Storage System
1. Design storage abstraction layer
2. Implement local filesystem backend
3. Add file upload/download handlers
4. Integrate with document metadata

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
- [x] Implement validation logic
  - Field presence and format validation
  - Status transition validation
  - User ownership validation
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
- [x] Set up cascade deletes for cleanup

#### 3. Repository Layer
- [x] Implement CRUD operations
- [x] Add user-specific queries
- [x] Add status management
- [x] Add storage usage tracking

#### 4. Service Layer
- [x] Create DocumentService
- [x] Implement business logic
- [x] Add authorization checks
- [x] Handle error cases

#### 5. API Layer
- [x] Create Pydantic schemas
- [x] Implement API endpoints
- [x] Add file upload handling
- [x] Add filtering and pagination
- [ ] Add response compression
- [ ] Handle concurrent access

#### 6. Storage Configuration
- [ ] Add environment variables
- [ ] Create configuration class
- [ ] Implement storage interface
- [ ] Add local filesystem backend

### EPIC 2: Storage System Implementation

#### 1. Local Storage Backend
- [ ] Design directory structure
- [ ] Implement file operations
- [ ] Add cleanup utilities
- [ ] Handle concurrent access

#### 2. Storage Configuration
- [ ] Add environment variables
- [ ] Create configuration class
- [ ] Implement storage factory
- [ ] Add storage utilities

### Testing Strategy

#### 1. Unit Tests
- [ ] Domain model validation
- [ ] Storage operations
- [ ] Repository operations
- [ ] Service layer logic

#### 2. Integration Tests
- [ ] File upload/download flow
- [ ] Storage backend integration
- [ ] Database operations
- [ ] API endpoints

#### 3. Performance Tests
- [ ] Large file handling
- [ ] Concurrent operations
- [ ] Storage space management
