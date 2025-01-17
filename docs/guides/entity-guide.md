# Adding a New Entity in the Four-Layer Architecture

Below is a **step-by-step** guide on how to introduce a **new entity** into this project's four-layer architecture (Domain → Repository → Service → Router), along with the supporting schemas and tests. It's structured to match the patterns currently used (Activity, Moment, Note, User, etc.), so everything remains consistent.

---

## 1. Overview of the 4-Layer Flow

Here’s the **typical flow** when adding a brand-new entity (for illustration, we’ll call it `Task`—imagine a “task” that a user can create and mark as done). These same steps apply to **any** new entity:

1. **Domain Layer** (`domain/Task.py` + possibly `domain/exceptions.py` updates)
   - Create a domain model `TaskData` (or similarly named).
   - Implement validations, domain logic, specialized domain exceptions if needed.
2. **Repository Layer** (`repositories/TaskRepository.py`)
   - Create an ORM model `Task` in `orm/TaskModel.py`.
   - Then create `TaskRepository` to handle DB queries/CRUD for `Task`.
3. **Service Layer** (`services/TaskService.py`)
   - Create a `TaskService` that orchestrates domain logic + repository calls, handles domain exceptions, etc.
4. **Router Layer** (`routers/v1/TaskRouter.py`)
   - Create a new FastAPI router with endpoints for creating, retrieving, listing, updating, and/or deleting tasks.

Additionally, you’ll add supporting **Pydantic** schemas for request/response in `schemas/pydantic/`, and unittests for domain, repository, service, and router.

Below is a detailed breakdown.

---

## 2. Domain Layer

### 2.1. Create Domain Model

Inside `domain/Task.py` (or similarly named file), define your new domain class:

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
        """Validates this domain model instance."""
        if not self.title or not isinstance(self.title, str):
            raise TaskValidationError("Title must be a non-empty string")
        if not self.user_id:
            raise TaskValidationError("user_id is required")
        # Additional domain rules can go here...
```

### 2.2. Create or Update Domain Exceptions (Optional)

If you want a specialized exception:

```python
# domain/exceptions.py

class TaskValidationError(ValidationException):
    """Raised when Task domain validation fails."""
    pass
```

_(You can also reuse existing `ValidationException` / `ValueError`. Your choice.)_

### 2.3. Optional: Value Objects

If `Task` has special fields (like a `TaskStatus` or `DueDate` with advanced constraints), define them in `domain/values.py`:

```python
# domain/values.py

@dataclass(frozen=True)
class TaskStatus:
    value: str
    # Potential validations or transitions...
```

_(Only do this if you need advanced domain logic. Otherwise, straightforward fields in `TaskData` might suffice.)_

---

## 3. Repository Layer

### 3.1. ORM Model

Add a SQLAlchemy model in `orm/TaskModel.py`:

```python
# orm/TaskModel.py

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped
from datetime import datetime
from orm.BaseModel import EntityMeta

class Task(EntityMeta):
    """Task ORM model for storing tasks in the database."""

    __tablename__ = "tasks"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),  # or adapt to match your user PK type
        nullable=False
    )
    title: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[str] = Column(Text, nullable=True)
    is_done: Mapped[bool] = Column(Boolean, default=False)
    created_at: Mapped[datetime] = Column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}')>"
```

**Tip:**

- If you need a unique constraint (e.g., `topic_name` unique per user), use `UniqueConstraint("user_id", "name", name="...")` or an index.
- For mandatory fields, ensure `nullable=False`.
- For foreign keys, adapt to match your user’s PK type.

### 3.2. Adding a Database Migration

If you use a migration tool like **Alembic**, remember to generate a migration script:

```bash
alembic revision --autogenerate -m "Add Task entity"
alembic upgrade head
```

_(This ensures the new `tasks` table is created in your DB.)_

### 3.3. TaskRepository

Create `repositories/TaskRepository.py`:

```python
# repositories/TaskRepository.py

