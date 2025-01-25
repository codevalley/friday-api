# Storage and Document Feature Sync Refactor

This document outlines the plan for converting the storage and document features from a mixed async/sync implementation to a consistent pattern where:
- FastAPI routes remain async (consistent with other routes in the codebase)
- All business logic and I/O operations (services, repositories, storage) are synchronous

## Current Issues

1. Inconsistent async/sync patterns across the storage and document features
2. Mixed usage of async/sync methods leading to potential runtime issues
3. Complexity in handling async operations in storage implementations

## Design Goals

1. **Consistency**: Follow the established pattern in the codebase where:
   - Routes are async (like NoteRouter, TaskRouter)
   - Services, repositories, and storage operations are sync
2. **Performance**: Maintain efficient I/O operations through:
   - Chunked file reading/writing
   - Proper stream handling for large files
3. **Simplicity**: Reduce complexity by:
   - Removing mixed async/sync patterns
   - Using straightforward synchronous I/O operations
4. **Maintainability**: Improve code quality through:
   - Consistent patterns across features
   - Better testability with sync operations
   - Clear separation of concerns

## Implementation Progress

### Phase 1: Storage Layer 

1. Update Storage Interface 
   - Converted `IStorageService` methods to sync
   - Changed `AsyncIterator[bytes]` to `BinaryIO`
   - Updated method signatures and docstrings

2. Update Local Storage Implementation 
   - Removed `aiofiles` dependency
   - Implemented sync file operations with chunked reading
   - Maintained efficient large file handling using `BytesIO`
   - Added proper cleanup in delete operations
   - Added metadata handling for file ownership and permissions
   - Added unit tests for permission handling and file access
   - Fixed permission verification in `_verify_user_access`
   - Improved file search in `get_metadata` to look across all user directories
   - Added metadata file storage for MIME types and creation times
   - Implemented proper cleanup of metadata files during deletion
   - All unit tests passing including permission checks and error cases

3. Update Storage Implementations 
   - S3 Storage 
     - Created new sync implementation using boto3
     - Implemented user directory structure for file isolation
     - Added metadata file handling for ownership and permissions
     - Added proper error handling for S3-specific cases
     - Implemented efficient file streaming with BytesIO
     - Added permission checks consistent with local storage
     - Fixed error message format in file operations
     - Improved error handling for metadata file operations
     - Added consistent error messages across implementations
     - All unit tests passing with good coverage
   - Mock Storage 
     - Created new sync implementation
     - Added proper permission checks matching other implementations
     - Enhanced error simulation capabilities
     - Improved file search in get_metadata
     - Added efficient file streaming with BytesIO
   - Unit Tests 
     - Added tests for S3 storage implementation:
       - File operations (store, retrieve, delete)
       - Permission handling and access control
       - Error handling (not found, permissions, S3 errors)
       - Metadata operations and validation
       - S3 client stubbing for reproducible tests
     - Added tests for mock storage implementation:
       - Basic file operations
       - Permission checks and error handling
       - Error simulation capabilities
       - Metadata validation
     - All tests passing and providing good coverage

4. Additional Tasks 
   - Added performance considerations section
   - Documented memory handling for large files
   - Added examples of sync usage in docstrings
   - Removed unused dependencies
   - Fixed all linting issues (flake8)
   - Improved code organization and readability

### Phase 2: Repository Layer 

1. Document Repository 
   - Repository layer was already synchronous
   - All methods use standard SQLAlchemy operations
   - Proper transaction handling in place
   - Consistent error handling with storage layer
   - All repository tests passing

2. Integration with Storage 
   - Converted DocumentService to use sync storage operations
   - Removed all async/await keywords
   - Simplified file upload logic to use sync operations
   - Maintained proper error handling and transaction management
   - Improved code organization and readability

3. Testing Requirements 
   - Repository tests already in place and passing
   - Storage integration tests passing
   - Error handling tests in place
   - Transaction rollback tests working

4. Documentation Updates 
   - Updated implementation progress
   - Documented sync operations
   - Added examples of repository usage
   - Documented transaction handling

### Phase 3: Service Layer 

1. Document Service 
   - Converted all async methods to sync
   - Updated service-repository interaction
   - Simplified file handling operations
   - Maintained proper error handling

2. Activity Service 
   - Reviewed async operations
   - QueueService interface already synchronous
   - No changes needed

3. Note Service 
   - Reviewed async operations
   - QueueService interface already synchronous
   - No changes needed

4. OpenAI Service 
   - Reviewed client operations
   - OpenAI client already synchronous
   - No changes needed

5. Service Tests 
   - All tests passing with sync operations
   - Error propagation verified
   - Transaction handling confirmed

### Phase 4: API Layer 

1. Router Design 
   - Keep FastAPI endpoints async for better performance
   - Maintain consistency with other routers (NoteRouter, TaskRouter)
   - Service layer remains synchronous
   - No changes needed to router implementations

