Below is a comprehensive step-by-step guide on how to add a new entity to the existing API. This guide assumes the following:

- You are familiar with basic Python, FastAPI, SQLAlchemy, and Strawberry GraphQL.
- You have reviewed the current code structure and understand the layered architecture (domain, orm, repositories, services, routers, schemas).
- You have set up your development environment according to the project's README.

This guide will walk you through the entire process of introducing a new entity named `Project` (as an example) into the system. You can replace `Project` with the actual name of your entity.

## Overview

When adding a new entity:
1. Define the domain model and validation rules.
2. Create the ORM model and database migrations if needed.
3. Create Pydantic schemas for input/output.
4. Create a repository for data access.
5. Create service layer methods for business logic.
6. Add GraphQL schema definitions (types, queries, mutations).
7. Add REST API endpoints (routers).
8. Update OpenAPI documentation.
9. Add database table definition.
10. Write tests (unit tests, integration tests).
11. Update documentation and ensure both GraphQL and OpenAPI endpoints are accessible via the respective playground interfaces (GraphiQL and /docs).

## Folder Structure Recap

The project is organized as follows (simplified):

```
configs/
domain/
    __init__.py
    activity.py
    moment.py
    user.py
    # Add project.py here
metadata/
    Tags.py  # Update with new entity's tags
orm/
    ActivityModel.py
    MomentModel.py
    UserModel.py
    # Add ProjectModel.py here
repositories/
    ActivityRepository.py
    MomentRepository.py
    UserRepository.py
    # Add ProjectRepository.py here
routers/
    v1/
        ActivityRouter.py
        MomentRouter.py
        AuthRouter.py
        # Add ProjectRouter.py here
schemas/
    pydantic/
        ActivitySchema.py
        MomentSchema.py
        UserSchema.py
        # Add ProjectSchema.py
    graphql/
        types/
            Activity.py
            Moment.py
            User.py
            # Add Project.py
        mutations/
            ActivityMutation.py
            MomentMutation.py
            UserMutation.py
            # Add ProjectMutation.py
        # Update Query.py and Mutation.py to include Project queries and mutations
scripts/
    init_database.sql  # Add table definition here
services/
    ActivityService.py
    MomentService.py
    UserService.py
    # Add ProjectService.py here
utils/
    # Validation, error handling, etc.
main.py  # Update to include new router
```

---

## Step-by-Step Instructions

### 1. Domain Model

Domain models represent the core business logic and data validation rules. Let’s define `ProjectData` (our new entity) with strict validation rules.

**File:** `domain/project.py`
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import re

@dataclass
class ProjectData:
    name: str
    description: str
    owner_id: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Project name must be a non-empty string")
        if len(self.name) < 3:
            raise ValueError("Project name must be at least 3 characters")
        if not self.description or not isinstance(self.description, str):
            raise ValueError("Project description must be a non-empty string")
        if not self.owner_id or not isinstance(self.owner_id, str):
            raise ValueError("owner_id must be a non-empty string")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data["description"],
            owner_id=data["owner_id"],
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
```

Add `ProjectData` to `domain/__init__.py` so it’s easily importable:

```python
from .project import ProjectData

__all__ = ["ActivityData", "MomentData", "UserData", "ProjectData"]
```

### 2. ORM Model

The ORM model connects the domain with the database. It uses SQLAlchemy to define the `projects` table.

**File:** `orm/ProjectModel.py`
```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, Mapped
from datetime import datetime
from orm.BaseModel import EntityMeta
from orm.UserModel import User

