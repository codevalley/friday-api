# How to Add a New Domain/Entity: "Location" Example

This document guides you through the process of introducing a new domain/entity (`Location`) into the existing codebase. By following these steps, you will have a fully integrated domain that includes models, repositories, services, schemas (Pydantic and GraphQL), routers, metadata, and endpoint visibility in both REST and GraphQL interfaces.

## Prerequisites

- You have the project set up and running locally.
- You understand the project’s clean architecture layout (domain, services, repositories, schemas, routers, etc.).
- You have a running database and know how to run migrations or `create_all()` where applicable.
- You have knowledge of Python, FastAPI, SQLAlchemy, Strawberry GraphQL, and Pydantic.

## Steps Overview

1. **Domain Model (SQLAlchemy)**  
2. **Database Migration** (if needed)  
3. **Repository** (CRUD data access)  
4. **Service Layer** (business logic)  
5. **Pydantic Schemas** (validation and response shaping)  
6. **GraphQL Schemas** (queries, mutations, types)  
7. **Routers (REST Endpoints)** (expose CRUD operations over REST)  
8. **Metadata (Optional)** (add tags for OpenAPI docs)  
9. **Update main.py** (if needed)  
10. **Test & Verify** (check `/docs` and `/graphql`)

Below are detailed instructions and a recommended file structure. Replace `Location` with your actual entity name where appropriate.

---

## 1. Add a Domain Model

**File:** `models/LocationModel.py`

```python
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from models.BaseModel import EntityMeta

class Location(EntityMeta):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)

    # If there are related entities, define relationships here
    # e.g. `moments = relationship("Moment", back_populates="location")`
    
    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}')>"
```

**Key Points:**
- Define your columns, indexes, constraints.
- Follow the project’s conventions (naming, indexing, etc.).
- Add `__repr__` for easier debugging.

---

## 2. Database Migration

If using a migration tool (e.g., Alembic), create a migration script:

```bash
alembic revision --autogenerate -m "Add locations table"
alembic upgrade head
```

If the project relies on `init()` in `models/BaseModel.py` with `create_all()`, ensure it’s invoked after adding the new model.

---

## 3. Create a Repository

