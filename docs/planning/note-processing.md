Below is a detailed, step-by-step guide illustrating how to implement the scenario where notes are processed to extract other entities (moments, activities), and how a generic LLM (Large Language Model) service can be integrated. We’ll show how to structure the code and define interfaces so that the system can switch between OpenAI, Claude, or another LLM provider without changing the application logic.

We’ll follow the layered (clean architecture-like) approach:

- **Domain Layer**: Pure business logic (models, rules)
- **Application Layer (Services)**: Orchestrates use-cases, calls domain logic, uses repositories and external services via interfaces
- **Infrastructure Layer**: Actual implementations of repositories (ORM), LLM APIs (OpenAI, Claude), and other I/O tasks
- **Presentation Layer (Routers/Controllers)**: HTTP endpoints, GraphQL resolvers, etc.

This guide provides conceptual code snippets and explanations.

---

## Step-by-Step Implementation Guide

### 1. Domain Layer

**Entities/Value Objects**:
We have `Note`, `MomentData`, `ActivityData` as domain models. Each should encapsulate validation and no external references.

```python
# domain/note.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class NoteData:
    id: Optional[int]
    user_id: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    def validate(self):
        if not self.content or not self.user_id:
            raise ValueError("Invalid note data")
```

```python
# domain/moment.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class MomentData:
    id: Optional[int]
    user_id: str
    activity_id: int
    data: Dict[str, Any]
    timestamp: datetime
    # Validate within __post_init__ or separate method
```

```python
# domain/activity.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class ActivityData:
    id: Optional[int]
    user_id: str
    name: str
    description: str
    activity_schema: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Validate as needed
```

**No references to HTTP, LLM, or parsing logic here.** Just pure data models and basic validation rules.

---

### 2. Application Layer Interfaces

**Repositories Interfaces**:
Define interfaces for data persistence.
```python
# application/ports/repositories.py
from typing import Protocol, List, Optional
from domain.note import NoteData
from domain.moment import MomentData
from domain.activity import ActivityData

class NoteRepository(Protocol):
    def create(self, note: NoteData) -> NoteData: ...
    def get(self, note_id: int) -> Optional[NoteData]: ...
    # ... other methods ...

class MomentRepository(Protocol):
    def create(self, moment: MomentData) -> MomentData: ...
    # ... other methods ...

class ActivityRepository(Protocol):
    def create(self, activity: ActivityData) -> ActivityData: ...
    # ... other methods ...
```

**LLM Service Interface**:
This interface allows plugging in OpenAI, Claude, etc.
```python
# application/ports/llm_service.py
from typing import Protocol, List
from domain.moment import MomentData
from domain.activity import ActivityData

class LLMService(Protocol):
    def analyze_note(self, note_content: str) -> (List[MomentData], List[ActivityData]):
        """Analyze the note content and extract moments and activities."""
        ...
```

**Note Processing Service Interface**:
This is where we orchestrate note analysis. The `NoteProcessingService` uses the `LLMService` to transform note content into domain objects.
```python
# application/ports/note_processing_service.py
from typing import Protocol, List
from domain.moment import MomentData
from domain.activity import ActivityData

class NoteProcessingService(Protocol):
    def extract_entities_from_note(self, note_content: str, user_id: str) -> (List[MomentData], List[ActivityData]):
        """Extract entities (moments, activities) from the note content."""
        ...
```

---

### 3. Application Layer Implementations (Services)

We define a concrete `NoteProcessingServiceImpl` that uses the `LLMService`:

```python
# application/services/note_processing_service_impl.py
from typing import List
from domain.moment import MomentData
from domain.activity import ActivityData
from application.ports.llm_service import LLMService
from application.ports.note_processing_service import NoteProcessingService
from datetime import datetime

class NoteProcessingServiceImpl(NoteProcessingService):
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def extract_entities_from_note(self, note_content: str, user_id: str) -> (List[MomentData], List[ActivityData]):
        # Use LLM to analyze
        moments, activities = self.llm_service.analyze_note(note_content)
        # Add user_id, timestamps etc. to returned domain objects
        now = datetime.utcnow()
        for m in moments:
            m.user_id = user_id
            # Validate if needed
        for a in activities:
            a.user_id = user_id
            # Validate if needed
        return moments, activities
```

**NoteService** – The main use case: create a note and then extract entities.
```python
# application/services/note_service.py
from domain.note import NoteData
from datetime import datetime
from typing import Optional
from application.ports.repositories import NoteRepository, MomentRepository, ActivityRepository
from application.ports.note_processing_service import NoteProcessingService

class NoteService:
    def __init__(self,
                 note_repo: NoteRepository,
                 moment_repo: MomentRepository,
                 activity_repo: ActivityRepository,
                 note_processing_svc: NoteProcessingService):
        self.note_repo = note_repo
        self.moment_repo = moment_repo
        self.activity_repo = activity_repo
        self.note_processing_svc = note_processing_svc

    def create_note(self, user_id: str, content: str) -> NoteData:
        note = NoteData(
            id=None,
            user_id=user_id,
            content=content,
            created_at=datetime.utcnow(),
            updated_at=None
        )
        note.validate()
        saved_note = self.note_repo.create(note)

        # After creating note, extract entities
        moments, activities = self.note_processing_svc.extract_entities_from_note(content, user_id)
        for m in moments:
            self.moment_repo.create(m)
        for a in activities:
            self.activity_repo.create(a)

        return saved_note
```

