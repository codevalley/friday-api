## EPIC: Introduce "Topic" Entity

We will introduce a new top-level entity called **Topic**, which represents a user-specific tag or classification object with a distinct icon and name. This epic involves creating the necessary domain model, ORM model, repository, services, schemas, and optional routers to support CRUD operations on topics.

## Implementation Patterns

### 1. Domain Layer

- Use specific exceptions for each validation type (e.g., `TopicNameError`, `TopicIconError`)
- Use TypeVar for better type hints and inheritance
- Implement `to_dict()` and `from_dict()` methods for data conversion
- Add helper methods for state changes (e.g., `update_name()`, `update_icon()`)
- Validate all fields in `validate()` method
- Use UTC for all timestamps

### 2. ORM Layer

- Define constants for field lengths and other constraints
- Use `from_dict()`, `to_domain()`, and `from_domain()` methods
- Organize fields by type (primary key, required fields, timestamps, etc.)
- Use explicit relationship definitions
- Add comprehensive docstrings with all attributes

### 3. Repository Layer

- Extend `BaseRepository` for common CRUD operations
- Add domain-specific methods with `_from_domain` suffix
- Handle specific database errors (e.g., unique constraints)
- Convert exceptions to domain-specific ones
- Add user-scoped query methods

### 4. Service Layer

- Handle all database transactions
- Convert domain exceptions to HTTP exceptions
- Use specific status codes for different error types
- Add comprehensive error handling with rollbacks
- Validate ownership in all operations

### 5. Schema Layer

- Use Pydantic's Field for validation
- Add example values and descriptions
- Implement domain conversion methods
- Handle both snake_case and camelCase
- Use proper response wrappers

#### Schema Patterns

- All list responses inherit from `PaginationResponse`
- All response models have `from_domain` classmethods
- All models use `ConfigDict` with examples
- All fields have descriptions and validation rules
- All models follow consistent naming:
  - `{Entity}Base`: Common fields and validation
  - `{Entity}Create`: Creation fields with `to_domain()`
  - `{Entity}Update`: Optional fields for updates
  - `{Entity}Response`: Full model with system fields
  - `{Entity}List`: Paginated list response

#### Pagination Pattern

All list endpoints use consistent pagination through `PaginationResponse`:

```python
class PaginationResponse(BaseModel):
    """Base class for paginated responses."""

    items: List[Any]  # Override in child classes
    total: int
    page: int
    size: int
    pages: int
```

This ensures:

- Consistent pagination metadata
- Proper type hints
- Clear documentation
- Example responses
- Domain model conversion

---

## Feature Requirements

1. **Minimal Fields**
   - **id**: Primary key (integer)
   - **user_id**: Foreign key to User (UUID string)
   - **name**: Unique name per user (max 255 chars)
   - **icon**: Emoji or URI (max 255 chars)
   - **created_at**: Creation timestamp (UTC)
   - **updated_at**: Last update timestamp (UTC)
2. **Constraints**
   - `name` must be unique per user
   - `name` and `icon` cannot be empty
   - `name` and `icon` max length is 255 chars
   - All timestamps must be UTC
   - All string fields must be properly validated
3. **Error Handling**
   - `TopicNameError`: For name-related validation errors
   - `TopicIconError`: For icon-related validation errors
   - `TopicValidationError`: For general validation errors
   - HTTP 409: For name uniqueness conflicts
   - HTTP 400: For validation errors
   - HTTP 404: For not found errors
   - HTTP 500: For unexpected errors
4. **Business Logic**
   - Topics are user-scoped
   - Names must be unique per user
   - All updates maintain audit timestamps
   - All operations validate ownership
   - All string fields are trimmed and validated
5. **Future Considerations**
   - Potentially referencing `topic_id` in tasks, notes, or other entities in the future.
   - The same user can have multiple topics, but each must have a unique name.

---

## Overall Design Approach

The new **Topic** entity will follow the same layered design patterns used across the codebase:

1. **Domain**:
   - A `TopicData` dataclass that holds domain logic (validation, invariants).
2. **ORM**:
   - A `Topic` SQLAlchemy model (e.g., `orm.TopicModel`), including columns and constraints.
3. **Repository**:
   - A `TopicRepository` that extends or implements the standard CRUD approach.
4. **Service**:
   - A `TopicService` that orchestrates domain validations and calls to `TopicRepository`.
5. **Schemas**:
   - Pydantic schemas for creation, updates, and responses (`TopicCreate`, `TopicUpdate`, `TopicResponse`, etc.).
6. **Router (optional)**:
   - A set of FastAPI endpoints to create, read, update, and delete topics.

---

## Tasks & Subtasks

### 1. **Domain Layer**

**Task**: Define `TopicData` in the domain package.

