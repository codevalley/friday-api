Below is a **step-by-step** guide on how to introduce a **new entity** into this project’s four-layer architecture (Domain → Repository → Service → Router), along with the supporting schemas and tests. It's structured to match the patterns currently used in your codebase (Activity, Moment, Note, User, etc.), so everything remains consistent.

---

## 1. Overview of the 4-Layer Flow

Here’s the **typical flow** when adding a brand-new entity (for illustration, let’s call it `Task`—imagine a simple “task” that a user can create and mark as done, with optional notes or something like that). The same steps apply to any new entity:

1. **Domain Layer** (`domain/Task.py`, plus maybe `domain/exceptions.py` updates):  
   - Create a domain model `TaskData` or similarly named.
   - Implement validations, domain logic, specialized domain exceptions if needed.
2. **Repository Layer** (`repositories/TaskRepository.py`):  
   - Create an ORM model `Task` in `orm/TaskModel.py` (or if you want a separate file).
   - Then create `TaskRepository` to handle DB queries/CRUD for `Task`.
3. **Service Layer** (`services/TaskService.py`):  
   - Create a `TaskService` that orchestrates domain logic + repository calls + error handling, and optionally transforms domain exceptions into `HTTPException`.
4. **Router Layer** (`routers/v1/TaskRouter.py`):  
   - Create a new FastAPI router with endpoints for creating, retrieving, listing, updating, deleting tasks (whatever is needed).
   - Optionally add `GraphQL` types/mutations if you also support GraphQL.

Additionally, you’ll add supporting **Pydantic** schemas for request and response in `schemas/pydantic/`, **GraphQL** types/mutations in `schemas/graphql/`, and **unittest** coverage for domain, repository, service, and router.

Let’s break down the steps in detail.

---

## 2. Domain Layer

### 2.1. Create Domain Model

Inside `domain/Task.py` (or a similarly named file), define the new domain class, e.g.:

```python
# domain/task.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from domain.exceptions import TaskValidationError
# or use domain.values if you have specialized ValueObjects

@dataclass
class TaskData:
    """Domain model for Task.
    
    Represents a single user task with optional notes and statuses.
    """

    title: str
    user_id: str
    description: Optional[str] = None
    is_done: bool = False
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        self.validate()

    def validate(self):
        """Validates the TaskData instance."""
        if not self.title or not isinstance(self.title, str):
            raise TaskValidationError("Title must be a non-empty string")
        if not self.user_id:
            raise TaskValidationError("user_id is required")

        # Additional domain rules can go here...
```

### 2.2. Create or Update Domain Exceptions (Optional)

In `domain/exceptions.py`, if we want a specialized exception, we might do:

```python
# domain/exceptions.py

class TaskValidationError(ValidationException):
    """Raised when Task domain validation fails."""
    pass
```

*(If you just want to reuse something like `ValidationException` or `ValueError`, that’s fine. It’s optional.)*

### 2.3. (Optional) Value Objects

If `Task` has something like a `TaskStatus` or `DueDate` with domain constraints, you could define them in `domain/values.py`. For example:

```python
# domain/values.py

@dataclass(frozen=True)
class TaskStatus:
    # example if needed
    value: str
    ...
```

*(Only do this if you need advanced domain logic around the status or date fields.)*

---

## 3. Repository Layer

### 3.1. ORM Model

Add an ORM model in `orm/TaskModel.py`. For instance:

```python
# orm/TaskModel.py

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from datetime import datetime
from orm.BaseModel import EntityMeta

class Task(EntityMeta):
    """Task ORM model for storing tasks in the database."""

    __tablename__ = "tasks"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),  # or your user PK type
        nullable=False
    )
    title: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[str] = Column(Text, nullable=True)
    is_done: Mapped[bool] = Column(Boolean, default=False)
    created_at: Mapped[datetime] = Column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationship back to the User or other models
    # user: Mapped[User] = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}')>"
```

*(Add constraints, indexes, etc. as needed. Ensure `user_id` references your `users` table if you have a foreign key. If you want a relationship back to `User`, do so, then add a matching relationship in `UserModel.py` if desired.)*

