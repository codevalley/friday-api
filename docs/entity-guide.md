
# How to Add a New Domain Entity

This guide explains how to introduce a new domain entity into the codebase following the established clean architecture principles. It covers creating models, repositories, services, schemas, routers, and tests for the new entity. We will use "Location" as an example entity—replace `Location` and related terms with your actual domain concept.

## Prerequisites

- You have a working environment with the project set up, database configured, and migrations ready.
- You understand the project's clean architecture layers:
  - **Domain (models)**: Core domain entities and business rules (no external dependencies).
  - **Data Access (repositories)**: Encapsulate data persistence, returning domain objects to services.
  - **Application (services)**: Implement use cases, business logic, and validation.
  - **Presentation (routers, schemas)**: REST and GraphQL interfaces and schemas.
  
- You have reviewed the existing code, architecture documentation, and best practice recommendations.

## Steps Overview

1. **Domain Model (SQLAlchemy)**
2. **Database Migrations**
3. **Repository**
4. **Service Layer**
5. **Pydantic Schemas**
6. **GraphQL Schemas**
7. **Routers (REST Endpoints)**
8. **Testing**
9. **Documentation Updates**

Follow these steps carefully to ensure consistency, maintainability, and adherence to clean architecture.

---

## 1. Domain Model

**File:** `models/LocationModel.py`

Domain models reside in `models/`. Keep them free of external logic (no HTTP exceptions, no I/O). Just define the SQLAlchemy columns, relationships, and any basic constraints.

```python
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from models.BaseModel import EntityMeta

class Location(EntityMeta):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # If related entities exist, define relationships here.
    # e.g., `moments = relationship("Moment", back_populates="location")`

    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}')>"
```

**Key Points:**
- Define columns and constraints.
- Prefer UTC for any datetime fields.
- No external logic or HTTP exceptions.  

---

## 2. Database Migrations

Use your existing migration framework (e.g., Alembic) to create and apply a migration script:

```bash
alembic revision --autogenerate -m "Add locations table"
alembic upgrade head
```

Ensure `init()` or `metadata.create_all()` is invoked if the project uses direct `create_all()` calls.

---

## 3. Repository

**File:** `repositories/LocationRepository.py`

Repositories handle all CRUD operations and return domain entities. They should not raise `HTTPException`. If an entity is not found, return `None` and let services or routers handle errors.

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from models.LocationModel import Location

class LocationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, latitude: float, longitude: float) -> Location:
        location = Location(name=name, latitude=latitude, longitude=longitude)
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location
    
    def get_by_id(self, location_id: int) -> Optional[Location]:
        return self.db.query(Location).filter(Location.id == location_id).first()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Location]:
        return self.db.query(Location).offset(skip).limit(limit).all()

    def update(self, location_id: int, **kwargs) -> Optional[Location]:
        location = self.get_by_id(location_id)
        if not location:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(location, key, value)
        self.db.commit()
        self.db.refresh(location)
        return location

    def delete(self, location_id: int) -> bool:
        location = self.get_by_id(location_id)
        if not location:
            return False
        self.db.delete(location)
        self.db.commit()
        return True
```

**Key Points:**
- No `HTTPException` here.
- Return `None` if not found.

---

## 4. Service Layer

**File:** `services/LocationService.py`

Services orchestrate domain logic, validation, and repository calls. They handle domain-level validation and raise domain-specific exceptions or return `None` when needed. The router layer will map these conditions to HTTP errors.

```python
from typing import Optional, List
from fastapi import Depends
from sqlalchemy.orm import Session
from configs.Database import get_db_connection
from repositories.LocationRepository import LocationRepository
from schemas.pydantic.LocationSchema import LocationCreate, LocationUpdate
from exceptions import EntityNotFoundError  # Example custom exception

class LocationService:
    def __init__(self, db: Session = Depends(get_db_connection)):
        self.db = db
        self.location_repository = LocationRepository(db)

    def create_location(self, location_data: LocationCreate):
        # Basic validation can be done here if needed.
        location = self.location_repository.create(
            name=location_data.name,
            latitude=location_data.latitude,
            longitude=location_data.longitude
        )
        return location

    def get_location(self, location_id: int):
        location = self.location_repository.get_by_id(location_id)
        if not location:
            raise EntityNotFoundError("Location not found")
        return location

    def list_locations(self, skip: int = 0, limit: int = 100):
        return self.location_repository.list_all(skip=skip, limit=limit)

    def update_location(self, location_id: int, update_data: LocationUpdate):
        location = self.location_repository.get_by_id(location_id)
        if not location:
            raise EntityNotFoundError("Location not found")
        updated_location = self.location_repository.update(
            location_id, **update_data.dict(exclude_unset=True)
        )
        return updated_location

    def delete_location(self, location_id: int):
        success = self.location_repository.delete(location_id)
        if not success:
            raise EntityNotFoundError("Location not found")
        return True
