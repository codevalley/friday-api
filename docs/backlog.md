# Arch review

Below is a proposed, step-by-step action plan organized by thematic epics, with current progress indicated. Each epic addresses one or more of the identified issues, with tasks detailing what changes should be made and how.

Status Key:
✅ Complete
⏳ In Progress
🔄 Partially Complete
⭕ Not Started

---

## Epic 1: Streamline Domain and Service Boundaries 🔄

**Issues Addressed:** #1 (Duplicated domain logic), #2 (Repositories returning ORM models), #7 (Inconsistent validation patterns)

### Goal
- Ensure that all domain logic and validations reside in the domain layer.
- Services coordinate domain objects and repository operations but do not replicate domain logic.
- Services and domain models operate on domain objects, while repositories handle ORM boundaries.

### Tasks

**Task 1.1: ✅ Move all validation and business rules into domain models**  
- **Completed**: Successfully moved color and username validation into domain models
- **Result**: Services now delegate validation to domain models, with consistent error messages

**Task 1.2: ⏳ Ensure all repositories return domain models, not ORM models**  
- **Current State**: Repositories still return ORM objects that services convert to domain objects.  
- **Action**: Inside each repository method, convert ORM models to domain models before returning. For example, after querying an `Activity` (ORM), immediately call `ActivityData.from_orm(activity_orm)` and return that.  
- **Result**: Services always receive domain models directly from repositories, removing the need for the service layer to do conversions.
- **Priority**: High - Next task to tackle

**Task 1.3: ✅ Standardize validation patterns**  
- **Completed**: Implemented consistent validation patterns across domain models
- **Result**: Every domain entity ensures correctness at creation with standardized error messages

---

## Epic 2: Remove Infrastructure Leaks from Domain 🔄

**Issues Addressed:** #3 (HTTPException in domain), #6 (Domain referencing JSON schema directly)

### Goal
- Domain models and logic should not depend on HTTP frameworks or JSON schema libraries directly.
- Introduce a boundary layer or validators so that domain code remains pure.

### Tasks

**Task 2.1: ⏳ Replace HTTPException usage with domain-specific exceptions**  
- **Current State**: Domain and services still raise `HTTPException`.  
- **Action**: Define custom exceptions in the domain layer (e.g., `DomainValidationError`) and raise these from domain models when data is invalid. Services can catch these domain exceptions and map them to `HTTPException` in the controller/route layer.  
- **Priority**: High - Should be addressed next
- **Result**: Domain and services will be free of HTTP-specific exceptions.

**Task 2.2: ⭕ Encapsulate JSON schema validation**  
- **Current State**: Domain classes reference `jsonschema` directly.  
- **Action**: Introduce a validator utility in `utils/validation/` that performs JSON schema checks.
- **Priority**: Medium - Dependent on Task 2.1 completion
- **Result**: Domain classes will no longer depend on `jsonschema` library.

---

## Epic 3: Consolidate Validation and Schema Checks ⭕

**Issues Addressed:** #4 (Activity schema validation done multiple times)

### Goal
- Centralize activity schema validation in a single step so it's not repeated in multiple layers.

### Tasks

**Task 3.1: ⭕ Single entry point for schema validation**  
- **Priority**: Medium - Dependent on Epic 2 completion
- **Action**: Implement centralized validation in service or dedicated validator module
- **Status**: Not started - Waiting on Epic 2 completion

---

## Epic 4: Unify GraphQL and REST Interface Interactions ⭕

**Issues Addressed:** #5 (Parallel GraphQL and REST code)

### Goal
- Both GraphQL and REST endpoints should rely on the same service methods, returning domain models and mapping them in their respective presentation layer only.

### Tasks

**Task 4.1: ⭕ Remove GraphQL-specific versions of service calls**  
- **Priority**: Low - Can be done independently
- **Status**: Not started

**Task 4.2: ⭕ Centralize presentation transformations**  
- **Priority**: Low - Dependent on Task 4.1
- **Status**: Not started

---

## Epic 5: Remove Direct HTTP-Framework Dependencies ⭕

**Priority**: High - Related to Epic 2
**Status**: Not started - Should begin after Epic 2 completion

**Task 5.1: ⭕ Move HTTPException logic to presentation layer**  
- Will be addressed as part of Epic 2, Task 2.1

---

## Epic 6: Consistent Validation Approach ✅

**Status**: Complete
- Implemented consistent validation patterns
- Standardized error messages
- Domain models now handle their own validation

---

## Current Priority Order:

1. **Epic 2, Task 2.1** (High Priority)
   - Replace `HTTPException` with domain-specific exceptions
   - Critical for domain layer purity

2. **Epic 1, Task 1.2** (High Priority)
   - Convert repositories to return domain models
   - Will complete domain boundary streamlining

3. **Epic 2, Task 2.2** (Medium Priority)
   - Encapsulate JSON schema validation
   - Prerequisite for Epic 3

4. **Epic 3** (Medium Priority)
   - Consolidate validation and schema checks
   - Depends on completion of Epic 2

5. **Epic 4 & 5** (Lower Priority)
   - Can be tackled independently after core domain improvements

## Minor improvements for later:

Avoid calling logging.basicConfig() after you have a more advanced setup in configure_logging(). configure_logging() should be the one-stop shop for logging config.
If sqlalchemy logging is too noisy, reduce its level from DEBUG to something higher (like INFO or WARN).
If you want less verbose logs in production, you could add environment-based checks inside configure_logging() to set levels differently based on env.DEBUG_MODE.


• Goal: Use the same service/business logic methods for both GraphQL and REST to reduce duplication.  
• Tasks:  
  5.1 Identify overlapping code in GraphQL resolvers and REST endpoints.  
  5.2 Refactor any parallel methods in the services so that both GraphQL and REST clients invoke the same core function.  
  5.3 Consistently map the domain objects to GraphQL or REST response schemas, without branching logic.  
