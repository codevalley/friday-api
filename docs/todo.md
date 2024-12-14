### Phase 1: Code cleanup
**General architecture**:  
- [x] Consider splitting large schema files or using a registry pattern for GraphQL to reduce bottom-of-file imports.
  - Created base schema classes (MomentData, UserData, ActivityData)
  - Moved common logic to base classes
  - Better organized imports to reduce circular dependencies
- [ ] See if long method names can be reduced without losing clarity
- [x] Check if the `RepositoryMeta` interface is still necessary since you have direct repository implementations.
  - Removed in favor of direct domain model conversions

**Models/Domain**:  
- [x] Ensure that `validate_schema` or `validate_data` is always called before commit, possibly in the service layer.
  - Added validation in base schema classes with __post_init__
  - Comprehensive validation for all fields
- [x] Strictly use UTC for timestamps and ensure no confusion in time handling.
  - Consistent UTC timestamp handling in base schemas
  - Clear documentation about timestamp expectations

**Repositories**:  
- [x] Remove `HTTPException` from repositories. Return `None` or raise a custom `RepositoryError`. The service layer can catch this and raise `HTTPException`.
  - Moved HTTP concerns out of repositories
  - Using domain-specific errors in base schemas
- [x] Validate existence in the service layer rather than the repository layer, or have a repository method named `get_or_none` and let the service decide what to do if `None`.
  - Validation now happens in service layer using base schemas

**Services**:
- [x] Abstract error handling in services. Services can raise custom DomainError or `NotFoundError`. Routers catch these and return `HTTPException`.
  - Added proper error hierarchy with domain-specific errors

**Schemas**:  
- [x] Some duplicate logic exists between Pydantic and JSONSchema validations. Consider consolidating validation logic where possible.
  - Consolidated validation in base schema classes
  - Single source of truth for validation rules
- [x] GraphQL schemas make frequent use of string-JSON conversions (`ensure_string` and `ensure_dict`). Can use a single utility or internal code that uses dicts, only graphql boundary uses strings.
  - Created unified JSON handling in utils/json_utils.py
  - Consistent conversion at boundaries only
- [x] The GraphQL layer references `info.context` a lot, which is fine, but consider a single context object with typed attributes for better maintainability.
  - Improved GraphQL context handling with proper typing
- [x] If feasible, unify how you handle JSON fields. For instance, always store them as dict internally and convert to/from strings only at the boundary. Also reduce duplication of schema validation by centralizing it in the service layer. (agree?)
  - Implemented dict-based internal storage
  - JSON conversion only at boundaries
  - Centralized validation in base schemas

**Routers**:
- [x] Some routers directly raise HTTPException when they could just rely on the service to signal errors. Not a big issue, just a design choice. (choice?)
  - Moved error handling to service layer
  - Routers now handle only HTTP concerns
- [ ] Pagination parameters (page, size) are not always consistently validated (e.g., `ge=1`, `le=100`). Make sure consistent validation is applied everywhere.

**Security**:
- [ ] Use a single hashing strategy for user secrets (e.g., stick to sha256 or bcrypt).
- [ ] Rate limiting for Auth endpoints.

### Phase 2: Testing 

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

### General Todo
- [ ] Add these libs to our pipenv file.
   - python-jose
   - pathlib
   - httpx

## Security Issues

1. **Missing Rate Limiting**:
   - No rate limiting on authentication attempts
   - Fix: Implement rate limiting on auth endpoints

## Performance Issues

1. **Inefficient Database Queries**:
   - Each get_by_* method performs a separate query
   - Fix: Consider caching frequently accessed user data
   
2. **Recent Activity Tracking**:
   - No tracking of recent activities
   - Fix: Implement recent activity tracking

## Maintenance Issues

1. **Inconsistent Async/Sync Methods**:
   - Service methods are async but repository methods are sync
   - Fix: Make all database operations consistently async

## Enhancement Suggestions

1. **Audit Trail**:
   - No tracking of failed login attempts
   - Add logging for security events

2. **Password Recovery**:
   - No mechanism for user secret recovery
   - Consider implementing a secure recovery process

## Next Steps

1. Implement rate limiting using FastAPI's dependencies and Redis/Memcached
2. Add caching layer for frequently accessed user data
3. Make database operations consistently async
4. Add audit logging for security events
5. Design and implement a secure user secret recovery process
6. add to pipfile types-SQLAlchemy types-jsonschema
## Recent Fixes

1. Fixed bcrypt version detection issue by:
   - Removed passlib dependency for password hashing
   - Implemented direct bcrypt usage for password hashing and verification
   - Updated user secret generation to use secrets.token_urlsafe
   - Fixed token generation in auth router
