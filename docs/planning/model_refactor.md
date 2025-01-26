# Model Layer Refactoring Plan

## Current State Analysis

We currently have two different patterns in our codebase for handling model conversions:

1. **Service Layer Pattern (Target Pattern)**
   - Examples: `Activity`, `Moment`
   - Characteristics:
     - Clean ORM models with no conversion methods
     - Pydantic models handle all validation and conversion in service layer
     - No circular dependencies
     - Clear separation of concerns
   - Current Implementation:
     ```python
     # ORM Layer: Pure SQLAlchemy models
     class Activity(EntityMeta):
         id: Mapped[int] = Column(Integer, primary_key=True)
         # ... other fields ...

     # Service Layer: Pydantic handles conversion
     class ActivityService:
         def create_activity(self, data: ActivityCreate) -> ActivityResponse:
             activity = Activity(**data.model_dump())
             return ActivityResponse.model_validate(activity)
     ```

2. **Dictionary Pattern (Legacy)**
   - Examples: `Task`, `Topic`, `Note`, `Document`
   - Characteristics:
     - ORM models include `to_dict`/`from_dict` methods
     - Mixed concerns (data storage + conversion)
     - Potential validation duplication
   - Current Implementation:
     ```python
     # ORM Layer: Models with conversion logic
     class Document(EntityMeta):
         def to_dict(self) -> Dict[str, Any]:
             return {"id": self.id, ...}

         @classmethod
         def from_dict(cls, data: Dict[str, Any]) -> "Document":
             return cls(**data)
     ```

## Required Changes by Layer

### 1. ORM Layer (`orm/` directory)
- Remove `to_dict`/`from_dict` methods from:
  - `DocumentModel.py`
  - `TaskModel.py`
  - `TopicModel.py`
  - `NoteModel.py`
- Keep only:
  - SQLAlchemy model definitions
  - Field validations
  - Relationships
  - Database constraints

### 2. Domain Layer (`domain/` directory)
- Move domain-specific validation logic from ORM models
- Create or update domain exceptions for each entity
- Define domain-specific types and enums
- Example structure:
  ```python
  # domain/document.py
  class DocumentError(DomainError): ...
  class DocumentStatus(str, Enum): ...
  ```

### 3. Pydantic Layer (`schemas/pydantic/` directory)
For each entity, create:
1. Base Schema:
   ```python
   class DocumentBase(BaseModel):
       name: str
       mime_type: str
       # ... common fields ...
   ```

2. Create Schema:
   ```python
   class DocumentCreate(DocumentBase):
       user_id: str
       # ... creation-specific fields ...
   ```

3. Update Schema:
   ```python
   class DocumentUpdate(BaseModel):
       name: Optional[str] = None
       status: Optional[DocumentStatus] = None
       # ... updateable fields ...
   ```

4. Response Schema:
   ```python
   class DocumentResponse(DocumentBase):
       id: int
       created_at: datetime
       # ... additional response fields ...
   ```

### 4. Repository Layer (`repositories/` directory)
- Remove any dict conversion logic
- Work directly with ORM models
- Example structure:
  ```python
  class DocumentRepository(BaseRepository[Document, int]):
      def create(self, document: Document) -> Document:
          return super().create(document)
  ```

### 5. Service Layer (`services/` directory)
- Add conversion logic using Pydantic
- Handle all validation
- Example structure:
  ```python
  class DocumentService:
      def create_document(self, data: DocumentCreate) -> DocumentResponse:
          document = Document(**data.model_dump())
          created = self.repository.create(document)
          return DocumentResponse.model_validate(created)
  ```

## Migration Strategy

### Phase 1: Document Model (Sprint 1)
1. Create complete Pydantic schema set
2. Update service layer with new patterns
3. Remove dict methods from ORM
4. Update tests
5. Validate and fix any issues

### Phase 2: Task Model (Sprint 2)
1. Follow same steps as Document
2. Additional focus on relationship handling
3. Update task-specific validations

### Phase 3: Topic Model (Sprint 2)
1. Simplest model to migrate
2. Good candidate for parallel work

### Phase 4: Note Model (Sprint 3)
1. Most complex due to relationships
2. Requires careful testing of all connections

## Testing Requirements

1. **Unit Tests**
   - Pydantic schema validation
   - Service layer conversion
   - Repository operations
   - Domain logic

2. **Integration Tests**
   - End-to-end flows
   - API responses
   - Database operations

3. **Migration Tests**
   - Data consistency
   - Backward compatibility

## Success Criteria

1. **Code Quality**
   - No circular dependencies
   - Clear separation of concerns
   - Consistent patterns across all models
   - Improved maintainability

2. **Functionality**
   - All existing features working
   - No regression in behavior
   - Proper error handling
   - Correct validation

3. **Performance**
   - No degradation in response times
   - Efficient database queries
   - Optimal memory usage

4. **Testing**
   - 100% test coverage of new code
   - All existing tests passing
   - New tests for Pydantic schemas

## Rollback Plan

1. Keep old code paths until fully tested
2. Deploy changes gradually by model
3. Monitor for issues in staging
4. Have quick rollback scripts ready
