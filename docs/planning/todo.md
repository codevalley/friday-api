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



## ** [Second scan] Epics and Tasks**
### **Epic 1: Codebase Cleanup**
1. **Centralize Validation Logic**:
   - Extract JSON schema validation into a shared utility.
   - Ensure uniform use of this utility in models, services, and repositories.

2. **Consolidate Pagination Logic**:
   - Introduce a shared pagination utility in `utils/`.

3. **Remove Unused Code**:
   - Audit unused methods and imports across all files.

4. **Enhance Type Annotations**:
   - Improve type hints in all repository and service methods.

---

### **Epic 2: Architectural Refinements**
1. **Ensure Uniform Error Handling**:
   - Create a shared error-handling module.
   - Refactor all services and routers to use consistent exception handling.

2. **Optimize Cross-Layer Interactions**:
   - Reuse service methods across REST and GraphQL layers to reduce duplication.

3. **Expand Repository Abstraction**:
   - Leverage `BaseRepository` for more uniform CRUD operations.

---

### **Epic 3: Schema Enhancements**
1. **Standardize Pydantic and GraphQL Schemas**:
   - Ensure naming conventions and validation logic are consistent across Pydantic and Strawberry schemas.

2. **Improve Domain Mapping**:
   - Review and streamline the `to_domain` and `from_domain` methods for all entities.

3. **Simplify Conversion Utilities**:
   - Consolidate `ensure_dict` and `ensure_string` utilities to reduce redundancy.

---

### **Epic 4: Testing Improvements**
1. **Expand Unit Test Coverage**:
   - Add tests for edge cases in repositories and services.
   - Validate cascading delete scenarios for related entities.

2. **Introduce Integration Tests**:
   - Verify end-to-end functionality of key workflows (e.g., creating an activity and logging moments).

3. **Improve Test Fixtures**:
   - Use modular fixtures to set up reusable test data.

---

### **Epic 5: Documentation and Linting**
1. **Update Documentation**:
   - Include examples of common workflows (e.g., logging moments) in `README.md`.
   - Document error codes and responses for REST and GraphQL APIs.

2. **Ensure Code Quality**:
   - Fix all linting issues detected by `flake8`, `black`, and `mypy`.
