### Hands-on Guide: Adding a New Entity

This guide provides detailed steps to add a new entity while adhering to the clean architecture principles of the project. Each step outlines changes needed for the model, schema (Pydantic, GraphQL), repository, service, routers, OpenAPI documentation, and testing. We use "Location" as an example; replace `Location` with your new entity.

---

### 1. **Domain Model**

**File:** `models/LocationModel.py`

Define the SQLAlchemy model with required fields and relationships.

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

    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}')>"
```

**Key Points:**
- Use `EntityMeta` as the base class.
- Follow naming conventions for columns and constraints.

---

### 2. **Database Migration**

Use Alembic for database migrations.

```bash
alembic revision --autogenerate -m "Add locations table"
alembic upgrade head
```

Verify the table structure in the database.

---

### 3. **Repository**

**File:** `repositories/LocationRepository.py`

Implement CRUD operations in the repository.

```python
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

    def get_by_id(self, location_id: int):
        return self.db.query(Location).filter(Location.id == location_id).first()

    def list_all(self):
        return self.db.query(Location).all()

    def update(self, location_id: int, **kwargs):
        location = self.get_by_id(location_id)
        if not location:
            return None
        for key, value in kwargs.items():
            setattr(location, key, value)
        self.db.commit()
        self.db.refresh(location)
        return location

    def delete(self, location_id: int):
        location = self.get_by_id(location_id)
        if location:
            self.db.delete(location)
            self.db.commit()
            return True
        return False
```

---

### 4. **Service Layer**

**File:** `services/LocationService.py`

Implement the business logic.

```python
from sqlalchemy.orm import Session
from repositories.LocationRepository import LocationRepository
from schemas.pydantic.LocationSchema import LocationCreate, LocationUpdate

class LocationService:
    def __init__(self, db: Session):
        self.repository = LocationRepository(db)

    def create_location(self, location_data: LocationCreate):
        return self.repository.create(
            name=location_data.name,
            latitude=location_data.latitude,
            longitude=location_data.longitude
        )

    def get_location(self, location_id: int):
        return self.repository.get_by_id(location_id)

    def list_locations(self):
        return self.repository.list_all()

    def update_location(self, location_id: int, location_data: LocationUpdate):
        return self.repository.update(location_id, **location_data.dict(exclude_unset=True))

    def delete_location(self, location_id: int):
        return self.repository.delete(location_id)
```

---

### 5. **Pydantic Schemas**

**File:** `schemas/pydantic/LocationSchema.py`

Define request and response schemas for the API.

```python
from pydantic import BaseModel

class LocationBase(BaseModel):
    name: str
    latitude: float
    longitude: float

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    name: str = None
    latitude: float = None
    longitude: float = None

class LocationResponse(LocationBase):
    id: int

    class Config:
        orm_mode = True
```

---

### 6. **GraphQL Schemas**

**File:** `schemas/graphql/types/Location.py`

Define types and inputs for GraphQL.

```python
import strawberry

@strawberry.type
class Location:
    id: int
    name: str
    latitude: float
    longitude: float

@strawberry.input
class LocationInput:
    name: str
    latitude: float
    longitude: float

@strawberry.input
class LocationUpdateInput:
    name: str = None
    latitude: float = None
    longitude: float = None
```

---

### 7. **REST Router**

**File:** `routers/v1/LocationRouter.py`

Implement the REST endpoints.

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from services.LocationService import LocationService
from schemas.pydantic.LocationSchema import LocationCreate, LocationUpdate, LocationResponse

router = APIRouter(prefix="/locations", tags=["locations"])

def get_service(db: Session = Depends()):
    return LocationService(db)

@router.post("", response_model=LocationResponse)
def create_location(location: LocationCreate, service: LocationService = Depends(get_service)):
    return service.create_location(location)

@router.get("/{location_id}", response_model=LocationResponse)
def get_location(location_id: int, service: LocationService = Depends(get_service)):
    return service.get_location(location_id)

@router.get("", response_model=list[LocationResponse])
def list_locations(service: LocationService = Depends(get_service)):
    return service.list_locations()

@router.put("/{location_id}", response_model=LocationResponse)
def update_location(location_id: int, location: LocationUpdate, service: LocationService = Depends(get_service)):
    return service.update_location(location_id, location)

@router.delete("/{location_id}", response_model=bool)
def delete_location(location_id: int, service: LocationService = Depends(get_service)):
    return service.delete_location(location_id)
```

---

### 8. **Testing**

Add unit and integration tests for repositories, services, and routers. Use `pytest`.

**File:** `__tests__/test_LocationRouter.py`

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_location():
    response = client.post("/locations", json={"name": "Test Location", "latitude": 12.34, "longitude": 56.78})
    assert response.status_code == 200
    assert response.json()["name"] == "Test Location"

def test_get_location():
    location_id = 1  # Replace with actual ID after creation
    response = client.get(f"/locations/{location_id}")
    assert response.status_code == 200
    assert response.json()["id"] == location_id
```

---

### 9. **Documentation**

- Update OpenAPI tags in `metadata/Tags.py`.
- Add API examples to `docs/`.
- Review GraphQL documentation for new queries and mutations.

---

### Conclusion

Following this guide ensures a consistent approach to adding new entities, maintaining the clean architecture principles.