- **Subtask 1.1**: Create a new file `domain/topic.py` (or reuse an existing domain file structure).

  - **Implementation**:

    ```python
    # domain/topic.py

    from dataclasses import dataclass
    from typing import Optional
    from datetime import datetime

    from domain.exceptions import DomainException

    @dataclass
    class TopicData:
        id: Optional[int]
        user_id: str
        name: str
        icon: str
        created_at: Optional[datetime] = None
        updated_at: Optional[datetime] = None

        def __post_init__(self):
            self.validate()

        def validate(self) -> None:
            # Example validations:
            if not self.name or not isinstance(self.name, str):
                raise DomainException("Topic name must be a non-empty string", code="TOPIC_INVALID_NAME")
            if not self.icon or not isinstance(self.icon, str):
                raise DomainException("Topic icon must be a non-empty string", code="TOPIC_INVALID_ICON")
    ```

  - **Validation**:
    - Non-empty `name` and `icon`.
    - `name` uniqueness will be enforced via repository or database constraint.

- **Subtask 1.2**: Decide on custom domain exceptions (if needed).
  - Could reuse a general `DomainException` or define `TopicValidationError` if we want more specialized error messages.

---

### 2. **ORM Layer**

**Task**: Create `Topic` model under `orm/TopicModel.py`.

- **Subtask 2.1**: Create the file `orm/TopicModel.py` or place in an existing file if needed.
- **Subtask 2.2**: Define the `Topic` SQLAlchemy model:

  ```python
  from sqlalchemy import (
      Column,
      Integer,
      String,
      ForeignKey,
      DateTime,
      CheckConstraint,
      UniqueConstraint,
  )
  from sqlalchemy.orm import Mapped, relationship
  from datetime import datetime, UTC

  from orm.BaseModel import EntityMeta

  class Topic(EntityMeta):
      __tablename__ = "topics"

      id: Mapped[int] = Column(Integer, primary_key=True, index=True)
      user_id: Mapped[str] = Column(
          String(36),
          ForeignKey("users.id", ondelete="CASCADE"),
          nullable=False,
      )
      name: Mapped[str] = Column(String(255), nullable=False)
      icon: Mapped[str] = Column(String(255), nullable=False)
      created_at: Mapped[datetime] = Column(
          DateTime(timezone=True),
          nullable=False,
          default=lambda: datetime.now(UTC),
      )
      updated_at: Mapped[datetime] = Column(
          DateTime(timezone=True),
          nullable=True,
          onupdate=lambda: datetime.now(UTC),
      )

      # Constraints
      __table_args__ = (
          CheckConstraint("name != ''", name="check_topic_name_not_empty"),
          CheckConstraint("icon != ''", name="check_topic_icon_not_empty"),
          UniqueConstraint("user_id", "name", name="uq_topic_name_per_user"),
      )
  ```

- **Subtask 2.3**: Ensure to handle any foreign key relationships or data constraints.
- **Subtask 2.4**: (Optional) If you want to define a relationship to `User`:
  ```python
  user = relationship("User", back_populates="topics")
  ```
  - Then in `UserModel`, add: `topics: Mapped[List["Topic"]] = relationship("Topic", back_populates="user", cascade="all, delete-orphan")`

---

### 3. **Repository Layer**

**Task**: Create `TopicRepository` to handle data persistence.

- **Subtask 3.1**: Create `repositories/TopicRepository.py`.
- **Subtask 3.2**: Implement standard CRUD methods, using your existing `BaseRepository` patterns:

  ```python
  from typing import Optional, Dict, Any, List
  from sqlalchemy.orm import Session
  from orm.TopicModel import Topic
  from .BaseRepository import BaseRepository

  class TopicRepository(BaseRepository[Topic, int]):
      def __init__(self, db: Session):
          super().__init__(db, Topic)

      def get_by_name(self, user_id: str, name: str) -> Optional[Topic]:
          return (
              self.db.query(Topic)
              .filter(Topic.user_id == user_id, Topic.name == name)
              .first()
          )

      def list_topics(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Topic]:
          return (
              self.db.query(Topic)
              .filter(Topic.user_id == user_id)
              .offset(skip)
              .limit(limit)
              .all()
          )
  ```

- **Subtask 3.3**: Add additional queries if needed:
  - For example, `delete_topic`, `update_topic`, etc., or rely on the inherited ones from `BaseRepository`.

---

### 4. **Service Layer**

**Task**: Create a `TopicService` to orchestrate topic logic.