from typing import List
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
```

_(We’re subclassing your `BaseRepository` to reuse `create`, `get`, `delete`, etc. We add specialized queries like `list_tasks_for_user` if needed.)_

**Handling Partial Updates**  
For partial updates (e.g., only updating `title` or `is_done`), typically your `update` method in `BaseRepository` or `TaskRepository` merges only provided fields. Make sure to do something like:

```python
def update_task_fields(self, task_id: int, data: dict) -> Optional[Task]:
    task = self.get(task_id)
    if not task:
        return None
    for key, value in data.items():
        setattr(task, key, value)
    self.db.commit()
    self.db.refresh(task)
    return task
```

---

## 4. Service Layer

### 4.1. `TaskService`

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
        domain_task = task_data.to_domain(user_id)
        try:
            domain_task.validate()
        except TaskValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        db_task = self.task_repo.create(
            title=domain_task.title,
            user_id=domain_task.user_id,
            description=domain_task.description,
            is_done=domain_task.is_done,
        )
        # BaseRepository typically commits and refreshes automatically
        return TaskResponse.model_validate(db_task)

    def get_task(self, task_id: int, user_id: str) -> TaskResponse:
        db_task = self.task_repo.get_by_user(task_id, user_id)
        if not db_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return TaskResponse.model_validate(db_task)

    def list_tasks(self, user_id: str, page: int = 1, size: int = 50):
        validate_pagination(page, size)
        skip = (page - 1) * size
        items = self.task_repo.list_tasks_for_user(user_id, skip=skip, limit=size)
        total = len(items)  # or a count query
        return {
            "items": [TaskResponse.model_validate(t) for t in items],
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

        update_dict = data.model_dump(exclude_unset=True)
        updated = self.task_repo.update(task_id, update_dict)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update task",
            )
        return TaskResponse.model_validate(updated)

    def delete_task(self, task_id: int, user_id: str) -> bool:
        db_task = self.task_repo.get_by_user(task_id, user_id)
        if not db_task:
            raise HTTPException(404, detail="Task not found")
        return self.task_repo.delete(task_id)
```

---

## 5. Router Layer

### 5.1. FastAPI Router

Create `routers/v1/TaskRouter.py`:

```python
# routers/v1/TaskRouter.py
from fastapi import APIRouter, Depends, status
from schemas.pydantic.TaskSchema import TaskCreate, TaskUpdate
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
    response_model=GenericResponse,  # or GenericResponse[TaskResponse]
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

_(Now you have a CRUD router: `POST /v1/tasks`, `GET /v1/tasks`, `GET /v1/tasks/{task_id}`, etc.)_

---

## 6. Pydantic Schemas

### 6.1. Request and Response

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

    model_config = ConfigDict(from_attributes=True)
```

---

## 7. Tests

### 7.1. Domain Tests

Create `__tests__/unit/domain/test_task_data.py`:

```python
import pytest
from domain.task import TaskData
from domain.exceptions import TaskValidationError

def test_task_data_valid():
    task = TaskData(title="My Task", user_id="user123")
    task.validate()  # Should not raise

def test_task_data_no_title():
    with pytest.raises(TaskValidationError):
        TaskData(title="", user_id="user123")
```

### 7.2. Repository Tests

`__tests__/unit/repositories/test_task_repository.py`:

```python
import pytest
from repositories.TaskRepository import TaskRepository

@pytest.fixture
def task_repository(test_db_session):
    return TaskRepository(test_db_session)

def test_create_task(task_repository, sample_user):
    new_task = task_repository.create(
        title="Test Repo Task",
        user_id=sample_user.id,
        is_done=False,
    )
    assert new_task.id is not None
    assert new_task.title == "Test Repo Task"
```

### 7.3. Service Tests

`__tests__/unit/services/test_task_service.py`:

