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
    
    async def create(self, data: dict) -> T:
        """Create a new entity"""
        pass

    async def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID"""
        pass

    async def get_all(self) -> List[T]:
        """Get all entities"""
        pass

    async def update(self, id: int, data: dict) -> Optional[T]:
        """Update an entity"""
        pass

    async def delete(self, id: int) -> bool:
        """Delete an entity"""
        pass
```

### Concrete Repositories

1. **Book Repository**
```python
# repositories/BookRepository.py
class BookRepository(RepositoryMeta[BookModel]):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: dict) -> BookModel:
        book = BookModel(**data)
        self._session.add(book)
        await self._session.commit()
        return book
```

2. **Author Repository**
```python
# repositories/AuthorRepository.py
class AuthorRepository(RepositoryMeta[AuthorModel]):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: int) -> Optional[AuthorModel]:
        query = select(AuthorModel).where(AuthorModel.id == id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
```

## Key Features

1. **Generic Implementation**
   - Type-safe repository operations
   - Reusable CRUD operations
   - Consistent interface across entities

2. **Async Database Operations**
   - Asynchronous database access
   - Efficient resource utilization
   - Better scalability

3. **Session Management**
   - Proper transaction handling
   - Connection pooling
   - Resource cleanup

## Database Operations

### 1. Create Operations
```python
async def create(self, data: dict) -> T:
    entity = self._model(**data)
    self._session.add(entity)
    await self._session.commit()
    return entity
```

### 2. Read Operations
```python
async def get_all(self) -> List[T]:
    query = select(self._model)
    result = await self._session.execute(query)
    return result.scalars().all()
```

### 3. Update Operations
```python
async def update(self, id: int, data: dict) -> Optional[T]:
    entity = await self.get_by_id(id)
    if entity:
        for key, value in data.items():
            setattr(entity, key, value)
        await self._session.commit()
    return entity
```

### 4. Delete Operations
```python
async def delete(self, id: int) -> bool:
    entity = await self.get_by_id(id)
    if entity:
        await self._session.delete(entity)
        await self._session.commit()
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
   - Efficient queries
   - Connection pooling
   - Proper indexing

3. **Testing**
   - Repository mocking
   - Integration tests
   - Database fixtures
``` 