- **Subtask 4.1**: Create `services/TopicService.py`.
- **Subtask 4.2**: Typical methods:

  - `create_topic()`
  - `get_topic()`
  - `update_topic()`
  - `delete_topic()`
  - `list_topics()`

  ```python
  from typing import Optional, Dict, Any
  from fastapi import Depends, HTTPException, status
  from sqlalchemy.orm import Session
  from configs.Database import get_db_connection
  from repositories.TopicRepository import TopicRepository
  from domain.topic import TopicData
  from domain.exceptions import DomainException
  from schemas.pydantic.TopicSchema import (
      TopicCreate,
      TopicUpdate,
      TopicResponse,
  )

  class TopicService:
      def __init__(self, db: Session = Depends(get_db_connection)):
          self.db = db
          self.topic_repo = TopicRepository(db)

      def create_topic(self, user_id: str, data: TopicCreate) -> TopicResponse:
          # Convert schema to domain
          domain_data = data.to_domain(user_id)
          # Validate domain
          domain_data.validate()

          # Check if name already exists for user
          existing = self.topic_repo.get_by_name(user_id, domain_data.name)
          if existing:
              raise HTTPException(
                  status_code=status.HTTP_409_CONFLICT,
                  detail="Topic name already exists for user"
              )

          # Create via repository
          topic_orm = self.topic_repo.create(instance=domain_data.to_orm_model())
          self.db.commit()
          self.db.refresh(topic_orm)

          return TopicResponse.model_validate(topic_orm)

      # Similarly implement get_topic, update_topic, delete_topic, list_topics...
  ```

- **Subtask 4.3**: Consider advanced logic such as hooking into queue services or domain events. For now, we only do basic operations.

---

### 5. **Schema Layer**

**Task**: Define Pydantic schemas for request/response.

- **Subtask 5.1**: Create `schemas/pydantic/TopicSchema.py`:

  ```python
  from pydantic import BaseModel, Field, ConfigDict
  from typing import Optional
  from datetime import datetime
  from domain.topic import TopicData

  class TopicCreate(BaseModel):
      name: str = Field(..., min_length=1, max_length=255)
      icon: str = Field(..., min_length=1, max_length=255)

      def to_domain(self, user_id: str) -> TopicData:
          return TopicData(
              id=None,
              user_id=user_id,
              name=self.name,
              icon=self.icon,
          )

  class TopicUpdate(BaseModel):
      name: Optional[str] = Field(None, min_length=1, max_length=255)
      icon: Optional[str] = Field(None, min_length=1, max_length=255)

      def to_domain(self, existing: TopicData) -> TopicData:
          name = self.name if self.name is not None else existing.name
          icon = self.icon if self.icon is not None else existing.icon

          return TopicData(
              id=existing.id,
              user_id=existing.user_id,
              name=name,
              icon=icon,
              created_at=existing.created_at,
              updated_at=datetime.now()
          )

  class TopicResponse(BaseModel):
      id: int
      user_id: str
      name: str
      icon: str
      created_at: Optional[datetime] = None
      updated_at: Optional[datetime] = None

      model_config = ConfigDict(from_attributes=True)

      @classmethod
      def from_domain(cls, domain: TopicData) -> "TopicResponse":
          return cls(
              id=domain.id,
              user_id=domain.user_id,
              name=domain.name,
              icon=domain.icon,
              created_at=domain.created_at,
              updated_at=domain.updated_at
          )
  ```

- **Subtask 5.2**: If needed, add a `TopicList` for paginated responses.

---

### 6. **Router Layer** (Optional / If Required Now)

**Task**: Add a new router `routers/v1/TopicRouter.py` to handle CRUD operations.

- **Subtask 6.1**: Create `TopicRouter.py`.

  ```python
  from fastapi import APIRouter, Depends, status
  from schemas.pydantic.TopicSchema import (
      TopicCreate,
      TopicUpdate,
      TopicResponse,
  )
  from schemas.pydantic.CommonSchema import GenericResponse
  from services.TopicService import TopicService
  from dependencies import get_current_user
  from orm.UserModel import User

  router = APIRouter(prefix="/v1/topics", tags=["topics"])

  @router.post(
      "",
      response_model=GenericResponse[TopicResponse],
      status_code=status.HTTP_201_CREATED
  )
  async def create_topic(
      topic: TopicCreate,
      service: TopicService = Depends(),
      current_user: User = Depends(get_current_user),
  ):
      result = service.create_topic(user_id=current_user.id, data=topic)
      return GenericResponse(data=result, message="Topic created successfully")

  @router.get("/{topic_id}", response_model=GenericResponse[TopicResponse])
  async def get_topic(
      topic_id: int,
      service: TopicService = Depends(),
      current_user: User = Depends(get_current_user)
  ):
      # implement in service e.g. service.get_topic(topic_id, current_user.id)
      ...
  # etc.
  ```

- **Subtask 6.2**: Add routes for update, delete, list, ensuring ownership checks and domain validations.

- **Subtask 6.3**: Include `TopicRouter` in `main.py` or appropriate place:

  ```python
  from routers.v1.TopicRouter import router as topic_router

  app.include_router(topic_router)
  ```

---

### 7. **Testing**

