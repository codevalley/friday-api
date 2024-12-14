### Hands-On Guide: Adding a New Entity to Your Project

This guide provides a step-by-step walkthrough for adding a new entity to your project while maintaining adherence to the clean architecture and best practices already established. For this example, let's add a new entity called `Task` to your project.

---

### **Step 1: Prerequisites**
1. **Understand the Project Architecture:**
   - Domain Layer: Core models and business rules.
   - Application Layer: Services implementing use cases.
   - Data Access Layer: Repositories abstracting database operations.
   - Presentation Layer: REST and GraphQL APIs.

2. **Tools Required:**
   - Python 3.12+.
   - Database migration tool (e.g., Alembic if you're using it).
   - Your editor configured with black, flake8, and mypy.

---

### **Step 2: Domain Model**
1. **File:** `models/TaskModel.py`
2. **Implementation:**
   ```python
   from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
   from sqlalchemy.orm import relationship
   from datetime import datetime
   from models.BaseModel import EntityMeta

   class Task(EntityMeta):
       __tablename__ = "tasks"

       id = Column(Integer, primary_key=True, index=True)
       title = Column(String(255), nullable=False)
       description = Column(String(1000), nullable=True)
       is_completed = Column(Boolean, default=False)
       user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
       created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

       # Relationships
       user = relationship("User", back_populates="tasks")

       def __repr__(self):
           return f"<Task(id={self.id}, title={self.title}, is_completed={self.is_completed})>"
   ```

---

### **Step 3: Database Migration**
1. **File:** `scripts/migrations/add_task_entity.sql`
2. **Implementation:**
   ```sql
   -- Create tasks table
   CREATE TABLE tasks (
       id INT PRIMARY KEY AUTO_INCREMENT,
       title VARCHAR(255) NOT NULL,
       description TEXT,
       is_completed BOOLEAN DEFAULT FALSE,
       user_id VARCHAR(36) NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
       FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
   );

   -- Add indexes
   CREATE INDEX idx_tasks_user_id ON tasks(user_id);
   ```

3. **Run Migration:**
   ```bash
   alembic revision --autogenerate -m "Add Task entity"
   alembic upgrade head
   ```

---

### **Step 4: Repository**
1. **File:** `repositories/TaskRepository.py`
2. **Implementation:**
   ```python
   from typing import List, Optional
   from sqlalchemy.orm import Session
   from models.TaskModel import Task

   class TaskRepository:
       def __init__(self, db: Session):
           self.db = db

       def create(self, title: str, description: Optional[str], user_id: str) -> Task:
           task = Task(title=title, description=description, user_id=user_id)
           self.db.add(task)
           self.db.commit()
           self.db.refresh(task)
           return task

       def get_by_id(self, task_id: int, user_id: str) -> Optional[Task]:
           return self.db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()

       def list_tasks(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Task]:
           return self.db.query(Task).filter(Task.user_id == user_id).offset(skip).limit(limit).all()

       def update(self, task_id: int, user_id: str, **kwargs) -> Optional[Task]:
           task = self.get_by_id(task_id, user_id)
           if not task:
               return None
           for key, value in kwargs.items():
               setattr(task, key, value)
           self.db.commit()
           self.db.refresh(task)
           return task

       def delete(self, task_id: int, user_id: str) -> bool:
           task = self.get_by_id(task_id, user_id)
           if not task:
               return False
           self.db.delete(task)
           self.db.commit()
           return True
   ```

---

### **Step 5: Service Layer**
1. **File:** `services/TaskService.py`
2. **Implementation:**
   ```python
   from typing import List, Optional
   from fastapi import Depends
   from sqlalchemy.orm import Session
   from repositories.TaskRepository import TaskRepository
   from schemas.pydantic.TaskSchema import TaskCreate, TaskUpdate, TaskResponse
   from configs.Database import get_db_connection

   class TaskService:
       def __init__(self, db: Session = Depends(get_db_connection)):
           self.task_repository = TaskRepository(db)

       def create_task(self, task_data: TaskCreate, user_id: str) -> TaskResponse:
           task = self.task_repository.create(
               title=task_data.title,
               description=task_data.description,
               user_id=user_id
           )
           return TaskResponse.from_orm(task)

       def get_task(self, task_id: int, user_id: str) -> Optional[TaskResponse]:
           task = self.task_repository.get_by_id(task_id, user_id)
           if not task:
               return None
           return TaskResponse.from_orm(task)

       def list_tasks(self, user_id: str, page: int = 1, size: int = 100) -> List[TaskResponse]:
           skip = (page - 1) * size
           tasks = self.task_repository.list_tasks(user_id, skip, size)
           return [TaskResponse.from_orm(task) for task in tasks]

       def update_task(self, task_id: int, task_data: TaskUpdate, user_id: str) -> Optional[TaskResponse]:
           task = self.task_repository.update(task_id, user_id, **task_data.dict(exclude_unset=True))
           if not task:
               return None
           return TaskResponse.from_orm(task)

       def delete_task(self, task_id: int, user_id: str) -> bool:
           return self.task_repository.delete(task_id, user_id)
   ```

---

### **Step 6: Schema**
1. **Pydantic Schema**
   - **File:** `schemas/pydantic/TaskSchema.py`
   ```python
   from pydantic import BaseModel, Field
   from datetime import datetime
   from typing import Optional

   class TaskBase(BaseModel):
       title: str = Field(..., min_length=1, max_length=255)
       description: Optional[str] = Field(None, max_length=1000)

   class TaskCreate(TaskBase):
       pass

   class TaskUpdate(BaseModel):
       title: Optional[str] = Field(None, min_length=1, max_length=255)
       description: Optional[str] = Field(None, max_length=1000)
       is_completed: Optional[bool] = None

   class TaskResponse(TaskBase):
       id: int
       is_completed: bool
       created_at: datetime
       updated_at: datetime

       class Config:
           orm_mode = True
   ```

2. **GraphQL Schema**
   - **File:** `schemas/graphql/Task.py`
   ```python
   import strawberry
   from typing import Optional

   @strawberry.type
   class Task:
       id: int
       title: str
       description: Optional[str]
       is_completed: bool
       created_at: str
       updated_at: str
   ```

---

### **Step 7: API Endpoints**
1. **REST Endpoint**
   - **File:** `routers/v1/TaskRouter.py`
   ```python
   from fastapi import APIRouter, Depends, HTTPException
   from typing import List
   from services.TaskService import TaskService
   from schemas.pydantic.TaskSchema import TaskCreate, TaskUpdate, TaskResponse
   from dependencies import get_current_user
   from models.UserModel import User

   router = APIRouter(prefix="/v1/tasks", tags=["tasks"])

   @router.post("", response_model=TaskResponse)
   async def create_task(task: TaskCreate, service: TaskService = Depends(), current_user: User = Depends(get_current_user)):
       return service.create_task(task, current_user.id)

   @router.get("", response_model=List[TaskResponse])
   async def list_tasks(page: int = 1, size: int = 50, service: TaskService = Depends(), current_user: User = Depends(get_current_user)):
       return service.list_tasks(current_user.id, page, size)

   @router.get("/{task_id}", response_model=TaskResponse)
   async def get_task(task_id: int, service: TaskService = Depends(), current_user: User = Depends(get_current_user)):
       task = service.get_task(task_id, current_user.id)
       if not task:
           raise HTTPException(status_code=404, detail="Task not found")
       return task

   @router.put("/{task_id}", response_model=TaskResponse)
   async def update_task(task_id: int, task: TaskUpdate, service: TaskService = Depends(), current_user: User = Depends(get_current_user)):
       return service.update_task(task_id, task, current_user.id)

   @router.delete("/{task_id}", status_code=204)
   async def delete_task(task_id: int, service: TaskService = Depends(), current_user: User = Depends(get_current_user)):
       if not service.delete_task(task_id, current_user.id):
           raise HTTPException(status_code=404, detail="Task not found")
   ```

2. **GraphQL Endpoint**
   - **File:** `schemas/graphql/mutations/TaskMutation.py`
   ```python
   import strawberry
   from typing import List
   from schemas.graphql.types.Task import Task

   @strawberry.type
   class TaskMutation:
       @strawberry.mutation
       async def create_task(self, title: str, description: str) -> Task:
           # Implement task creation logic here
           pass
   ```

---

### **Step 8: Testing**
1. **Unit Tests:**
   - Create tests for `TaskRepository` and `TaskService`.
   - Place test files in `__tests__/repositories/test_TaskRepository.py` and `__tests__/services/test_TaskService.py`.

2. **Integration Tests:**
   - Test endpoints with FastAPI's TestClient.

---

This guide provides everything you need to add a new entity to your project efficiently. Let me know if you want me to refine this further or provide additional boilerplate!