**File:** `repositories/LocationRepository.py`

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
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

    def validate_existence(self, location_id: int) -> Location:
        location = self.get_by_id(location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        return location
```

---

## 4. Add Service Logic

**File:** `services/LocationService.py`

```python
from typing import Optional, List
from fastapi import Depends
from sqlalchemy.orm import Session
from configs.Database import get_db_connection
from repositories.LocationRepository import LocationRepository
from schemas.pydantic.LocationSchema import LocationCreate, LocationUpdate
from schemas.graphql.Location import Location as LocationGQLType

class LocationService:
    def __init__(self, db: Session = Depends(get_db_connection)):
        self.db = db
        self.location_repository = LocationRepository(db)
    
    def create_location(self, location_data: LocationCreate) -> LocationGQLType:
        location = self.location_repository.create(
            name=location_data.name,
            latitude=location_data.latitude,
            longitude=location_data.longitude
        )
        return LocationGQLType.from_db(location)

    def get_location(self, location_id: int) -> Optional[LocationGQLType]:
        location = self.location_repository.validate_existence(location_id)
        return LocationGQLType.from_db(location) if location else None

    def list_locations(self, skip: int = 0, limit: int = 100) -> List[LocationGQLType]:
        locations = self.location_repository.list_all(skip=skip, limit=limit)
        return [LocationGQLType.from_db(loc) for loc in locations]

    def update_location(self, location_id: int, location_data: LocationUpdate) -> Optional[LocationGQLType]:
        self.location_repository.validate_existence(location_id)
        update_data = location_data.dict(exclude_unset=True)
        location = self.location_repository.update(location_id, **update_data)
        return LocationGQLType.from_db(location) if location else None

    def delete_location(self, location_id: int) -> bool:
        return self.location_repository.delete(location_id)
```

---

## 5. Pydantic Schemas

**File:** `schemas/pydantic/LocationSchema.py`

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

---

## 6. GraphQL Schemas

**File:** `schemas/graphql/Location.py`

```python
import strawberry
from typing import Optional, List
from datetime import datetime
from utils.json_utils import ensure_string, ensure_dict

@strawberry.type
class Location:
    @classmethod
    def from_db(cls, db_location):
        return cls(
            id=db_location.id,
            name=db_location.name,
            latitude=db_location.latitude,
            longitude=db_location.longitude
        )

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
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
```

**Add Queries & Mutations:**

Update `schemas/graphql/Query.py` to add a query for listing and getting locations:

```python
# In schemas/graphql/Query.py
from schemas.graphql.Location import Location as LocationType
from schemas.graphql.Location import LocationInput, LocationUpdateInput
from configs.GraphQL import get_graphql_context

@strawberry.field(description="Get a Location by ID")
def getLocation(self, id: int, info: Info) -> Optional[LocationType]:
    location_service = info.context["location_service"]
    return location_service.get_location(id)

@strawberry.field(description="List all Locations")
def getLocations(self, info: Info, skip: int = 0, limit: int = 100) -> List[LocationType]:
    location_service = info.context["location_service"]
    return location_service.list_locations(skip=skip, limit=limit)
```

Update `schemas/graphql/Mutation.py`:

```python
# In schemas/graphql/Mutation.py
from schemas.graphql.Location import Location, LocationInput, LocationUpdateInput
from schemas.pydantic.LocationSchema import LocationCreate, LocationUpdate

@strawberry.field(description="Create a new Location")
def create_location(self, location: LocationInput, info: Info) -> Location:
    location_service = info.context["location_service"]
    loc_create = LocationCreate(**location.__dict__)
    return location_service.create_location(loc_create)

@strawberry.field(description="Update an existing Location")
def update_location(self, location_id: int, location: LocationUpdateInput, info: Info) -> Location:
    location_service = info.context["location_service"]
    loc_update = LocationUpdate(**{k:v for k,v in location.__dict__.items() if v is not None})
    return location_service.update_location(location_id, loc_update)

@strawberry.field(description="Delete a Location")
def delete_location(self, location_id: int, info: Info) -> bool:
    location_service = info.context["location_service"]
    return location_service.delete_location(location_id)
```

**Note**: Make sure to add `location_service` to the GraphQL context in `configs/GraphQL.py`.

```python
# configs/GraphQL.py
from services.LocationService import LocationService

async def get_graphql_context(
    activity_service: ActivityService = Depends(),
    moment_service: MomentService = Depends(),
    location_service: LocationService = Depends()
):
    return {
        "activity_service": activity_service,
        "moment_service": moment_service,
        "location_service": location_service,
    }
```

---

## 7. REST Routers

**File:** `routers/v1/LocationRouter.py`

```python
from typing import List
from fastapi import APIRouter, Depends, Query
from schemas.pydantic.LocationSchema import LocationCreate, LocationUpdate, LocationResponse
from services.LocationService import LocationService

router = APIRouter(
    prefix="/v1/locations",
    tags=["locations"]
)

@router.post("", response_model=LocationResponse, status_code=201)
async def create_location(location: LocationCreate, service: LocationService = Depends()):
    return service.create_location(location)

@router.get("", response_model=List[LocationResponse])
async def list_locations(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), service: LocationService = Depends()):
    return service.list_locations(skip=skip, limit=limit)

@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(location_id: int, service: LocationService = Depends()):
    return service.get_location(location_id)

@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(location_id: int, location: LocationUpdate, service: LocationService = Depends()):
    return service.update_location(location_id, location)

@router.delete("/{location_id}", status_code=204)
async def delete_location(location_id: int, service: LocationService = Depends()):
    service.delete_location(location_id)
    return None
```

**Finally**, include this router in `main.py`:

```python
from routers.v1.LocationRouter import router as LocationRouter
app.include_router(LocationRouter)
```

---

## 8. Metadata (Optional)

Add a tag in `metadata/Tags.py`:

```python
Tags.append({
    "name": "locations",
    "description": "Manage geographic locations"
})
```

---

## 9. Update main.py (if not done yet)

Make sure you have `LocationRouter` included:

```python
from routers.v1.LocationRouter import router as LocationRouter

