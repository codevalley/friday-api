# Tasks Feature Implementation Plan

## Development Workflow
1. Pick the next incomplete task from the plan (tasks are ordered by dependency)
2. Implement the task following the established patterns from Notes/Moments/Activities
3. Write tests before or alongside the implementation (TDD preferred)
4. Mark the task as complete (✓) and add implementation details/comments
5. Run all tests to ensure no regressions
6. Move to the next task

## Overview
This plan outlines the implementation of a new `Task` entity following the established four-layer architecture pattern (Domain → Repository → Service → Router) used in the existing codebase for Notes, Moments, and Activities.

A Task represents a user-created item that needs to be completed, with properties like title, description, priority, status, created date, due date, and optional tags, parent task.

## Core Features
- Users can create, read, update, and delete tasks
- Tasks have a title, description, status (todo/in-progress/done), due date
- Tasks belong to a user (similar to Notes)
- Tasks can be listed with pagination
- Tasks can be filtered by status and due date
- Basic validation rules for task properties

## Implementation Plan

### Epic 1: Core Domain & Data Layer
**Goal**: Implement the foundational domain model and database layer for Tasks

#### Task 1.1: Domain Implementation ✓
- [x] Create `domain/task.py`
  - [x] 1.1.1 Implement the core domain model class (TaskData)
  - [x] 1.1.2 Add validation rules (title constraints, status fields, due date checks)
  - [x] 1.1.3 Add task-specific exceptions to `domain/exceptions.py`
  - [x] 1.1.4 Add TaskStatus and TaskPriority enums in `domain/values.py`

Implementation Details:
- Created TaskData with fields: title, description, user_id, status, priority, due_date, tags, parent_id
- Added validation for all fields including due_date > created_at check
- Implemented status transitions (todo → in_progress → done)
- Added support for task priorities (LOW, MEDIUM, HIGH, URGENT)
- Added support for tags and parent tasks (hierarchical structure)
- Added comprehensive unit tests in `__tests__/unit/domain/test_task_data.py`

#### Task 1.2: ORM Model ✓
- [x] Create `orm/TaskModel.py`
  - [x] 1.2.1 Define SQLAlchemy model fields mirroring domain
  - [x] 1.2.2 Set up relationship with User model (foreign key: user_id)
  - [x] 1.2.3 Add indexes and constraints for status, due_date

Implementation Details:
- Created Task ORM model with all necessary fields (title, description, status, priority, due_date, tags, parent_id)
- Added relationships (owner -> User, subtasks -> self-referential)
- Added database constraints (non-empty title/description, no self-referential parent)
- Added indexes on id, user_id, status, and due_date
- Added TaskStatus and TaskPriority as SQLAlchemy Enums
- Updated User model to include tasks relationship
- Updated BaseModel initialization to include Task model

#### Task 1.3: Repository Layer ✓
- [x] Create `repositories/TaskRepository.py`
  - [x] 1.3.1 Implement `TaskRepository` extending `BaseRepository`
  - [x] 1.3.2 Add create/read/update/delete methods, ensuring consistent patterns with `NoteRepository`
  - [x] 1.3.3 Implement filtering and pagination support

Implementation Details:
- Created TaskRepository extending BaseRepository
- Added task-specific methods: create_task, list_user_tasks, count_user_tasks, get_subtasks, update_task_status
- Implemented filtering by status, priority, due date, and parent task
- Added support for subtasks with parent task validation
- Added ordering by priority and due date

#### Task 1.4: Tests for Domain & Repository ✓
- [x] Create `__tests__/unit/domain/test_task_data.py`
  - [x] 1.4.1 Test domain validations and exceptions
  - [x] 1.4.2 Test edge cases, empty title, invalid status, etc.
- [x] Create `__tests__/unit/repositories/test_task_repository.py`
  - [x] 1.4.3 Test repository CRUD operations
  - [x] 1.4.4 Ensure foreign key constraints and user_id references are validated

Implementation Details:
- Added comprehensive tests for TaskData validation and exceptions
- Added tests for TaskRepository covering all CRUD operations
- Added tests for task filtering, pagination, and subtask management
- Added tests for status transitions and parent task validation
- Ensured test coverage matches existing entities

### Epic 2: Service Layer & Business Logic ✓
**Goal**: Implement the service layer to handle business logic and orchestration

#### Task 2.1: Service Implementation ✓
- [x] Create `services/TaskService.py`
  - [x] 2.1.1 Implement CRUD operations similar to `NoteService`
  - [x] 2.1.2 Validate domain logic (handle domain exceptions → HTTP errors)
  - [x] 2.1.3 Implement filtering and pagination logic consistently
  - [x] 2.1.4 Test with fake DB session