class Project(EntityMeta):
    __tablename__ = "projects"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    owner_id: Mapped[str] = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[str] = Column(String(1000), nullable=False)
    created_at: Mapped[datetime] = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    owner: Mapped[User] = relationship("User", back_populates="projects")

    __table_args__ = (
        CheckConstraint("name IS NOT NULL AND name != ''", name="check_name_not_empty"),
        CheckConstraint("description IS NOT NULL AND description != ''", name="check_description_not_empty"),
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"
```

In `orm/UserModel.py`, add a relationship so users can have projects:

```python
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
```

### 3. Pydantic Schemas

These schemas define the request/response formats used by the API. They are separate from domain models and ORM models.

**File:** `schemas/pydantic/ProjectSchema.py`
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from domain.project import ProjectData

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=3, description="Name of the project")
    description: str = Field(..., description="Description of the project")

class ProjectCreate(ProjectBase):
    def to_domain(self, owner_id: str) -> ProjectData:
        return ProjectData(
            name=self.name,
            description=self.description,
            owner_id=owner_id
        )

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3)
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    owner_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    @classmethod
    def from_domain(cls, domain: ProjectData) -> "ProjectResponse":
        return cls(**domain.to_dict())
```

### 4. Repository

The repository handles CRUD operations at the database level.

**File:** `repositories/ProjectRepository.py`
```python
from typing import Optional, List
from sqlalchemy.orm import Session
from orm.ProjectModel import Project
from .BaseRepository import BaseRepository

class ProjectRepository(BaseRepository[Project, int]):
    def __init__(self, db: Session):
        super().__init__(db, Project)

    def list_projects(self, owner_id: str, skip: int = 0, limit: int = 100) -> List[Project]:
        return (
            self.db.query(Project)
            .filter(Project.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_owner(self, project_id: int, owner_id: str) -> Optional[Project]:
        return (
            self.db.query(Project)
            .filter(Project.id == project_id, Project.owner_id == owner_id)
            .first()
        )
```

### 5. Service

The service layer applies business logic on top of the repository.

**File:** `services/ProjectService.py`
```python
from typing import Optional
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from configs.Database import get_db_connection
from domain.project import ProjectData
from repositories.ProjectRepository import ProjectRepository
from schemas.pydantic.ProjectSchema import ProjectCreate, ProjectUpdate, ProjectResponse
from utils.validation.validation import validate_pagination

class ProjectService:
    def __init__(self, db: Session = Depends(get_db_connection)):
        self.db = db
        self.project_repo = ProjectRepository(db)

    def create_project(self, project_data: ProjectCreate, owner_id: str) -> ProjectResponse:
        domain_data = project_data.to_domain(owner_id)
        instance = self.project_repo.create(domain_data)
        return ProjectResponse.from_orm(instance)

    def get_project(self, project_id: int, owner_id: str) -> Optional[ProjectResponse]:
        project = self.project_repo.get_by_owner(project_id, owner_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return ProjectResponse.from_orm(project)

    def list_projects(self, owner_id: str, page: int = 1, size: int = 50):
        validate_pagination(page, size)
        skip = (page - 1) * size
        items = self.project_repo.list_projects(owner_id, skip=skip, limit=size)
        total = len(items)
        return {
            "items": [ProjectResponse.from_orm(i) for i in items],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }

    def update_project(self, project_id: int, owner_id: str, update_data: ProjectUpdate) -> ProjectResponse:
        project = self.project_repo.get_by_owner(project_id, owner_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        data_to_update = update_data.dict(exclude_unset=True)
        updated = self.project_repo.update(project_id, data_to_update)
        return ProjectResponse.from_orm(updated)

    def delete_project(self, project_id: int, owner_id: str):
        project = self.project_repo.get_by_owner(project_id, owner_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        self.project_repo.delete(project_id)
        return True
```

### 6. GraphQL Schema

Add a new type and mutations for GraphQL.

**File:** `schemas/graphql/types/Project.py`
```python
import strawberry
from datetime import datetime
from typing import Optional

@strawberry.type
class Project:
    id: int
    name: str
    description: str
    owner_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
```

**File:** `schemas/graphql/mutations/ProjectMutation.py`
```python
import strawberry
from strawberry.types import Info
from fastapi import HTTPException

from schemas.pydantic.ProjectSchema import ProjectCreate, ProjectUpdate
from schemas.graphql.types.Project import Project as GQLProject
from configs.GraphQL import get_user_from_context, get_db_from_context
from services.ProjectService import ProjectService

@strawberry.input
class ProjectInput:
    name: str
    description: str

@strawberry.input
class ProjectUpdateInput:
    name: Optional[str] = None
    description: Optional[str] = None

@strawberry.type
class ProjectMutation:
    @strawberry.mutation
    def create_project(self, info: Info, project: ProjectInput) -> GQLProject:
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        service = ProjectService(get_db_from_context(info))
        pydantic_obj = ProjectCreate(name=project.name, description=project.description)
        result = service.create_project(pydantic_obj, user.id)
        return GQLProject(**result.dict())

    @strawberry.mutation
    def update_project(self, info: Info, project_id: int, project: ProjectUpdateInput) -> GQLProject:
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        service = ProjectService(get_db_from_context(info))
        update_obj = ProjectUpdate(**project.__dict__)
        result = service.update_project(project_id, user.id, update_obj)
        return GQLProject(**result.dict())

    @strawberry.mutation
    def delete_project(self, info: Info, project_id: int) -> bool:
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        service = ProjectService(get_db_from_context(info))
        return service.delete_project(project_id, user.id)
```

Update `schemas/graphql/Mutation.py` to include `ProjectMutation`:
```python
from schemas.graphql.mutations.ProjectMutation import ProjectMutation

@strawberry.type(description="Mutate all entities")
class Mutation(UserMutation, ActivityMutation, MomentMutation, ProjectMutation):
    pass
```

Update `schemas/graphql/Query.py` to add a field to get a single project or list projects:
```python
from schemas.graphql.types.Project import Project as GQLProject

@strawberry.type
class Query:
    # Existing queries...
    @strawberry.field(description="Get a Project by ID")
    def getProject(self, info: Info, project_id: int) -> Optional[GQLProject]:
        user = get_user_from_context(info)
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        service = ProjectService(get_db_from_context(info))
        result = service.get_project(project_id, user.id)
        if result:
            return GQLProject(**result.dict())
        return None
```

### 7. REST Router

Add endpoints for the Project entity in REST API.

**File:** `routers/v1/ProjectRouter.py`
```python
from fastapi import APIRouter, Depends, status
from services.ProjectService import ProjectService
from schemas.pydantic.ProjectSchema import ProjectCreate, ProjectUpdate, ProjectResponse
from schemas.pydantic.CommonSchema import GenericResponse, MessageResponse
from schemas.pydantic.PaginationSchema import PaginationParams
from dependencies import get_current_user
from orm.UserModel import User
from utils.error_handlers import handle_exceptions

router = APIRouter(prefix="/v1/projects", tags=["projects"])

@router.post("", response_model=GenericResponse[ProjectResponse], status_code=status.HTTP_201_CREATED)
@handle_exceptions
async def create_project(project: ProjectCreate, service: ProjectService = Depends(), current_user: User = Depends(get_current_user)):
    result = service.create_project(project, current_user.id)
    return GenericResponse(data=result, message="Project created successfully")

@router.get("", response_model=GenericResponse[dict])
@handle_exceptions
async def list_projects(pagination: PaginationParams = Depends(), service: ProjectService = Depends(), current_user: User = Depends(get_current_user)):
    result = service.list_projects(current_user.id, pagination.page, pagination.size)
    return GenericResponse(data=result, message=f"Retrieved {result['total']} projects")

@router.get("/{project_id}", response_model=GenericResponse[ProjectResponse])
@handle_exceptions
async def get_project(project_id: int, service: ProjectService = Depends(), current_user: User = Depends(get_current_user)):
    result = service.get_project(project_id, current_user.id)
    return GenericResponse(data=result)

@router.put("/{project_id}", response_model=GenericResponse[ProjectResponse])
@handle_exceptions
async def update_project(project_id: int, project: ProjectUpdate, service: ProjectService = Depends(), current_user: User = Depends(get_current_user)):
    result = service.update_project(project_id, current_user.id, project)
    return GenericResponse(data=result, message="Project updated successfully")

@router.delete("/{project_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
@handle_exceptions
async def delete_project(project_id: int, service: ProjectService = Depends(), current_user: User = Depends(get_current_user)):
    service.delete_project(project_id, current_user.id)
    return MessageResponse(message="Project deleted successfully")
```

Add the new router to `main.py`:
```python
from routers.v1.ProjectRouter import router as ProjectRouter

app.include_router(ProjectRouter)
```

### 8. OpenAPI Documentation

Update `metadata/Tags.py` to include your new entity:

```python
Tags = [
    # ... existing tags ...
    {
        "name": "projects",
        "description": "Create and manage projects with custom attributes",
    },
]
```

### 9. Database Table Definition

Update `scripts/init_database.sql` to include your new table:

```sql
-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CHECK (name != '')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add indexes
CREATE INDEX idx_projects_user_id ON projects(user_id);
```

### 10. Testing

Create test files under `__tests__` directory:

**File:** `__tests__/test_project.py`
```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.mark.integration
def test_create_project():
    # Assuming we have a token for a test user
    token = "Bearer <YOUR_TEST_TOKEN>"
    payload = {
        "name": "Test Project",
        "description": "This is a test project"
    }
    response = client.post("/v1/projects", json=payload, headers={"Authorization": token})
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Test Project"
```

Add more tests for listing, updating, and deleting projects, and for GraphQL endpoints as well. Run tests with `pytest`.

### Additional Notes

- Make sure to handle authentication and authorization properly.
- Keep code style consistent with existing conventions.
- Add logging and error handling as done in other entities.
- Update `pytest.ini` or test configuration if needed.
- Extend this guide for custom pagination, filtering, or indexing as required.
- After adding a new table, you'll need to recreate the database or run migrations.

---

By following these steps, a new developer can add a new entity to the API, including all necessary components from domain models to database tables and tests.