app.include_router(LocationRouter)
```

Also ensure `LocationService` is imported and used in `get_graphql_context` if that wasn’t done yet.

---

## 10. Test & Verify

- Run the server: `uvicorn main:app --reload`
- Visit `http://localhost:8000/docs` to see the new `locations` endpoints under the OpenAPI documentation.
- Visit `http://localhost:8000/graphql` to explore `getLocation`, `getLocations`, `create_location`, `update_location`, `delete_location` in the GraphQL playground.
- Test with curl or a GraphQL client to verify all CRUD operations.

**Example REST Calls:**
```bash
curl -X POST "http://localhost:8000/v1/locations" -H "Content-Type: application/json" -d '{"name":"Home","latitude":37.7749,"longitude":-122.4194}'
```

**GraphQL Example:**
```graphql
mutation {
  create_location(location: {name: "Office", latitude: 40.7128, longitude: -74.0060}) {
    id
    name
    latitude
    longitude
  }
}
```

---

## Conclusion

By following the above steps, you have successfully introduced a new domain (`Location`) into the codebase. This template can be replicated for any new domain entity you want to add. Just follow the same pattern:

1. Model
2. Repository
3. Service
4. Schemas (Pydantic & GraphQL)
5. Routers (REST)
6. Update main configuration (imports, router inclusion)
7. Validate endpoints in `/docs` and `/graphql`

This ensures a consistent, maintainable, and quickly expandable architecture for introducing new concepts into the system.
# How to Add a New Domain/Entity: "Location" Example



This document guides you through the process of introducing a new domain/entity (`Location`) into the existing codebase. By following these steps, you will have a fully integrated domain that includes models, repositories, services, schemas (Pydantic and GraphQL), routers, metadata, and endpoint visibility in both REST and GraphQL interfaces.



## Prerequisites



- You have the project set up and running locally.

- You understand the project’s clean architecture layout (domain, services, repositories, schemas, routers, etc.).

- You have a running database and know how to run migrations or `create_all()` where applicable.

- You have knowledge of Python, FastAPI, SQLAlchemy, Strawberry GraphQL, and Pydantic.



## Steps Overview



1. **Domain Model (SQLAlchemy)**  

2. **Database Migration** (if needed)  

3. **Repository** (CRUD data access)  

4. **Service Layer** (business logic)  

5. **Pydantic Schemas** (validation and response shaping)  

6. **GraphQL Schemas** (queries, mutations, types)  

7. **Routers (REST Endpoints)** (expose CRUD operations over REST)  

8. **Metadata (Optional)** (add tags for OpenAPI docs)  

9. **Update main.py** (if needed)  

10. **Test & Verify** (check `/docs` and `/graphql`)



Below are detailed instructions and a recommended file structure. Replace `Location` with your actual entity name where appropriate.



---



## 1. Add a Domain Model



**File:** `models/LocationModel.py`



```python

from sqlalchemy import Column, Integer, String, Float

from sqlalchemy.orm import relationship

from models.BaseModel import EntityMeta



class Location(EntityMeta):

    __tablename__ = "locations"

    

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), unique=True, index=True)

    latitude = Column(Float)

    longitude = Column(Float)



    # If there are related entities, define relationships here

    # e.g. `moments = relationship("Moment", back_populates="location")`

    

    def __repr__(self):

        return f"<Location(id={self.id}, name='{self.name}')>"

```



**Key Points:**

- Define your columns, indexes, constraints.

- Follow the project’s conventions (naming, indexing, etc.).

- Add `__repr__` for easier debugging.



---



## 2. Database Migration



If using a migration tool (e.g., Alembic), create a migration script:



```bash

alembic revision --autogenerate -m "Add locations table"

alembic upgrade head

```



If the project relies on `init()` in `models/BaseModel.py` with `create_all()`, ensure it’s invoked after adding the new model.