### 3.2. TaskRepository

In `repositories/TaskRepository.py`:

```python
# repositories/TaskRepository.py

from typing import Optional, List
from sqlalchemy.orm import Session
from orm.TaskModel import Task
from repositories.BaseRepository import BaseRepository

class TaskRepository(BaseRepository[Task, int]):
    """Repository for managing Task entities in the database."""

    def __init__(self, db: Session):
        super().__init__(db, Task)

    def list_tasks_for_user(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        return (
            self.db.query(Task)
            .filter(Task.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    # Additional queries if needed...
```

*(We’re subclassing your `BaseRepository` to reuse the standard `create`, `get`, `delete`, etc. We can add specialized queries if needed, e.g. `list_tasks_for_user` above.)*

---

## 4. Service Layer

### 4.1. `TaskService`

Create `services/TaskService.py`:

```python
# services/TaskService.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from configs.Database import get_db_connection
from domain.task import TaskData
from domain.exceptions import TaskValidationError
from repositories.TaskRepository import TaskRepository
from schemas.pydantic.TaskSchema import (
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from utils.validation import validate_pagination

class TaskService:
    def __init__(self, db: Session = Depends(get_db_connection)):
        self.db = db
        self.task_repo = TaskRepository(db)

    def create_task(self, task_data: TaskCreate, user_id: str) -> TaskResponse:
        # Convert Pydantic input -> domain model
        domain_task = task_data.to_domain(user_id)

        # Domain validation might raise TaskValidationError, so catch:
        try:
            domain_task.validate()
        except TaskValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        # Create DB model
        db_task = self.task_repo.create(
            title=domain_task.title,
            user_id=domain_task.user_id,
            description=domain_task.description,
            is_done=domain_task.is_done,
        )

        # The create call will commit + refresh, so db_task.id and db_task.created_at are set
        return TaskResponse.from_orm(db_task)

    def get_task(self, task_id: int, user_id: str) -> TaskResponse:
        db_task = self.task_repo.get_by_user(task_id, user_id)
        if not db_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return TaskResponse.from_orm(db_task)

    def list_tasks(self, user_id: str, page: int = 1, size: int = 50):
        validate_pagination(page, size)
        skip = (page - 1) * size
        items = self.task_repo.list_tasks_for_user(user_id, skip=skip, limit=size)
        total = len(items)  # or do a separate count
        # Build the response. Possibly use a PaginationResponse or a specialized TaskList Pydantic
        return {
            "items": [TaskResponse.from_orm(t) for t in items],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    def update_task(self, task_id: int, user_id: str, data: TaskUpdate) -> TaskResponse:
        db_task = self.task_repo.get_by_user(task_id, user_id)
        if not db_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        # Apply updates
        update_dict = data.model_dump(exclude_unset=True)
        updated_task = self.task_repo.update(task_id, update_dict)
        if not updated_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or update failed",
            )

        return TaskResponse.from_orm(updated_task)

    def delete_task(self, task_id: int, user_id: str) -> bool:
        # Basic check
        db_task = self.task_repo.get_by_user(task_id, user_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")

        return self.task_repo.delete(task_id)
```

### 4.2. Domain vs. HTTP

Observe how we handle domain errors (`TaskValidationError`) and re-raise them as `HTTPException`. This keeps the domain pure. The service is “HTTP-aware.”

---

## 5. Router Layer

### 5.1. FastAPI Router

Create `routers/v1/TaskRouter.py`:

