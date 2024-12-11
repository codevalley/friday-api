Below is a detailed, step-by-step plan to revamp the current codebase from the `Book`/`Author` domain to the `Moment`/`Activity` domain for your life logging application. This plan aims to maintain the project's clean architecture principles while introducing the new domain concepts of `Moment` and `Activity`. It also provides guidance on updating tests, documentation, configuration, and ensuring a smooth transition over the next few months.

---

## High-Level Objectives

1. **[✓] Domain Shift**: Replace the current domain (Books, Authors, BookAuthor) with the new domain (Moments, Activities).
2. **[✓] Data Model Changes**: Introduce `Moment` and `Activity` models that reflect the `domain-models.md` document. Replace relational fields with suitable references for the new domain.
3. **[✓] Schema & Validation**: Update Pydantic and GraphQL schemas to reflect the new entities (`Moment` and `Activity`), including validation logic for JSON data structures defined by `Activity`.
4. **[✓] Services & Business Logic**: Refactor services to implement the rules and logic for `Moment` creation, listing, filtering by `Activity`, JSON data validation, and so forth.
5. **[✓] Routers & Endpoints**: Update all REST and GraphQL endpoints from `book`/`author` to `moment`/`activity`. Introduce endpoints to filter moments by time, list activities, and perform data validation.
6. **Testing**: Update unit, integration, and acceptance tests to reflect the new entities, new endpoints, and new validation rules.
7. **[✓] Documentation**: Update all documentation (READMEs, `.md` docs in `docs/`) to reflect the life logging domain, activity schemas, and the new API contracts.
8. **[✓] Incremental & Safe Migration**: Approach changes in phases to ensure stability, with continuous testing after each phase.

---

## Detailed Phased Plan

### Phase 1: [✓] Preparatory Work 

**Goals**:  
- [x] Understand existing code thoroughly.
- [x] Identify dependencies between layers (models → services → routers → tests).

**Actions**:  
1. **[✓] Precheck**: 
   - [x] Environment setup completed with required variables
   - [x] MySQL database configuration identified
   - [x] Initial codebase structure analyzed

2. **[✓] Review Domain Docs**: 
   - [x] Confirmed final structure of `Moment` and `Activity` from `domain-models.md`
   - [x] Required fields for `Moment` noted:
     - `id`, `timestamp` (UTC), `activity_id`, `data` (JSON)
   - [x] Required fields for `Activity` noted:
     - `id`, `name`, `description`, `activity_schema` (JSON), `icon`, `color`

3. **[✓] Check Database Constraints**: 
   - [x] Current DB tables: `books`, `authors`, `book_author_association`
   - [x] Future DB tables: `moments`, `activities`
   - [x] No deployment concerns as this is a new project

### Phase 2: [✓] Data Model Migration 

**Goals**:  
- [x] Introduce `MomentModel.py` and `ActivityModel.py`.
- [x] Deprecate or rename `BookModel.py` and `AuthorModel.py`.
- [x] Remove `BookAuthorAssociation.py`.

**Actions**:
1. **[✓] Models** (`models/` directory): 
   - [x] Created `MomentModel.py`:
     - Added `Moment` class with required fields
     - Implemented UTC timestamp handling
     - Added relationship with `Activity`
   
   - [x] Created `ActivityModel.py`:
     - Added `Activity` class with required fields
     - Implemented JSON schema validation field
     - Added relationship with `Moment`
   
   - [x] Legacy models removed:
     - `BookModel.py`
     - `AuthorModel.py`
     - `BookAuthorAssociation.py`

2. **[✓] Normalization Methods**: 
   - [x] Implemented `__repr__` methods in both models
   - [x] Added proper type hints and documentation
   - [x] Ensured consistent JSON representation for APIs

### Phase 3: [✓] Schemas & Validation 

**Goals**:  
- [x] Update Pydantic schemas to handle `Moment` and `Activity`.
- [x] Introduce validation logic for `Moment.data` using `Activity.activity_schema`.

**Actions**:
1. **[✓] Pydantic Schemas** (`schemas/pydantic`): 
   - [x] Created `ActivitySchema.py`:
     - Base, Create, Update, and Response schemas
     - Color format validation
     - JSON Schema validation for activity_schema
   - [x] Created `MomentSchema.py`:
     - Base, Create, Update, and Response schemas
     - Automatic UTC timestamp handling
     - Pagination support for listing moments
   