---



## 3. Create a Repository



**File:** `repositories/LocationRepository.py`



```python

from typing import List, Optional

from sqlalchemy.orm import Session

from fastapi import HTTPException

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



    def validate_existence(self, location_id: int) -> Location:

        location = self.get_by_id(location_id)

        if not location:

            raise HTTPException(status_code=404, detail="Location not found")

        return location

```



---



## 4. Add Service Logic



**File:** `services/LocationService.py`



```python

from typing import Optional, List

from fastapi import Depends

from sqlalchemy.orm import Session

from configs.Database import get_db_connection

from repositories.LocationRepository import LocationRepository

from schemas.pydantic.LocationSchema import LocationCreate, LocationUpdate

from schemas.graphql.Location import Location as LocationGQLType



class LocationService:

    def __init__(self, db: Session = Depends(get_db_connection)):

        self.db = db

        self.location_repository = LocationRepository(db)

    

    def create_location(self, location_data: LocationCreate) -> LocationGQLType:

        location = self.location_repository.create(

            name=location_data.name,

            latitude=location_data.latitude,

            longitude=location_data.longitude

        )

        return LocationGQLType.from_db(location)



    def get_location(self, location_id: int) -> Optional[LocationGQLType]:

        location = self.location_repository.validate_existence(location_id)

        return LocationGQLType.from_db(location) if location else None



    def list_locations(self, skip: int = 0, limit: int = 100) -> List[LocationGQLType]:

        locations = self.location_repository.list_all(skip=skip, limit=limit)

        return [LocationGQLType.from_db(loc) for loc in locations]



    def update_location(self, location_id: int, location_data: LocationUpdate) -> Optional[LocationGQLType]:

        self.location_repository.validate_existence(location_id)

        update_data = location_data.dict(exclude_unset=True)

        location = self.location_repository.update(location_id, **update_data)

        return LocationGQLType.from_db(location) if location else None



    def delete_location(self, location_id: int) -> bool:

        return self.location_repository.delete(location_id)

```



---



## 5. Pydantic Schemas



**File:** `schemas/pydantic/LocationSchema.py`



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



---



## 6. GraphQL Schemas



**File:** `schemas/graphql/Location.py`



```python

import strawberry

from typing import Optional, List

from datetime import datetime

from utils.json_utils import ensure_string, ensure_dict



@strawberry.type

class Location:

    @classmethod

    def from_db(cls, db_location):

        return cls(

            id=db_location.id,

            name=db_location.name,

            latitude=db_location.latitude,

            longitude=db_location.longitude

        )



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

    name: Optional[str] = None

    latitude: Optional[float] = None

    longitude: Optional[float] = None

```



**Add Queries & Mutations:**



Update `schemas/graphql/Query.py` to add a query for listing and getting locations:



```python

# In schemas/graphql/Query.py

from schemas.graphql.Location import Location as LocationType

from schemas.graphql.Location import LocationInput, LocationUpdateInput

from configs.GraphQL import get_graphql_context



@strawberry.field(description="Get a Location by ID")

def getLocation(self, id: int, info: Info) -> Optional[LocationType]:

    location_service = info.context["location_service"]

    return location_service.get_location(id)



@strawberry.field(description="List all Locations")

def getLocations(self, info: Info, skip: int = 0, limit: int = 100) -> List[LocationType]:

    location_service = info.context["location_service"]

    return location_service.list_locations(skip=skip, limit=limit)

```



Update `schemas/graphql/Mutation.py`:



```python

# In schemas/graphql/Mutation.py

from schemas.graphql.Location import Location, LocationInput, LocationUpdateInput

from schemas.pydantic.LocationSchema import LocationCreate, LocationUpdate



@strawberry.field(description="Create a new Location")

def create_location(self, location: LocationInput, info: Info) -> Location:

    location_service = info.context["location_service"]

    loc_create = LocationCreate(**location.__dict__)

    return location_service.create_location(loc_create)



@strawberry.field(description="Update an existing Location")

def update_location(self, location_id: int, location: LocationUpdateInput, info: Info) -> Location:

    location_service = info.context["location_service"]

    loc_update = LocationUpdate(**{k:v for k,v in location.__dict__.items() if v is not None})

    return location_service.update_location(location_id, loc_update)



@strawberry.field(description="Delete a Location")

def delete_location(self, location_id: int, info: Info) -> bool:

    location_service = info.context["location_service"]

    return location_service.delete_location(location_id)

```