```python
# routers/v1/TaskRouter.py
from fastapi import APIRouter, Depends, status
from schemas.pydantic.TaskSchema import (
    TaskCreate,
    TaskUpdate,
)
from schemas.pydantic.CommonSchema import GenericResponse, MessageResponse
from services.TaskService import TaskService
from dependencies import get_current_user
from orm.UserModel import User

router = APIRouter(
    prefix="/v1/tasks",
    tags=["tasks"]
)

@router.post(
    "",
    response_model=GenericResponse,  # or a GenericResponse[TaskResponse]
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    task: TaskCreate,
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
):
    created = service.create_task(task, current_user.id)
    return {"data": created, "message": "Task created successfully"}

@router.get("")
def list_tasks(
    page: int = 1,
    size: int = 50,
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
):
    result = service.list_tasks(current_user.id, page, size)
    return {"data": result, "message": "Retrieved tasks"}

@router.get("/{task_id}")
def get_task(
    task_id: int,
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
):
    result = service.get_task(task_id, current_user.id)
    return {"data": result}

@router.put("/{task_id}")
def update_task(
    task_id: int,
    task: TaskUpdate,
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
):
    result = service.update_task(task_id, current_user.id, task)
    return {"data": result, "message": "Task updated successfully"}

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    service: TaskService = Depends(),
    current_user: User = Depends(get_current_user),
):
    service.delete_task(task_id, current_user.id)
    return {"message": "Task deleted successfully"}
```

*(Now you have a standard CRUD router: `POST /v1/tasks`, `GET /v1/tasks`, etc. The router uses the `TaskService` to handle logic. The `get_current_user` dependency ensures the user is known, so we can tie tasks to that user.)*

---

## 6. Pydantic Schemas

### 6.1. Request and Response Schemas

Create `schemas/pydantic/TaskSchema.py`:

```python
# schemas/pydantic/TaskSchema.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from domain.task import TaskData

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_done: bool = False

    def to_domain(self, user_id: str) -> TaskData:
        return TaskData(
            title=self.title,
            description=self.description,
            is_done=self.is_done,
            user_id=user_id,
        )

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_done: Optional[bool] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    is_done: bool
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    # We can construct from DB or domain if we want:
    @classmethod
    def from_orm(cls, orm_model):
        return cls(
            id=orm_model.id,
            title=orm_model.title,
            description=orm_model.description,
            is_done=orm_model.is_done,
            user_id=orm_model.user_id,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )

    model_config = ConfigDict(from_attributes=True)
```

*(When the service returns a Task model from the DB, you call `TaskResponse.from_orm(db_task)`. For creation, you do `TaskCreate(...).to_domain(user_id)`. This is consistent with your current approach for `Note` or `Moment`.)*

---

## 7. Tests

### 7.1. Domain Tests

Create `__tests__/unit/domain/test_task_data.py`, for instance:

```python
# __tests__/unit/domain/test_task_data.py
import pytest
from datetime import datetime
from domain.task import TaskData
from domain.exceptions import TaskValidationError

def test_task_data_valid():
    task = TaskData(
        title="My Task",
        user_id="test_user"
    )
    task.validate()  # Should not raise

def test_task_data_invalid_title():
    with pytest.raises(TaskValidationError):
        TaskData(title="", user_id="test_user")

def test_task_data_missing_user():
    with pytest.raises(TaskValidationError):
        TaskData(title="Title", user_id="")
```

### 7.2. Repository Tests

Create `__tests__/unit/repositories/test_task_repository.py`:

```python
import pytest
from repositories.TaskRepository import TaskRepository
from orm.TaskModel import Task

@pytest.fixture
def task_repository(test_db_session):
    return TaskRepository(test_db_session)

def test_create_task_success(task_repository, sample_user):
    # sample_user fixture ensures the user is in the DB
    new_task = task_repository.create(
        title="Test Task",
        user_id=sample_user.id,
        description="Task desc",
        is_done=False,
    )
    assert new_task.id is not None
    assert new_task.title == "Test Task"
    assert new_task.user_id == sample_user.id
```

*(Use a fixture like `sample_user` that inserts a user so the foreign key is valid.)*

### 7.3. Service Tests

`__tests__/unit/services/test_task_service.py`:

```python
import pytest
from services.TaskService import TaskService
from schemas.pydantic.TaskSchema import TaskCreate

@pytest.fixture
def task_service(test_db_session):
    return TaskService(test_db_session)

def test_create_task_success(task_service, sample_user):
    data = TaskCreate(
        title="Service Task",
        description="A test task"
    )
    result = task_service.create_task(data, sample_user.id)
    assert result.title == "Service Task"
    assert result.user_id == sample_user.id
    assert result.id is not None
```

### 7.4. Router Tests

`__tests__/unit/routers/test_task_router.py`:

