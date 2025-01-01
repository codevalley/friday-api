# Tasks Feature Implementation Plan

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

#### Task 1.1: Domain Implementation
- [ ] Create `domain/task.py`
  - 1.1.1 Implement the core domain model class (e.g., TaskData)
  - 1.1.2 Add validation rules (title constraints, status fields, due date checks)
  - 1.1.3 Add task-specific exceptions to `domain/exceptions.py` as needed
  - 1.1.4 (Optional) Add any new value objects (e.g., `TaskStatus`) if business logic is advanced

#### Task 1.2: ORM Model
- [ ] Create `orm/TaskModel.py`
  - 1.2.1 Define SQLAlchemy model fields mirroring domain
  - 1.2.2 Set up relationship with User model (foreign key: user_id)
  - 1.2.3 Add indexes and constraints for status, due_date

#### Task 1.3: Repository Layer
- [ ] Create `repositories/TaskRepository.py`
  - 1.3.1 Implement `TaskRepository` extending `BaseRepository`
  - 1.3.2 Add create/read/update/delete methods, ensuring consistent patterns with `NoteRepository`
  - 1.3.3 Implement filtering and pagination support

#### Task 1.4: Tests for Domain & Repository
- [ ] Create `__tests__/unit/domain/test_task_data.py`
  - 1.4.1 Test domain validations and exceptions
  - 1.4.2 Test edge cases, empty title, invalid status, etc.
- [ ] Create `__tests__/unit/repositories/test_task_repository.py`
  - 1.4.3 Test repository CRUD operations
  - 1.4.4 Ensure foreign key constraints and user_id references are validated

### Epic 2: Service Layer & Business Logic
**Goal**: Implement the service layer to handle business logic and orchestration

#### Task 2.1: Service Implementation
- [ ] Create `services/TaskService.py`
  - 2.1.1 Implement CRUD operations similar to `NoteService`
  - 2.1.2 Validate domain logic (handle domain exceptions → HTTP errors)
  - 2.1.3 Implement filtering and pagination logic consistently
  - 2.1.4 Test with fake or real DB session (depending on your approach)

#### Task 2.2: Service Tests
- [ ] Create `__tests__/unit/services/test_task_service.py`
  - 2.2.1 Test each CRUD method
  - 2.2.2 Test error handling for domain exceptions
  - 2.2.3 Test pagination and filtering

### Epic 3: API Layer & Schemas
**Goal**: Implement the REST API endpoints and data schemas

#### Task 3.1: Pydantic Schemas
- [ ] Create `schemas/pydantic/TaskSchema.py`
  - 3.1.1 Define `TaskCreate`, `TaskUpdate`, `TaskResponse`
  - 3.1.2 Add validation constraints (title length, status)
  - 3.1.3 Implement conversion methods (to_domain, from_orm)

#### Task 3.2: REST Router
- [ ] Create `routers/v1/TaskRouter.py`
  - 3.2.1 Implement CRUD endpoints (POST, GET, PUT, DELETE)
  - 3.2.2 Add filtering and pagination
  - 3.2.3 Reuse existing auth/permission checks
  - 3.2.4 Standardize response models (use `TaskResponse`)
  - 3.2.5 Add OpenAPI "tasks" tag in metadata/Tags.py

#### Task 3.3: Router Tests
- [ ] Create `__tests__/unit/routers/test_task_router.py`
  - 3.3.1 Test all endpoints for success cases
  - 3.3.2 Test authentication/permission-based errors
  - 3.3.3 Test boundary conditions (missing title, invalid status, etc.)

### Epic 4: GraphQL Integration (Optional)
**Goal**: Add GraphQL support for Tasks

#### Task 4.1: GraphQL Types
- [ ] Create `schemas/graphql/types/Task.py`
- [ ] Create `schemas/graphql/types/TaskInput.py`
- [ ] Create `schemas/graphql/types/TaskResponse.py`

#### Task 4.2: GraphQL Mutations
- [ ] Create `schemas/graphql/mutations/TaskMutation.py`
- [ ] Update `schemas/graphql/Mutation.py`

#### Task 4.3: GraphQL Queries
- [ ] Update `schemas/graphql/Query.py`
- [ ] Add task-related resolvers

## File Structure
```
domain/
  ├── task.py
orm/
  ├── TaskModel.py
repositories/
  ├── TaskRepository.py
services/
  ├── TaskService.py
routers/v1/
  ├── TaskRouter.py
schemas/
  ├── pydantic/
  │   └── TaskSchema.py
  └── graphql/
      ├── types/
      │   ├── Task.py
      │   ├── TaskInput.py
      │   └── TaskResponse.py
      └── mutations/
          └── TaskMutation.py
__tests__/
  └── unit/
      ├── domain/
      │   └── test_task_data.py
      ├── repositories/
      │   └── test_task_repository.py
      ├── services/
      │   └── test_task_service.py
      └── routers/
          └── test_task_router.py
```

## Database Schema
```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'todo',
    due_date TIMESTAMP,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
```

## Implementation Order
1. Start with Epic 1 (Domain & Data Layer)
   - This establishes the foundation
   - Ensures data model is solid before building features

2. Move to Epic 2 (Service Layer)
   - Builds on domain layer
   - Implements core business logic

3. Complete Epic 3 (API Layer)
   - Makes feature accessible via REST
   - Implements all user-facing functionality

4. Finally Epic 4 (GraphQL) if needed
   - Adds alternative access method
   - Can be done after basic functionality is working

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