2. Integration Points 
   - Service layer calls are sync
   - FastAPI dependency injection working correctly
   - Error handling preserved
   - Transaction management working

3. Documentation Updates 
   - Added notes about async/sync architecture
   - Documented service layer changes
   - Updated API documentation
   - Added examples of router usage

### Implementation Complete 

The sync refactoring project is now complete with all phases implemented:

1. Phase 1: Storage Layer 
   - Converted S3 operations to sync
   - Updated mock storage implementation
   - Added comprehensive tests
   - Improved error handling

2. Phase 2: Repository Layer 
   - Repository layer already synchronous
   - Added proper transaction handling
   - Updated documentation
   - All tests passing

3. Phase 3: Service Layer 
   - Converted document service to sync
   - Other services already synchronous
   - Updated error handling
   - Added comprehensive tests
   - Added missing count_documents method
   - Fixed validation for unique_name field

4. Phase 4: API Layer 
   - Kept FastAPI endpoints async
   - Service layer fully synchronous
   - Consistent with other routers
   - Documentation updated
   - Fixed route conflicts for public documents
   - Updated test assertions for pagination response

### Testing Status

1. Unit Tests
   - DocumentService tests passing
   - DocumentRepository tests passing
   - Storage implementation tests passing:
     - File operations (store, retrieve, delete)
     - Metadata handling (MIME types, creation times)
     - Permission checks and access control
     - Error handling and edge cases
   - All linter errors addressed

2. Integration Tests
   - Document router tests passing:
     - Document upload with proper MIME type handling
     - Document listing with pagination
     - Document retrieval with correct metadata
     - Document updates
     - Document deletion (including metadata cleanup)
     - Storage usage
     - Public document access
   - Storage integration tests passing
   - Error handling verified
   - Transaction management confirmed

3. Remaining Tasks
   - Review and update DocumentService unit tests
   - Add more integration tests for edge cases
   - Add performance tests for large file operations
   - Document testing strategy and coverage

### Architecture Overview

The final architecture follows these principles:

1. FastAPI Endpoints:
   - Remain async for optimal performance
   - Handle HTTP concerns and request/response formatting
   - Use dependency injection for services

2. Service Layer:
   - Fully synchronous implementation
   - Handles business logic and orchestration
   - Manages transactions and error handling

3. Repository Layer:
   - Synchronous database operations
   - Handles data persistence
   - Manages entity relationships

4. Storage Layer:
   - Synchronous file operations
   - Efficient streaming for large files
   - Proper error handling

This architecture provides:
- Clear separation of concerns
- Consistent error handling
- Efficient resource usage
- Maintainable codebase

## Implementation Approach

1. **File Storage Pattern**
   - Store files in user-specific directories: `/<storage_root>/<user_id>/<file_id>`
   - Maintain metadata files alongside content: `/<storage_root>/<user_id>/<file_id>.meta`
   - Metadata includes: owner_id, mime_type, created_at, and other file properties

2. **Permission Handling**
   - Files are private by default, accessible only by owner
   - Use metadata to track file ownership
   - Check permissions before file operations
   - Support public file access through explicit owner_id parameter

3. **Testing Strategy**
   - Test file operations: store, retrieve, delete
   - Test permission scenarios: owner access, unauthorized access
   - Test error cases: file not found, permission denied
   - Use temporary directories for test isolation

4. **Best Practices**
   - Always clean up resources (close file handles)
   - Use chunked reading for large files
   - Validate inputs before operations
   - Handle all error cases explicitly
   - Document public interfaces thoroughly

## Performance Considerations

### Memory Management
1. **Chunked File Operations**
   - Files are read and written in chunks to minimize memory usage
   - Default chunk size is 8MB, configurable based on system resources
   - Prevents memory exhaustion when handling large files

2. **Streaming Data**
   - All storage implementations use `BinaryIO` for file operations
   - Data is streamed directly from source to destination
   - No need to load entire file into memory
   - Efficient for both small and large files

3. **Metadata Handling**
   - Metadata files are small JSON documents stored alongside content
   - Loaded into memory only when needed
   - Cached when appropriate to reduce I/O operations

### S3 Storage Optimizations
1. **Directory Structure**
   - Files organized by user: `/<user_id>/<file_id>`
   - Metadata files: `/<user_id>/<file_id>.meta`
   - Efficient for listing user files and checking permissions

2. **Error Handling**
   - Early metadata checks prevent unnecessary file transfers
   - Permission checks done before file operations
   - Proper error propagation for client handling

3. **Connection Management**
   - Reuse boto3 client connections
   - Proper error handling for connection issues
   - Retries with exponential backoff for transient failures

### Local Storage Optimizations
1. **File System Organization**
   - Mirror S3 directory structure for consistency
   - Efficient local file operations using native OS calls
   - Proper cleanup of temporary files