```python
import pytest
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials
from main import app  # or create a special fixture for your app
from schemas.pydantic.TaskSchema import TaskCreate
from orm.UserModel import User

# or create an @pytest.fixture that sets up the test app if needed

@pytest.fixture
def mock_auth_credentials():
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-token")

@pytest.fixture
def client(test_db_session, mock_auth_credentials, sample_user):
    # Overriding get_current_user to return the sample_user
    def override_get_current_user():
        return sample_user

    app.dependency_overrides["dependencies.get_current_user"] = override_get_current_user
    # We also rely on the real DB from test_db_session
    return TestClient(app)

def test_create_task_success(client):
    payload = {
        "title": "Router Task",
        "description": "From router test"
    }
    response = client.post("/v1/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["title"] == "Router Task"
    assert data["id"] is not None
```

---

## 8. Summarized Steps

1. **Domain**  
   - Add `TaskData` in `domain/task.py` with your business logic.  
   - Add domain exceptions if needed.  
2. **ORM & Repository**  
   - In `orm/TaskModel.py`, define the SQLAlchemy `Task` model.  
   - In `repositories/TaskRepository.py`, define `TaskRepository` (subclass `BaseRepository`).  
3. **Service**  
   - In `services/TaskService.py`, define a `TaskService` class that uses your `TaskRepository`.  
   - Perform domain validation, handle domain exceptions, raise `HTTPException` if needed.  
4. **Router**  
   - In `routers/v1/TaskRouter.py`, create endpoints (POST, GET, etc.).  
   - They call the `TaskService` methods.  
5. **Pydantic Schemas**  
   - In `schemas/pydantic/TaskSchema.py`, define `TaskCreate`, `TaskUpdate`, and `TaskResponse` (with `.to_domain()` and `.from_orm()`).  
6. **Tests**  
   - Domain tests: `test_task_data.py`  
   - Repository tests: `test_task_repository.py`  
   - Service tests: `test_task_service.py`  
   - Router tests: `test_task_router.py`  

That’s it! Following these steps keeps your approach consistent with existing entities (`Note`, `Moment`, `Activity`), ensuring each new entity flows through **domain** → **repository** → **service** → **router** with separate Pydantic schemas for input/output.

---

## Key Philosophy & Guiding Principles

1. **Strict Layer Separation**  
   Each of the four layers—**Domain**, **Repository**, **Service**, **Router**—should remain independent in terms of functionality:
   - **Domain**: Business logic, validation rules, domain-specific exceptions. **No** HTTP or DB code. 
   - **Repository**: Strictly data access (SQLAlchemy or other). **No** domain logic or HTTP concerns. 
   - **Service**: Coordination logic. Catches domain exceptions, re-raises as `HTTPException`. Orchestrates domain + repository calls. 
   - **Router**: HTTP endpoints or GraphQL resolvers. Minimal logic: pass inputs to the service, return service results.  

   **Why**: Each layer has a single responsibility, reducing coupling and making it easier to change or test each piece independently.

2. **Domain Models Are the Single Source of Truth**  
   The `domain/` classes define how entities (Activity, Moment, Note, Task, etc.) behave. They own the business rules. The Pydantic or GraphQL schemas exist to translate “external data” to or from your domain.  

   **Why**: This ensures your domain logic doesn’t get scattered in multiple places. The domain stays consistent even if you add new transport layers (like another API or a different UI).

3. **Pydantic Schemas for I/O, Not for Business Logic**  
   Pydantic schemas in `schemas/pydantic/` exist to handle request validation, shaping the data for domain usage. They do not contain advanced domain rules. 

   **Why**: This approach clarifies the difference between “request validation” and “deeper business constraints” in the domain.

4. **Service as an Application Facade**  
   Services are “HTTP-aware” but domain-agnostic. They handle domain exceptions (like `ActivityValidationError`) and raise `HTTPException` if needed. They also orchestrate multiple repositories if needed.  

   **Why**: This structure keeps your domain pure while providing a clean interface for the router.