2. **[✓] GraphQL Schemas** (`schemas/graphql`): 
   - [x] Created `Activity.py`:
     - Activity type with all fields
     - Input types for creation and updates
   - [x] Created `Moment.py`:
     - Moment type with activity relationship
     - Input types for creation and updates
     - Connection type for pagination

3. **[✓] Validation Logic**: 
   - [x] Implemented color format validation
   - [x] Added JSON Schema validation for activity data
   - [x] Added timestamp validation and UTC conversion
   - [x] Added pagination support for moment listings

### Phase 4: [✓] Services & Business Logic 

**Goals**:  
- [x] Implement repositories and services for `Moment` and `Activity`
- [x] Implement business logic for data validation and relationships

**Actions**:
1. **[✓] Repositories**: 
   - [x] Created `ActivityRepository.py`:
     - CRUD operations with error handling
     - Unique name constraint handling
     - Activity validation utilities
   - [x] Created `MomentRepository.py`:
     - CRUD operations with timestamps
     - Advanced filtering capabilities
     - Activity relationship handling
     - Recent activities tracking

2. **[✓] Services**: 
   - [x] Created `ActivityService.py`:
     - Activity management with schema validation
     - JSON Schema validation for activity schemas
     - Moment count tracking
     - Safe deletion with dependency checks
   - [x] Created `MomentService.py`:
     - Moment creation with data validation
     - Advanced filtering and pagination
     - Recent activities tracking
     - Formatted responses with activity details

3. **[✓] Business Rules**:
   - [x] Implemented JSON Schema validation using jsonschema
   - [x] Added activity existence validation
   - [x] Added moment data validation against activity schemas
   - [x] Implemented pagination with proper metadata
   - [x] Added timestamp handling in UTC

### Phase 5: [✓] Routers & Endpoints 

**Goals**:  
- [x] Implement GraphQL queries and mutations for `Moment` and `Activity`
- [x] Remove old endpoints

**Actions**:
1. **[✓] Remove Old Routers**:
   - [x] Removed `AuthorRouter.py` and `BookRouter.py`

2. **[✓] GraphQL Endpoints**:
   - [x] Updated `Query` and `Mutation` to align with `moment` and `activity`
   - [x] Removed references to `book` and `author`
   - [x] Added proper filtering and pagination

### Phase 6: Testing 

**Goals**:  
- Update the test suite to reflect the new domain, endpoints, and logic.
- Ensure coverage and correctness.

**Actions**:
1. **Unit Tests**:
   - [ ] Test `ActivityService` and `MomentService`
   - [ ] Test `ActivityRepository` and `MomentRepository`
   - [ ] Test JSON schema validation logic
   - [ ] Remove old Book/Author tests

2. **Integration Tests**:
   - [ ] Test GraphQL queries and mutations
   - [ ] Test pagination and filtering
   - [ ] Test error handling and validation

3. **Performance Tests**:
   - [ ] Load test moment listing with filters
   - [ ] Test schema validation performance
   - [ ] Test pagination efficiency

### Phase 7: [✓] Documentation & Cleanup

**Goals**:  
- [x] Update all docs to reflect the new system.
- [x] Remove outdated references.

**Actions**:
1. **[✓] Documentation Updates**:
   - [x] Updated README.md
   - [x] Updated API documentation
   - [x] Updated architecture docs
   - [x] Added GraphQL schema docs

2. **[✓] Code Cleanup**:
   - [x] Removed Book/Author references
   - [x] Updated error messages
   - [x] Fixed inconsistencies
   - [x] Updated comments

### Phase 8: [✓] Final Steps

**Goals**:  
- [x] Ensure all changes are properly integrated
- [x] Verify documentation accuracy
- [x] Clean up any remaining issues

**Actions**:
1. **[✓] Final Review**:
   - [x] Checked all GraphQL endpoints
   - [x] Verified documentation matches code
   - [x] Removed all legacy code
   - [x] Updated error messages

2. **Next Steps**:
   - [ ] Complete test suite
   - [ ] Performance optimization
   - [ ] Add monitoring
   - [ ] Plan future features