Implementation Details:
- Created TaskService with full CRUD operations
- Added proper error handling with domain exceptions mapped to HTTP errors
- Implemented filtering by status, priority, due date, and parent task
- Added pagination support consistent with other services
- Added support for subtasks and parent task validation
- Added comprehensive unit tests with mocked dependencies

#### Task 2.2: Service Tests ✓
- [x] Create `__tests__/unit/services/test_task_service.py`
  - [x] 2.2.1 Test each CRUD method
  - [x] 2.2.2 Test error handling for domain exceptions
  - [x] 2.2.3 Test pagination and filtering

Implementation Details:
- Added comprehensive tests for all CRUD operations
- Added tests for error handling and domain exceptions
- Added tests for filtering, pagination, and subtask operations
- Achieved test coverage matching other services
- Used consistent mocking patterns with other service tests

### Epic 3: API Layer & Schemas
**Goal**: Implement the REST API endpoints and data schemas

#### Task 3.1: Pydantic Schemas ✓
- [x] Create `schemas/pydantic/TaskSchema.py`
  - [x] 3.1.1 Define `TaskCreate`, `TaskUpdate`, `TaskResponse`
  - [x] 3.1.2 Add validation constraints (title length, status)
  - [x] 3.1.3 Implement conversion methods (to_domain, from_orm)

Implementation Details:
- Created TaskBase with common fields (title, description, status, priority, due_date, tags, parent_id)
- Added TaskCreate schema with to_domain conversion
- Added TaskUpdate schema with optional fields for partial updates
- Added TaskResponse schema with id, user_id, and timestamps
- Added validation constraints using Pydantic Field
- Used consistent patterns with other entity schemas

#### Task 3.2: REST Router ✓
- [x] Create `routers/v1/TaskRouter.py`
  - [x] 3.2.1 Implement CRUD endpoints (POST, GET, PUT, DELETE)
  - [x] 3.2.2 Add filtering and pagination
  - [x] 3.2.3 Reuse existing auth/permission checks
  - [x] 3.2.4 Standardize response models (use `TaskResponse`)
  - [x] 3.2.5 Add OpenAPI "tasks" tag in metadata/Tags.py

Implementation Details:
- Created TaskRouter with full CRUD operations
- Added filtering by status, priority, due dates, and parent task
- Implemented pagination consistent with other routers
- Added HTTPBearer security dependency
- Added proper response models and type annotations
- Added dedicated endpoints for status updates and subtasks
- Added comprehensive error handling with @handle_exceptions
- Followed consistent patterns from NoteRouter and ActivityRouter

#### Task 3.3: Router Tests ✓
- [x] Create `__tests__/unit/routers/test_task_router.py`
  - [x] 3.3.1 Test all endpoints for success cases
  - [x] 3.3.2 Test authentication/permission-based errors
  - [x] 3.3.3 Test boundary conditions (missing title, invalid status, etc.)

Implementation Details:
- Added comprehensive tests for all CRUD endpoints
- Added tests for authentication and authorization errors
  - Note: Currently returns 403 for missing auth token due to FastAPI's HTTPBearer behavior
  - TODO: Consider modifying to return 401 for missing auth token to better follow HTTP standards
- Added tests for validation errors (empty title, invalid status)
- Added tests for filtering and pagination
- Added tests for subtask operations
- Added tests for error cases (not found, unauthorized)
- Followed consistent patterns from other router tests
- Achieved test coverage matching other routers (94% coverage)

### Epic 4: GraphQL Integration (Optional) ⚠️
**Goal**: Add GraphQL support for Tasks

#### Task 4.1: GraphQL Types ✓
- [x] Create `schemas/graphql/types/Task.py`
  - [x] 4.1.1 Define TaskType with all fields
  - [x] 4.1.2 Define TaskInputType for mutations
  - [x] 4.1.3 Add field resolvers for relationships (user, parent task)

Implementation Details:
- Created Task GraphQL type with all fields from domain model
- Added TaskInput and TaskUpdateInput for mutations
- Added TaskConnection for paginated results
- Added field resolvers for user and parent task relationships

#### Task 4.2: GraphQL Mutations ✓
- [x] Create `schemas/graphql/mutations/TaskMutation.py`
  - [x] 4.2.1 Add createTask mutation
  - [x] 4.2.2 Add updateTask mutation
  - [x] 4.2.3 Add deleteTask mutation
  - [x] 4.2.4 Add updateTaskStatus mutation
- [x] Update `schemas/graphql/Mutation.py`
  - [x] 4.2.5 Register task mutations

