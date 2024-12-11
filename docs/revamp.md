# Revamp Plan: Book Management to Life Moments System

This document outlines the comprehensive plan to transform the current book management system into a life moments tracking system.

## Entity Transformation
### Current to New Mapping
- `Book` → `Moment`
- `Author` → `Activity`
- `BookAuthor` → (Remove, no equivalent needed)

## Required Changes by Directory

### 1. Models Directory (`/models`)
- Rename and modify `BookModel.py` to `MomentModel.py`
  - Replace book-specific fields with:
    - id: Integer (keep)
    - timestamp: DateTime (new)
    - activity_id: Integer (transform from author_id)
    - data: JSON (new)

- Rename and modify `AuthorModel.py` to `ActivityModel.py`
  - Replace author-specific fields with:
    - id: Integer (keep)
    - name: String (keep)
    - description: String (transform from biography)
    - activity_schema: JSON (new)
    - icon: String (new)
    - color: String (new)

- Remove `BookAuthorAssociation.py` (no longer needed)
- Update `__init__.py` with new model imports
- Update `BaseModel.py` if any base model changes are needed

### 2. Schemas Directory (`/schemas`)
- Transform input/output schemas:
  - `book.py` → `moment.py`
    - Create schemas for:
      - MomentCreate
      - MomentResponse
      - MomentUpdate
  - `author.py` → `activity.py`
    - Create schemas for:
      - ActivityCreate
      - ActivityResponse
      - ActivityUpdate
- Update any shared schemas or dependencies

### 3. Services Directory (`/services`)
- Transform `BookService.py` to `MomentService.py`
  - Update CRUD operations for moments
  - Add timestamp handling
  - Add JSON data validation against activity schema
- Transform `AuthorService.py` to `ActivityService.py`
  - Update CRUD operations for activities
  - Add schema validation logic
  - Add icon and color handling
- Update `__init__.py` with new service imports

### 4. Repositories Directory (`/repositories`)
- Transform `BookRepository.py` to `MomentRepository.py`
  - Update database queries for new schema
  - Add timestamp-based queries
- Transform `AuthorRepository.py` to `ActivityRepository.py`
  - Update queries for activity-specific fields
- Remove `BookAuthorRepository.py`
- Update base repository if needed

### 5. Routers Directory (`/routers/v1`)
- Transform endpoints:
  - `books.py` → `moments.py`
    - Update CRUD endpoints
    - Add timestamp-based filtering
    - Add activity-based filtering
  - `authors.py` → `activities.py`
    - Update CRUD endpoints
    - Add schema validation endpoints
- Update route registrations in main router file

### 6. Database Migrations
- Create new migration script for:
  - Creating `moments` table
  - Creating `activities` table
  - Dropping `books`, `authors`, and `book_author` tables

### 7. Tests Directory (`/__tests__`)
- Update test files:
  - Rename and modify test files to match new entities
  - Update test data fixtures
  - Add new test cases for:
    - Timestamp handling
    - JSON data validation
    - Activity schema validation
    - Icon and color handling

### 8. Configuration Files
- Update any configuration files referencing old entities
- Update environment variables if needed
- Update API documentation configuration

## Implementation Order
1. Create new models and schemas
2. Create database migrations
3. Update repositories
4. Update services
5. Update API routes
6. Update tests
7. Update configuration and documentation
8. Perform end-to-end testing

## Additional Considerations
- Ensure proper UTC timestamp handling
- Implement JSON schema validation for activity schemas
- Add proper indexing for timestamp-based queries
- Consider adding bulk operations for moments
- Implement proper error handling for JSON data validation

## Testing Strategy
1. Unit tests for new models and services
2. Integration tests for repositories
3. API endpoint tests
4. Migration tests
5. Performance tests for timestamp-based queries
6. Validation tests for JSON schemas

## Rollback Plan
1. Keep backup of old code
2. Create reverse migrations
3. Maintain old tests until new system is verified
4. Document rollback procedures

## Timeline Estimation
1. Documentation updates: 1 day
2. Core implementation: 3-4 days
3. Testing: 2-3 days
4. Review and refinement: 1-2 days
