# Data Access Layer

## Overview

The data access layer implements the repository pattern to abstract database operations from the business logic. Located in the `repositories/` directory, this layer provides a clean interface for data persistence while maintaining the principles of clean architecture.

## Repository Pattern Implementation

### Base Repository

```python
# repositories/RepositoryMeta.py
from typing import List, Optional, TypeVar, Generic

T = TypeVar('T')

class RepositoryMeta(Generic[T]):
    """Base repository with common CRUD operations"""
    
    def create(self, **data) -> T:
        """Create a new entity"""
        pass

    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID"""
        pass

    def get_all(self) -> List[T]:
        """Get all entities"""
        pass

    def update(self, id: int, **data) -> Optional[T]:
        """Update an entity"""
        pass

    def delete(self, id: int) -> bool:
        """Delete an entity"""
        pass
```

### Concrete Repositories

1. **Activity Repository**
```python
# repositories/ActivityRepository.py
class ActivityRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, activity_id: int) -> Optional[Activity]:
        return self.db.query(Activity).filter(Activity.id == activity_id).first()

    def validate_existence(self, activity_id: int) -> Activity:
        activity = self.get_by_id(activity_id)
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        return activity
```

2. **Moment Repository**
```python
# repositories/MomentRepository.py
class MomentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_moments(
        self,
        page: int = 1,
        size: int = 50,
        activity_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> MomentList:
        query = self.db.query(Moment)

        # Apply filters
        if activity_id is not None:
            query = query.filter(Moment.activity_id == activity_id)
        if start_time is not None:
            query = query.filter(Moment.timestamp >= start_time)
        if end_time is not None:
            query = query.filter(Moment.timestamp <= end_time)

        # Get total count and paginate
        total = query.count()
        pages = (total + size - 1) // size
        skip = (page - 1) * size

        moments = query.order_by(desc(Moment.timestamp)).offset(skip).limit(size).all()

        return MomentList(
            items=moments,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
```

## Key Features

1. **Generic Implementation**
   - Type-safe repository operations
   - Reusable CRUD operations
   - Consistent interface across entities

2. **Database Operations**
   - Efficient query building
   - Proper transaction handling
   - Connection management via SQLAlchemy

3. **Session Management**
   - Proper transaction handling
   - Connection pooling
   - Resource cleanup

## Database Operations

### 1. Create Operations
```python
def create(self, **data) -> T:
    entity = self._model(**data)
    self.db.add(entity)
    self.db.commit()
    self.db.refresh(entity)
    return entity
```

### 2. Read Operations
```python
def get_all(self) -> List[T]:
    return self.db.query(self._model).all()
```

### 3. Update Operations
```python
def update(self, id: int, **data) -> Optional[T]:
    entity = self.get_by_id(id)
    if entity:
        for key, value in data.items():
            if value is not None:
                setattr(entity, key, value)
        self.db.commit()
        self.db.refresh(entity)
    return entity
```

### 4. Delete Operations
```python
def delete(self, id: int) -> bool:
    entity = self.get_by_id(id)
    if entity:
        self.db.delete(entity)
        self.db.commit()
        return True
    return False
```

## Clean Architecture Integration

1. **Dependency Inversion**
   - Repository interfaces in domain layer
   - Implementations in infrastructure layer
   - Business logic depends on abstractions

2. **Data Mapping**
   - Converts between domain and database models
   - Handles database-specific concerns
   - Isolates persistence details

3. **Transaction Management**
   - Atomic operations
   - Consistent data state
   - Error handling and rollback

## Best Practices

1. **Error Handling**
   - Proper exception handling
   - Meaningful error messages
   - Transaction rollback on errors

2. **Performance Optimization**
   - Efficient queries with proper filtering
   - Pagination support
   - Proper indexing

3. **Testing**
   - Repository mocking
   - Integration tests
   - Database fixtures