Implementation Details:
- Implemented create_task mutation with full validation
- Added update_task mutation supporting partial updates
- Added delete_task mutation with proper authorization
- Added status update mutation
- Registered all mutations in the root Mutation type

#### Task 4.3: GraphQL Queries ✓
- [x] Update `schemas/graphql/Query.py`
  - [x] 4.3.1 Add task(id) query
  - [x] 4.3.2 Add tasks query with filtering
  - [x] 4.3.3 Add subtasks query
- [x] Add task-related resolvers
  - [x] 4.3.4 Implement pagination for tasks query
  - [x] 4.3.5 Add filtering by status, priority, due date

Implementation Details:
- Added get_task query for single task retrieval
- Added list_tasks query with pagination and filtering
- Added get_subtasks query for hierarchical task viewing
- Implemented proper error handling and authorization checks
- Added comprehensive tests in `__tests__/unit/graphql/test_task_graphql.py`

#### Task 4.4: Fix GraphQL Test Issues ✓
- [x] Fix test_update_task_mutation
  - [x] 4.4.1 Update assertions to match expected behavior after update
  - [x] 4.4.2 Fix parameter order in TaskMutation.update_task
  - [x] 4.4.3 Add more comprehensive assertions for update validation
- [ ] Improve error handling
  - [ ] 4.4.4 Add consistent error handling across all mutations
  - [ ] 4.4.5 Add error handling tests for invalid inputs
  - [ ] 4.4.6 Document error handling patterns

#### Task 4.5: GraphQL Documentation
- [ ] Add comprehensive documentation
  - [ ] 4.5.1 Document all GraphQL types and fields
  - [ ] 4.5.2 Add examples for common operations
  - [ ] 4.5.3 Document error handling and validation
  - [ ] 4.5.4 Add integration test examples

#### Task 4.6: Test Coverage Improvements
- [ ] Increase test coverage for GraphQL layer
  - [ ] 4.6.1 Add tests for edge cases in mutations
  - [ ] 4.6.2 Add tests for field resolvers
  - [ ] 4.6.3 Add tests for pagination
  - [ ] 4.6.4 Add tests for filtering
- [ ] Add integration tests
  - [ ] 4.6.5 Test full GraphQL operations end-to-end
  - [ ] 4.6.6 Test error scenarios
  - [ ] 4.6.7 Test performance with larger datasets

### Epic 5: Authentication Improvements
**Goal**: Improve authentication response consistency across the API

#### Task 5.1: Authentication Response Review
- [ ] Audit current authentication behavior
  - [ ] 5.1.1 Review all routers' authentication handling
  - [ ] 5.1.2 Document current response codes and messages
  - [ ] 5.1.3 Identify inconsistencies

#### Task 5.2: Authentication Response Standardization
- [ ] Create custom HTTPBearer implementation
  - [ ] 5.2.1 Return 401 for missing/invalid tokens
  - [ ] 5.2.2 Return 403 only for permission issues
  - [ ] 5.2.3 Standardize error messages

#### Task 5.3: Router Updates
- [ ] Update all routers to use new authentication
  - [ ] 5.3.1 Update TaskRouter
  - [ ] 5.3.2 Update NoteRouter
  - [ ] 5.3.3 Update MomentRouter
  - [ ] 5.3.4 Update ActivityRouter

## Implementation Order
1. Start with Epic 1 (Domain & Data Layer) ✓
   - This establishes the foundation
   - Ensures data model is solid before building features

2. Move to Epic 2 (Service Layer) ✓
   - Builds on domain layer
   - Implements core business logic

3. Complete Epic 3 (API Layer) ✓
   - Makes feature accessible via REST
   - Implements all user-facing functionality

4. Add GraphQL support (Epic 4) ⚠️
   - Basic functionality working
   - Tests fixed and passing
   - Need to improve error handling and documentation
   - Need to increase test coverage

5. Improve Authentication (Epic 5)
   - Review and standardize authentication responses
   - Implement across all routers consistently

## Testing Strategy
- Unit tests for each layer
- Integration tests for API endpoints
- Test coverage should match existing entities
- Use existing test fixtures and utilities
- Follow existing patterns for test organization

## Validation Rules
- Title: Required, 1-255 characters
- Description: Optional, no length limit
- Status: Must be one of: 'todo', 'in_progress', 'done'
- Due Date: Optional, must be future date if provided
- User ID: Required, must exist in users table

## Success Criteria
- All tests passing
- Code coverage matches existing entities
- Follows established patterns
- Documentation updated
- API endpoints functional and tested
- GraphQL queries/mutations working (if implemented)

## Notes
- Follow existing error handling patterns
- Use existing pagination utilities
- Maintain consistent response formats
- Keep domain logic pure and separate
- Use existing auth mechanisms