**Note**: Make sure to add `location_service` to the GraphQL context in `configs/GraphQL.py`.



```python

# configs/GraphQL.py

from services.LocationService import LocationService



async def get_graphql_context(

    activity_service: ActivityService = Depends(),

    moment_service: MomentService = Depends(),

    location_service: LocationService = Depends()

):

    return {

        "activity_service": activity_service,

        "moment_service": moment_service,

        "location_service": location_service,

    }

```



---



## 7. REST Routers



**File:** `routers/v1/LocationRouter.py`



```python

from typing import List

from fastapi import APIRouter, Depends, Query

from schemas.pydantic.LocationSchema import LocationCreate, LocationUpdate, LocationResponse

from services.LocationService import LocationService



router = APIRouter(

    prefix="/v1/locations",

    tags=["locations"]

)



@router.post("", response_model=LocationResponse, status_code=201)

async def create_location(location: LocationCreate, service: LocationService = Depends()):

    return service.create_location(location)



@router.get("", response_model=List[LocationResponse])

async def list_locations(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), service: LocationService = Depends()):

    return service.list_locations(skip=skip, limit=limit)



@router.get("/{location_id}", response_model=LocationResponse)

async def get_location(location_id: int, service: LocationService = Depends()):

    return service.get_location(location_id)



@router.put("/{location_id}", response_model=LocationResponse)

async def update_location(location_id: int, location: LocationUpdate, service: LocationService = Depends()):

    return service.update_location(location_id, location)



@router.delete("/{location_id}", status_code=204)

async def delete_location(location_id: int, service: LocationService = Depends()):

    service.delete_location(location_id)

    return None

```



**Finally**, include this router in `main.py`:



```python

from routers.v1.LocationRouter import router as LocationRouter

app.include_router(LocationRouter)

```



---



## 8. Metadata (Optional)



Add a tag in `metadata/Tags.py`:



```python

Tags.append({

    "name": "locations",

    "description": "Manage geographic locations"

})

```



---



## 9. Update main.py (if not done yet)



Make sure you have `LocationRouter` included:



```python

from routers.v1.LocationRouter import router as LocationRouter



app.include_router(LocationRouter)

```



Also ensure `LocationService` is imported and used in `get_graphql_context` if that wasn’t done yet.



---



## 10. Test & Verify



- Run the server: `uvicorn main:app --reload`

- Visit `http://localhost:8000/docs` to see the new `locations` endpoints under the OpenAPI documentation.

- Visit `http://localhost:8000/graphql` to explore `getLocation`, `getLocations`, `create_location`, `update_location`, `delete_location` in the GraphQL playground.

- Test with curl or a GraphQL client to verify all CRUD operations.



**Example REST Calls:**

```bash

curl -X POST "http://localhost:8000/v1/locations" -H "Content-Type: application/json" -d '{"name":"Home","latitude":37.7749,"longitude":-122.4194}'

```



**GraphQL Example:**

```graphql

mutation {

  create_location(location: {name: "Office", latitude: 40.7128, longitude: -74.0060}) {

    id

    name

    latitude

    longitude

  }

}

```



---



## Conclusion



By following the above steps, you have successfully introduced a new domain (`Location`) into the codebase. This template can be replicated for any new domain entity you want to add. Just follow the same pattern:



1. Model

2. Repository

3. Service

4. Schemas (Pydantic & GraphQL)

5. Routers (REST)

6. Update main configuration (imports, router inclusion)

7. Validate endpoints in `/docs` and `/graphql`



This ensures a consistent, maintainable, and quickly expandable architecture for introducing new concepts into the system.