```python
import pytest
from services.TaskService import TaskService
from schemas.pydantic.TaskSchema import TaskCreate

@pytest.fixture
def task_service(test_db_session):
    return TaskService(test_db_session)

def test_create_task_service(task_service, sample_user):
    data = TaskCreate(title="Service Task")
    result = task_service.create_task(data, sample_user.id)
    assert result.title == "Service Task"
    assert result.id is not None
    assert result.user_id == sample_user.id
```

### 7.4. Router Tests

`__tests__/unit/routers/test_task_router.py`:

```python
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client(test_db_session, sample_user):
    # Overriding get_current_user to return the sample_user
    def override_get_current_user():
        return sample_user

    app.dependency_overrides["dependencies.get_current_user"] = override_get_current_user
    return TestClient(app)

def test_create_task_router(client):
    payload = {"title": "Router Task"}
    response = client.post("/v1/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["title"] == "Router Task"
    assert data["id"] is not None
```

---

## 8. Summarized Steps

1. **Domain**  
   Add a new domain model (e.g., `TaskData`) in `domain/`, ensure validations are present.
2. **ORM & Repository**  
   In `orm/`, define the SQLAlchemy model. In `repositories/`, create a repository (optionally subclassing `BaseRepository`).
3. **Service**  
   In `services/`, create a `TaskService` that orchestrates domain validations, calls repository methods, and raises `HTTPException` if needed.
4. **Router**  
   In `routers/v1/`, add a router for the entity (CRUD endpoints).
5. **Schemas**  
   In `schemas/pydantic/`, add create/update/response schemas.
6. **Tests**  
   Write domain, repository, service, and router tests, each focusing on its own layer.

---

## Key Philosophy & Guiding Principles

1. **Strict Layer Separation**

   - **Domain**: Business rules, domain exceptions, validations.
   - **Repository**: Data access (SQLAlchemy or otherwise).
   - **Service**: Orchestrates domain & repository, transforms domain exceptions to HTTP exceptions.
   - **Router**: Minimal HTTP logic, delegates to `Service`.

2. **Domain Models as Single Source of Truth**  
   The domain classes (`TaskData`, etc.) define the business rules. Pydantic schemas handle only I/O transformations (requests/responses).

3. **Use Domain Exceptions**  
   Domain code raises `TaskValidationError` (or similar). The service layer catches and re-raises as `HTTPException` if needed.

4. **Migration Awareness**  
   Any changes to the ORM layer likely need a migration if your database is in production. Tools like **Alembic** or **flask-migrate** let you generate and apply migrations consistently.

5. **Tests at Each Layer**

   - **Domain**: Test validations and logic in isolation.
   - **Repository**: Test DB-level operations (possibly with an in-memory or test DB).
   - **Service**: Test real domain + repository calls (or mock the repository).
   - **Router**: Test endpoints with `TestClient`, verifying status codes and JSON responses.

6. **Consistent Patterns**
   - For pagination, use the same approach (`page`, `size`, `validate_pagination`).
   - For partial updates, accept optional fields and only update what’s present.
   - For unique constraints (e.g., `name` must be unique per user), define either a DB unique index or check inside the repository before creation, raising a domain exception or `HTTPException` if it fails.

---

## Common Pitfalls to Avoid

1. **Leaking Domain Logic into the Router or Repository**  
   Keep domain logic (validations, special rules) in the domain class. The router should be minimal, delegating to the service.
2. **Skipping Tests in One Layer**  
   Because each layer has distinct responsibilities, skipping tests can lead to hidden bugs.
3. **Forgetting Migrations**  
   When the schema changes, ensure you generate and apply the appropriate migration in your dev/staging/production environments.
4. **Inconsistent Error Handling**  
   Domain raises domain exceptions, service catches them, router deals with `HTTPException`. Keep it consistent.

---

### Conclusion

Following these steps, you can **add any new entity** (e.g., Topics, Tasks, Labels, Projects) to your project without disturbing the existing codebase’s structure. Stick to the four-layer approach—**Domain** → **Repository** → **Service** → **Router**—plus consistent **Pydantic** schemas and thorough testing at each layer. This keeps your architecture clean, maintainable, and easy to extend.