```

**Key Points:**
- Services raise domain-specific exceptions (e.g., `EntityNotFoundError`) rather than `HTTPException`.
- Validation and business rules belong here.

---

## 5. Pydantic Schemas

**File:** `schemas/pydantic/LocationSchema.py`

Pydantic models define data shapes for requests and responses. They also enforce input validation.

```python
from typing import Optional
from pydantic import BaseModel, Field

class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    latitude: float
    longitude: float

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class LocationResponse(LocationBase):
    id: int
    
    class Config:
        orm_mode = True
```

**Key Points:**
- Keep input/output schemas separate (e.g., `LocationCreate` vs. `LocationResponse`).
- Use `Field` constraints and `orm_mode` for seamless SQLAlchemy model integration.

---

## 6. GraphQL Schemas

**File:** `schemas/graphql/Location.py`

Define GraphQL types and inputs. In GraphQL, handle conversions cleanly—use dict internally and only convert to strings if needed.

```python
import strawberry
from typing import Optional, List
from utils.json_utils import ensure_string, ensure_dict

@strawberry.type
class Location:
    id: int
    name: str
    latitude: float
    longitude: float

    @classmethod
    def from_db(cls, db_location):
        return cls(
            id=db_location.id,
            name=db_location.name,
            latitude=db_location.latitude,
            longitude=db_location.longitude
        )

@strawberry.input
class LocationInput:
    name: str
    latitude: float
    longitude: float

@strawberry.input
class LocationUpdateInput:
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
```

Then integrate `Location` queries and mutations in `schemas/graphql/Query.py` and `schemas/graphql/Mutation.py`, using the `LocationService` from context and handling domain exceptions.

---

## 7. Routers (REST Endpoints)

**File:** `routers/v1/LocationRouter.py`

Routers convert domain exceptions into `HTTPException` and handle authentication if needed.

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from schemas.pydantic.LocationSchema import LocationCreate, LocationUpdate, LocationResponse
from services.LocationService import LocationService
from exceptions import EntityNotFoundError

router = APIRouter(
    prefix="/v1/locations",
    tags=["locations"]
)

@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(location: LocationCreate, service: LocationService = Depends()):
    loc = service.create_location(location)
    return loc

@router.get("", response_model=List[LocationResponse])
async def list_locations(skip: int = 0, limit: int = 100, service: LocationService = Depends()):
    return service.list_locations(skip=skip, limit=limit)

@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(location_id: int, service: LocationService = Depends()):
    try:
        return service.get_location(location_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(location_id: int, location: LocationUpdate, service: LocationService = Depends()):
    try:
        return service.update_location(location_id, location)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(location_id: int, service: LocationService = Depends()):
    try:
        service.delete_location(location_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
```

**Key Points:**
- Routers map domain exceptions to `HTTPException`.
- Maintain consistent pagination and query parameters.

---

## 8. Testing

Add unit tests for each layer and integration tests for the endpoints. Place them in `__tests__` directory:

- **Unit Tests**: Test `LocationService` and `LocationRepository` logic.
- **Integration Tests**: Use `TestClient` to call endpoints and verify responses.
- **GraphQL Tests**: Verify GraphQL queries and mutations return expected results.

Example (unit test):

```python
def test_location_service_create(db_session):
    service = LocationService(db_session)
    loc = service.create_location(LocationCreate(name="Office", latitude=40.7128, longitude=-74.0060))
    assert loc.name == "Office"
```

---

## 9. Documentation Updates

- Update `docs/` to include the new entity’s details.
- Add references in `docs/arch/data-access.md` or `docs/arch/domain-models.md` if needed.
- Keep `repo-structure.md` updated.

---

## Additional Recommendations

- **No `HTTPException` in Models or Repositories**: Keep them domain- and data-layer agnostic.
- **Use Domain Exceptions in Services**: Services should raise exceptions like `EntityNotFoundError`.  
- **Consistent Validation**: Validate data in services when it involves business rules.  
- **Follow Code Style**: Use `black`, `isort`, `flake8`, `mypy` for code consistency.
- **Performance Considerations**: If needed, add indexing or caching in repositories.

---

## Conclusion

By following these steps, you integrate a new domain entity into the system while maintaining clean architecture principles. This approach ensures that your code remains testable, maintainable, and scalable as your project grows.
