# Friday API todo

### Action Plan (Organized as Epics)

**Epic 1: Architectural Improvements**
- ~~Refactor JSON schema validation to the domain layer.~~ ✅
- Resolve circular dependencies in services.

**Epic 2: Repository Enhancements** ✅
- ~~Introduce a `BaseRepository` class.~~
- ~~Standardize error handling with custom exceptions.~~
- ~~Improve transaction management for batch operations.~~

**Epic 3: Service Refactoring** ⏳
- ~~Extract validation logic into shared utilities.~~ ✅
- ~~Simplify complex service methods.~~ ✅
- ~~Fix moment retrieval issues~~ ✅

**Epic 4: Testing Enhancements**
- Write integration tests for GraphQL APIs.
- Add edge case tests for schema validation.

**Epic 5: Code Quality and Cleanup**
- Remove unused methods and imports.
- Implement middleware for centralized error handling.

**Epic 6: Database Improvements**
- Integrate Alembic for schema migrations.
- Improve granularity of database constraints.

**Epic 7: Documentation Updates**
- Update API documentation to include error response formats.
- Add migration strategy and database guidelines to project documentation.

---

### Conclusion
The "Friday API" demonstrates excellent adherence to Clean Architecture principles but has room for improvement in code reusability, validation consistency, and testing. By addressing the identified issues, the codebase can achieve higher maintainability, scalability, and robustness.
