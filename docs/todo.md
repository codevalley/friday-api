### Phase 1: Code cleanup
**General architecture**:  
- [ ] Consider splitting large schema files or using a registry pattern for GraphQL to reduce bottom-of-file imports.
- [ ] See if long method names can be reduced without losing clarity
- [ ] Check if the `RepositoryMeta` interface is still necessary since you have direct repository implementations.

**Models/Domain**:  
- [ ] Ensure that `validate_schema` or `validate_data` is always called before commit, possibly in the service layer.
- [ ] Strictly use UTC for timestamps and ensure no confusion in time handling.

**Repositories**:  
- [ ] Remove `HTTPException` from repositories. Return `None` or raise a custom `RepositoryError`. The service layer can catch this and raise `HTTPException`.
- [ ] Validate existence in the service layer rather than the repository layer, or have a repository method named `get_or_none` and let the service decide what to do if `None`.

**Services**:
- [ ] Abstract error handling in services. Services can raise custom DomainError or `NotFoundError`. Routers catch these and return `HTTPException`.

**Schemas**:  
- [ ] Some duplicate logic exists between Pydantic and JSONSchema validations. Consider consolidating validation logic where possible.
- [ ] GraphQL schemas make frequent use of string-JSON conversions (`ensure_string` and `ensure_dict`). Can use a single utility or internal code that uses dicts, only graphql boundary uses strings.
- [ ] The GraphQL layer references `info.context` a lot, which is fine, but consider a single context object with typed attributes for better maintainability.
- [ ] If feasible, unify how you handle JSON fields. For instance, always store them as dict internally and convert to/from strings only at the boundary. Also reduce duplication of schema validation by centralizing it in the service layer. (agree?)

**Routers**:
- [ ] Some routers directly raise HTTPException when they could just rely on the service to signal errors. Not a big issue, just a design choice. (choice?)
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
- Add these libs to our pipenv file.
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

## Recent Fixes

1. Fixed bcrypt version detection issue by:
   - Removed passlib dependency for password hashing
   - Implemented direct bcrypt usage for password hashing and verification
   - Updated user secret generation to use secrets.token_urlsafe
   - Fixed token generation in auth router