5. **Repository Just for Data Persistence**  
   Each repository does CRUD queries and minor filtering or pagination. Avoid placing domain logic or complex business rules in the repository.  

   **Why**: Minimizes duplication and ensures your logic stays in the domain/services.

---

## Pitfalls to Avoid

1. **Leaking Domain Concerns into Other Layers**  
   - **Domain** must not import or raise `fastapi.HTTPException`.  
   - **Repository** should not know about domain `ValidationError` or business rules. 
   - **Service** might do domain logic if it duplicates code that already exists in the domain—avoid that.  

2. **Partial Mocking in Router Tests**  
   - If you only partially mock the service or DB, you can end up with DB constraints not being satisfied (foreign-key errors, missing IDs).  
   - Either use a **fully mocked** approach (where the service returns “fake” fully-populated objects) or a **fully real** approach (use the test DB).  

3. **Inconsistent Error Handling**  
   - If domain code sometimes raises domain exceptions and sometimes raises `HTTPException`, it can cause confusion.  
   - Keep it consistent: domain → domain exceptions, service → `HTTPException`.  

4. **Repository Bloat**  
   - Repositories can balloon if we keep adding specialized queries. If you see repeated patterns, consider factoring them out or ensuring they truly belong at the repository level.  

5. **Skipping Tests in One Layer**  
   - Because each layer has distinct logic, skipping tests for domain or service can cause regressions.  
   - Unit tests in domain, repository, service, and router are all important for coverage and confidence.

---

## Keeping Code Manageable & Scalable

1. **Naming & Structure**  
   - Consistent file naming (e.g. `TaskModel.py`, `TaskRepository.py`, `TaskService.py`, `TaskRouter.py`) helps new devs orient.  
   - Follow the same patterns for “create, get, list, update, delete” to keep the codebase uniform.

2. **Use Common Patterns & Utilities**  
   - If you have repeated logic (pagination, color validation, date constraints), centralize it in `utils/validation` or a shared library.  
   - For pagination, keep the same approach (like `page` and `size` query params, `validate_pagination(page, size)` in the service, etc.).

3. **Testing Strategy**  
   - **Domain**: Unit test each new entity’s validation logic thoroughly.  
   - **Repository**: Use a real test DB session to confirm constraints and foreign keys.  
   - **Service**: Test real domain calls plus repository calls, or mock the repository if you prefer.  
   - **Router**: Perform integration-style tests with an actual DB session or a fully mocked service. Keep it consistent to avoid partial mocking pitfalls.

4. **Incremental Evolution**  
   - When you add new domain rules or fields, update the domain model first. Then adapt the repository, service, router layers.  
   - The separate tests at each layer help ensure each piece is still correct.

5. **Use Domain Exceptions**  
   - If a new domain rule requires a custom error, define it in `domain/exceptions.py`. The service can catch it and raise an HTTP 400 or 422 as appropriate.  
   - Consistent usage clarifies the difference between domain issues vs. repository failures.

6. **Embrace the “Single Source of Truth”**  
   - For each new feature, always ask: “Which domain entity is responsible for that rule or data?” Then implement it in that entity’s domain logic.  
   - Resist putting the logic in the router or repository.  

7. **Refactoring is Easier with Separation**  
   - Because each layer is clearly defined, if you later decide to switch from MySQL to Postgres, only your repository code changes.  
   - If you add a new transport mechanism (like a gRPC server or a new GraphQL field), you mostly only add new router/resolvers. The domain and service remain the same.

---

### Summarized Advice for New Features

- **Add Domain**: Create the new entity’s domain model (`XYZData`), ensure all validations are there.  
- **Add Repository**: Create the SQLAlchemy model (`XYZ`) and a repository class if needed.  
- **Add Service**: Orchestrate domain logic + repository calls. Catch domain errors, raise `HTTPException` if needed.  
- **Add Router**: Provide endpoints (`POST`, `GET`, etc.). Return appropriate Pydantic response schemas.  
- **Add/Update Tests**: Domain tests, repository tests, service tests, router tests. Keep them consistent and don’t skip layers.

By sticking to these guidelines, you ensure that each new feature (or entity) remains **easy to reason about**, **test**, and **extend**—keeping the overall codebase in good health.