2. **Resource Management**
   - File handles properly closed after operations
   - Temporary files cleaned up even after errors
   - System resources released promptly

## Memory Handling for Large Files

### File Upload Process
1. Client sends file in chunks
2. Each chunk is processed and written directly to storage
3. No complete file loaded into memory
4. Progress tracking available for large uploads

### File Download Process
1. File retrieved in chunks from storage
2. Each chunk streamed directly to client
3. Memory usage remains constant regardless of file size
4. Support for range requests and resumable downloads

### Error Recovery
1. Failed uploads can be resumed
2. Partial downloads can be continued
3. Temporary resources cleaned up properly
4. System remains stable even with multiple large files

## Usage Examples

### Storing Large Files
```python
# Efficient file upload
with open("large_file.dat", "rb") as f:
    storage.store(
        file_data=f,
        file_id="large_file.dat",
        user_id="user123",
        mime_type="application/octet-stream"
    )

# File is streamed in chunks, memory usage stays constant
```

### Retrieving Large Files
```python
# Efficient file download
file_obj = storage.retrieve(
    file_id="large_file.dat",
    user_id="user123"
)

# Stream chunks to client
for chunk in iter(lambda: file_obj.read(8192), b""):
    yield chunk
```

### Error Handling
```python
try:
    file_obj = storage.retrieve(
        file_id="nonexistent.txt",
        user_id="user123"
    )
except FileNotFoundError:
    # Handle missing file
except StoragePermissionError:
    # Handle permission error
except StorageError:
    # Handle other storage errors
```

## Testing Strategy

1. Unit Tests
   - Convert async tests to sync
   - Add specific tests for chunked operations
   - Verify error handling

2. Integration Tests
   - Test file upload/download flows
   - Verify proper cleanup of resources
   - Test concurrent operations

3. Performance Tests
   - Benchmark file operations
   - Test with various file sizes
   - Measure memory usage

## Migration Steps

1. Create feature branch `feature/sync-storage-refactor`
2. Implement changes phase by phase
3. Run comprehensive tests after each phase
4. Update documentation
5. Conduct code review
6. Merge to main branch

## Rollback Plan

1. Keep original async implementations in separate files until testing is complete
2. Maintain ability to switch back to async implementation if issues are discovered
3. Document all changes for easy rollback if needed

## Success Criteria

1. All tests passing
2. No performance degradation
3. Improved code maintainability
4. Consistent patterns across codebase
5. Proper handling of large files
6. Clean error handling
7. Updated documentation

## Future Considerations

1. Monitor performance in production
2. Consider adding caching layer if needed
3. Plan for future scaling requirements
4. Regular review of file operation patterns

### Recent Updates

1. Schema Layer
   - Added comprehensive schema validation:
     - Proper MIME type pattern validation
     - Consistent unique_name validation across schema and domain
     - Enhanced field descriptions and examples
     - Fixed metadata field aliasing
     - Added size validation for DocumentResponse
   - Added schema tests covering:
     - Base schema validation
     - Default values
     - Field constraints
     - Domain model conversion
     - Update schema validation
     - Status update validation
     - Response schema validation
     - Invalid cases for each field

2. Domain Model
   - Updated unique_name validation to match schema:
     - Changed from isalnum() to regex pattern
     - Now allows alphanumeric characters and underscores
     - Improved error messages for validation failures
   - All domain model tests passing

### Next Steps

1. Integration Tests
   - Add tests for:
     - File upload with various sizes
     - MIME type validation
     - Unique name validation
     - Public document access
     - Permission checks
     - Error handling scenarios
     - Transaction rollback cases
   - Test coverage goals:
     - Storage operations: 90%
     - Repository operations: 90%
     - Service layer: 85%
     - API endpoints: 80%

2. Performance Testing
   - Add tests for:
     - Large file uploads (>50MB)
     - Concurrent access
     - Public document retrieval
     - Document listing with pagination
   - Measure and document:
     - Response times
     - Memory usage
     - CPU utilization

3. Documentation
   - Add API documentation:
     - Request/response examples
     - Error scenarios
     - Authentication requirements
     - Rate limiting
   - Update schema documentation:
     - Field constraints
     - Validation rules
     - Example payloads

4. Final Review
   - Code quality check
   - Test coverage analysis
   - Performance metrics review
   - Documentation completeness
   - Security review

### Testing Strategy

1. Unit Tests
   - Schema validation
   - Domain model validation
   - Service layer business logic
   - Repository operations
   - Storage implementations

2. Integration Tests
   - API endpoints
   - Service-repository interaction
   - Storage operations
   - Error handling
   - Transaction management

3. Performance Tests
   - Load testing
   - Stress testing
   - Endurance testing
   - Scalability testing

4. Security Tests
   - Authentication
   - Authorization
   - Input validation
   - Error handling
   - File access controls