**Task**: Add or update test suites to validate the new functionality.

- **Subtask 7.1**: Unit tests for domain validations: `test_domain_topic.py`.
- **Subtask 7.2**: Tests for repository CRUD operations: `test_topic_repository.py`.
- **Subtask 7.3**: Tests for service logic: `test_topic_service.py`.
- **Subtask 7.4**: Integration tests for new endpoints in `test_topic_router.py`.

---

### 8. **Documentation & Post-Deployment**

**Task**: Update your OpenAPI docs, README, or any usage docs to highlight new `Topic` endpoints.

- **Subtask 8.1**: Add docstrings in `TopicService`, `TopicRepository`, `TopicRouter`.
- **Subtask 8.2**: If necessary, mention usage or examples for the new `Topic` entity in your project’s top-level documentation or wiki.

---

## Future Steps

- **Foreign Key references**: Decide if `topic_id` should be added to tasks, notes, or other entities. This would require:

  1. Adding a new column in the ORM (e.g., `Task.topic_id = Column(...)`).
  2. Possibly referencing in domain classes & repositories.
  3. Potential migrations or relationships for existing data.

- **Enrichment**: If you want AI-based or other processing for topics, extend the `RoboService` logic or queue jobs.

- **Advanced Validation**: For instance, restricting `icon` to a valid emoji or a valid URL format.

---

## Summary

By following these tasks and subtasks, we ensure the new `Topic` entity is introduced in a manner consistent with the project’s existing design:

1. A clear **domain** model (`TopicData`) with validation.
2. An **ORM** mapping for database operations.
3. A dedicated **repository** for consistent CRUD queries.
4. A **service** that enforces business logic and domain validations.
5. **Schemas** for external I/O with Pydantic.
6. An optional **router** for simple REST endpoints.
7. Thorough **testing** and **documentation** to guarantee reliability and maintainability.

## Progress Tracking

### Implementation Status

#### Core Components

- [x] Domain Model (`domain/topic.py`)
  - [x] Basic structure
  - [x] Validation logic
  - [x] Type hints and TypeVar
  - [x] to_dict/from_dict methods
  - [x] Update methods
  - [x] Specific exceptions
  - [x] UTC timestamp handling
- [x] ORM Model (`orm/TopicModel.py`)
  - [x] Basic structure
  - [x] Relationships
  - [x] Field length constants
  - [x] from_dict/to_domain/from_domain methods
  - [x] Organized field structure
  - [x] Comprehensive docstrings
- [x] Repository (`repositories/TopicRepository.py`)
  - [x] Basic structure
  - [x] CRUD operations
  - [x] Domain-specific methods
  - [x] Error handling with specific exceptions
  - [x] User-scoped queries
- [x] Service (`services/TopicService.py`)
  - [x] Basic structure
  - [x] CRUD operations
  - [x] Domain model methods
  - [x] Error handling with specific exceptions
  - [x] Transaction management
- [x] Schemas (`schemas/pydantic/TopicSchema.py`)
  - [x] Basic structure
  - [x] Domain conversion methods
  - [x] Example values
  - [x] Field descriptions
  - [x] Response wrappers (using GenericResponse and PaginationResponse)
- [x] Router (`routers/v1/TopicRouter.py`)
  - [x] Basic CRUD endpoints
  - [x] Authentication integration
  - [x] Error handling
  - [x] Pagination support
- [x] Database Schema (`scripts/init_database.sql`)

#### Integration

- [x] User Model Relationship
- [x] Unit Tests
  - [x] Domain Tests (validate, update methods, exceptions)
  - [x] Repository Tests (CRUD, error cases)
  - [x] Service Tests (business logic, transactions)
  - [x] Router Tests (endpoints, auth, pagination)
- [ ] Integration Tests
  - [ ] End-to-end flow tests
  - [ ] Database interaction tests
  - [ ] API response format tests
- [ ] API Documentation
  - [ ] OpenAPI descriptions
  - [ ] Usage examples
  - [ ] Integration guides

### Next Steps

1. Add integration tests (High Priority)
   - End-to-end flow tests
   - Database interaction tests
   - API response format tests
2. Update API documentation (Medium Priority)
   - OpenAPI descriptions
   - Usage examples
   - Integration guides

### Current Focus

1. Create integration test suite (High Priority)
   - Set up test database fixtures
   - Implement end-to-end flow tests
   - Add database interaction tests
   - Verify API response formats
2. Update API documentation (Medium Priority)

### Known Issues

1. ~~Linter error in `domain/topic.py` regarding type hints~~ (Fixed)
2. ~~Need to implement comprehensive test suite~~ (Done)
3. ~~Need to update other layers to use new domain model patterns~~ (Done)
4. ~~Schema layer needs example values and field descriptions~~ (Done)
5. Missing integration tests for end-to-end validation