---

### 4. Infrastructure Layer

**ORM Models** (using SQLAlchemy as example):
```python
# infrastructure/orm/NoteModel.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class NoteORM(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
```

Similarly for Moments, Activities ORM models.

**Repositories Implementations**:
```python
# infrastructure/repositories/note_repository_impl.py
from application.ports.repositories import NoteRepository
from domain.note import NoteData
from infrastructure.orm.NoteModel import NoteORM
from sqlalchemy.orm import Session

class NoteRepositoryImpl(NoteRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, note: NoteData) -> NoteData:
        orm = NoteORM(
            user_id=note.user_id,
            content=note.content,
            created_at=note.created_at,
            updated_at=note.updated_at
        )
        self.db.add(orm)
        self.db.commit()
        self.db.refresh(orm)
        note.id = orm.id
        return note
    # Implement other methods similarly
```

**LLMService Implementations**:
We have a generic `LLMService`. We can have multiple concrete classes:

- `OpenAIService` implementing `LLMService`
- `ClaudeService` implementing `LLMService`

```python
# infrastructure/llm/openai_service.py
from application.ports.llm_service import LLMService
from domain.moment import MomentData
from domain.activity import ActivityData
from typing import List
from datetime import datetime

class OpenAIService(LLMService):
    def __init__(self, openai_client):
        self.openai_client = openai_client

    def analyze_note(self, note_content: str) -> (List[MomentData], List[ActivityData]):
        # call OpenAI API
        response = self.openai_client.analyze_text(note_content)
        # Extract structured data from response
        # For example, response might be JSON with "moments" and "activities"
        moments = [MomentData(id=None, user_id="", activity_id=1, data={"example": "data"}, timestamp=datetime.utcnow())]
        activities = [ActivityData(id=None, user_id="", name="reading", description="Reading a book", activity_schema={}, created_at=datetime.utcnow())]
        return moments, activities
```

A `ClaudeService` would implement the same `LLMService` interface but call Claude’s API.

**NoteProcessingServiceImpl** just depends on `LLMService`, so we can inject either `OpenAIService` or `ClaudeService`.

---

### 5. Presentation Layer (Routers)

**FastAPI Router** as example:
```python
# presentation/routers/note_router.py
from fastapi import APIRouter, Depends
from application.services.note_service import NoteService

router = APIRouter()

@router.post("/notes")
def create_note_endpoint(
    user_id: str,
    content: str,
    note_service: NoteService = Depends(...)
):
    note = note_service.create_note(user_id, content)
    return {
        "id": note.id,
        "user_id": note.user_id,
        "content": note.content,
        "created_at": note.created_at.isoformat()
    }
```

We’ll need to wire dependencies using something like `Depends()` in FastAPI. For example, we might have a `get_note_service()` dependency that constructs the `NoteService` with the required repositories and `NoteProcessingService`.

---

### 6. Wiring Everything Up (Composition Root)

In your main application startup code:

```python
# main.py or app.py
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.repositories.note_repository_impl import NoteRepositoryImpl
from infrastructure.llm.openai_service import OpenAIService
from application.services.note_processing_service_impl import NoteProcessingServiceImpl
from application.services.note_service import NoteService
from presentation.routers.note_router import router as note_router

app = FastAPI()

# Setup DB
engine = create_engine("sqlite:///example.db")
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_note_service(db=Depends(get_db)):
    note_repo = NoteRepositoryImpl(db)
    moment_repo = ... # Implement similarly
    activity_repo = ... # Implement similarly

    # Choose LLM backend
    openai_client = ... # your openAI API client
    llm_service = OpenAIService(openai_client)
    note_processing_svc = NoteProcessingServiceImpl(llm_service)

    return NoteService(note_repo, moment_repo, activity_repo, note_processing_svc)

app.include_router(note_router, dependencies=[Depends(get_note_service)])
```

You would actually define a `get_note_service` dependency that returns a `NoteService` instance with all dependencies injected. In a more complex setup, you’d likely have a dedicated dependency injection library or a factory function.

---

### Summary

- **Domain Layer**: Just data structures and validation.
- **Application Layer**: Defines interfaces (ports) for repositories and LLM service. Implements `NoteService` and `NoteProcessingService` to orchestrate logic.
- **Infrastructure Layer**: Implements repositories (ORM), LLM services (OpenAI), and any adapters.
- **Presentation Layer**: Routers (FastAPI) that handle HTTP requests and call `NoteService`.
- **LLMService is generic**: `NoteProcessingServiceImpl` depends on `LLMService`. By swapping the `LLMService` implementation from `OpenAIService` to `ClaudeService` at injection time, we can easily switch the LLM provider without changing the business logic.

This approach ensures:
- LLM providers are easily swappable.
- The note processing logic is separate from the LLM integration.
- Domain remains free of external service logic.
- The application service orchestrates workflow and can handle multiple entity creations triggered by one event (adding a note triggers extracting and storing moments/activities).

This step-by-step guide and the provided code snippets should help you implement the architecture with a generic LLM service and a `NoteProcessingService` that leverages it.
