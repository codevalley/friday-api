# Active Development Backlog

## 1. Note Domain Implementation ⏳
**Goal**: Complete the Note domain model following clean architecture principles

### Tasks:
1. Create Note Domain Model
```python
# domain/note.py
from datetime import datetime
from typing import List, Optional

class NoteValidationError(Exception):
    def __init__(self, message: str, code: str = "NOTE_VALIDATION_ERROR"):
        self.code = code
        super().__init__(message)

class Note:
    def __init__(
        self, 
        content: str,
        user_id: str,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        attachments: Optional[List[str]] = None
    ):
        self.id = id
        self.content = content
        self.user_id = user_id
        self.created_at = created_at
        self.attachments = attachments or []
        self.validate()

    def validate(self) -> None:
        if not self.content:
            raise NoteValidationError("Content cannot be empty")
        if not self.user_id:
            raise NoteValidationError("User ID is required")
```

2. Update Repository Layer
```python
# repositories/NoteRepository.py
from domain.note import Note

class NoteRepository:
    def create(self, note: Note) -> Note:
        orm_note = NoteModel(
            content=note.content,
            user_id=note.user_id,
            attachments=note.attachments
        )
        self.db.add(orm_note)
        self.db.commit()
        return Note.from_orm(orm_note)
```

## 2. Repository Layer Refinement 🔄

### Tasks:
1. Create Base Repository Interface
```python
# repositories/base.py
from typing import TypeVar, Generic, List
from domain.base import DomainModel

T = TypeVar('T', bound=DomainModel)

class BaseRepository(Generic[T]):
    def get(self, id: int) -> T:
        raise NotImplementedError
    
    def create(self, entity: T) -> T:
        raise NotImplementedError
```

2. Update All Repositories to Return Domain Models

## 3. Service Layer Enhancement 🔄

### Tasks:
1. Move HTTP Exception Handling to Routers
```python
# routers/v1/error_handlers.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from domain.note import NoteValidationError

async def note_validation_exception_handler(
    request: Request, 
    exc: NoteValidationError
):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "code": exc.code}
    )
```

2. Create Base Service Interface
```python
# services/base.py
from typing import TypeVar, Generic
from domain.base import DomainModel

T = TypeVar('T', bound=DomainModel)

class BaseService(Generic[T]):
    def create(self, data: dict) -> T:
        raise NotImplementedError
```

## 4. Validation Consolidation ⭕

### Tasks:
1. Create Central Validation Module
```python
# utils/validation/domain_validators.py
from typing import Any, Type
from domain.base import DomainModel

def validate_domain_model(model_class: Type[DomainModel], data: dict) -> Any:
    """Central validation point for domain models"""
    instance = model_class(**data)
    instance.validate()
    return instance
```

## 5. Infrastructure Independence ⭕

### Tasks:
1. Create Database Abstraction Layer
```python
# infrastructure/database/interface.py
from typing import Protocol, TypeVar

T = TypeVar('T')

class DatabaseInterface(Protocol):
    def query(self, model: Type[T]) -> List[T]: ...
    def save(self, instance: T) -> T: ...
```

## Implementation Priority:
1. Complete Note Domain Model
2. Update Repository Layer
3. Move Exception Handling
4. Implement Validation Consolidation
5. Add Infrastructure Abstractions

## Success Criteria:
- All domain models are framework-independent
- Repositories return domain models
- HTTP exceptions handled only in routers
- Single validation entry point
- Clear separation between domain and infrastructure
