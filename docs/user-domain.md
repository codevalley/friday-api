## Implementation Progress Tracker

- [x] 1. Domain Model (`models/UserModel.py`)
- [x] 2. Repository Layer (`repositories/UserRepository.py`)
- [x] 3. Service Layer (`services/UserService.py`)
- [x] 4. Schemas (`schemas/pydantic/UserSchema.py`)
- [x] 5. Authentication Utilities (`utils/security.py`)
- [x] 6. Dependencies (`dependencies.py`)
- [x] 7. Routers (`routers/v1/AuthRouter.py`)
- [ ] 8. Secure Other Endpoints
- [ ] 9. JWT Configuration
- [ ] 10. Database Migrations
- [ ] 11. Testing

Below is a step-by-step plan for integrating a user registration and authentication flow similar to the project’s approach into our clean architecture codebase. This plan will guide in implementing this feature without breaking the established structure of our clean architecture.

## High-Level Objectives

1. Introduce a `User` domain that models the concept of a user.
2. Allow user registration to create a unique `user_id`, `username`, and `user_secret`.
3. Provide a login endpoint that accepts a `user_secret` and returns a JWT-based access token.
4. Secure other domain endpoints by requiring this JWT token for authentication.
5. Keep all changes in line with clean architecture principles:
   - Domain logic remains in `models` and `services`.
   - Persistence concerns remain in `repositories`.
   - Validation and request/response formatting stay in `schemas`.
   - Endpoints remain in `routers`.
   - Authentication and JWT handling are done via dependencies and utility modules.

## Detailed Plan

### 1. Domain Model (Models Layer)
**File: `models/UserModel.py`**

- Create a `User` model that represents the user entity in the system.
- Fields:
  - `id` (unique user_id, UUID or short ID)
  - `username` (string)
  - `user_secret` (secure secret key similar to a password but managed differently)
- Ensure no business logic in this file—only the data structure and ORM mappings if any.

Example:
```python
from sqlalchemy import Column, String
from models.BaseModel import EntityMeta
import uuid

class User(EntityMeta):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    user_secret = Column(String, unique=True, index=True, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
```

### 2. Repository (Data Access Layer)
**File: `repositories/UserRepository.py`**

- Implement a `UserRepository` class with methods like `create_user`, `get_by_user_secret`, and `get_by_id`.
- This repository will handle all database interactions related to the `User` entity.
- No business logic here—just CRUD operations.

Example:
```python
from typing import Optional
from sqlalchemy.orm import Session
from models.UserModel import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, username: str, user_secret: str) -> User:
        user = User(username=username, user_secret=user_secret)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_user_secret(self, user_secret: str) -> Optional[User]:
        return self.db.query(User).filter(User.user_secret == user_secret).first()

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
```

### 3. Services (Business Logic Layer)
**File: `services/UserService.py`**

- The `UserService` orchestrates user registration and authentication logic.
- `register_user(username: str)`: Generates a `user_secret`, saves user to DB, returns user info and user_secret.
- `authenticate_user(user_secret: str)`: Checks if user exists, if yes returns user. If not, raise a domain-specific error.
- Keep logic minimal—no JWT generation here, only domain logic.

Example:
```python
import secrets
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from repositories.UserRepository import UserRepository

class UserService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def register_user(self, username: str):
        # Generate a unique user_secret
        user_secret = secrets.token_urlsafe(32)
        # Create user
        user = self.user_repository.create_user(username, user_secret)
        return user, user_secret

    def authenticate_user(self, user_secret: str):
        user = self.user_repository.get_by_user_secret(user_secret)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return user
```

### 4. Schemas (Validation and DTOs)
**File: `schemas/pydantic/UserSchema.py`**

- Define Pydantic models for request and response bodies:
  - `UserRegisterRequest`: Contains `username`.
  - `UserRegisterResponse`: Returns `id`, `username`, and `user_secret`.
  - `UserLoginRequest`: Contains `user_secret`.
  - `Token`: For the login response, contains `access_token` and `token_type`.

Example:
```python
from pydantic import BaseModel, Field

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

class UserRegisterResponse(BaseModel):
    id: str
    username: str
    user_secret: str

    class Config:
        orm_mode = True

class UserLoginRequest(BaseModel):
    user_secret: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

### 5. Authentication Utilities
**File: `utils/security.py`** (Already existing or create a new one)

- Implement functions for:
  - `create_access_token(data: dict)`: Uses JWT to create a token with `user_id` as a claim.
  - `verify_token(token: str)`: Decode the JWT and return `user_id`.
- These utilities adhere to the same architecture principles—no domain logic here.

### 6. Dependencies
**File: `dependencies.py`**

- Add a `get_current_user` dependency similar to what we have in the second project:
  - Extract the `Authorization` header, parse token.
  - Decode token with `verify_token`.
  - Use `UserRepository` to load user from DB.
  - Raise HTTPException if invalid token or user not found.

```python
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from utils.security import verify_token
from repositories.UserRepository import UserRepository
from configs.Database import get_db_connection

def get_current_user(token: str, db: Session = Depends(get_db_connection)):
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

### 7. Routers (Presentation Layer)
**File: `routers/v1/AuthRouter.py`**

- Create an `auth` router for user-related endpoints:
  - `POST /register`: Accepts `username`, calls `UserService.register_user`, returns `user_id`, `username`, and `user_secret`.
  - `POST /token`: Accepts `user_secret`, calls `UserService.authenticate_user`, and if successful, returns a signed JWT token.

- No domain logic here: just parse request body, call service methods, and return response.

Example:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from configs.Database import get_db_connection
from services.UserService import UserService
from schemas.pydantic.UserSchema import UserRegisterRequest, UserRegisterResponse, UserLoginRequest, Token
from utils.security import create_access_token

router = APIRouter(prefix="/v1/auth", tags=["auth"])

@router.post("/register", response_model=UserRegisterResponse)
def register_user(
    request: UserRegisterRequest,
    db: Session = Depends(get_db_connection),
):
    service = UserService(db)
    user, user_secret = service.register_user(request.username)
    return UserRegisterResponse(id=user.id, username=user.username, user_secret=user_secret)

@router.post("/token", response_model=Token)
def login_for_access_token(
    request: UserLoginRequest,
    db: Session = Depends(get_db_connection),
):
    service = UserService(db)
    user = service.authenticate_user(request.user_secret)
    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token)
```

### 8. Secure Other Endpoints
- For any existing routers (like `ActivityRouter` or `MomentRouter`), require authentication by adding a dependency on `get_current_user`.
- For example:
```python
@router.get("/moments", response_model=MomentList)
def list_moments(
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user)  # User must be authenticated
):
    # existing logic
    ...
```

### 9. JWT Configuration
- Ensure your `utils/security.py` has the correct JWT secret key and expiration settings from your `configs/Environment.py`.
- Store your JWT secret and algorithm in environment variables or config settings.
- Make sure to handle token expiration and proper error responses.

### 10. Database Migrations
- Add a `users` table if not already present.
- Run migrations or `init()` to create/update database schema.

### 11. Testing
- Test `POST /v1/auth/register` to ensure it returns `id`, `username`, and `user_secret`.
- Test `POST /v1/auth/token` with a valid `user_secret` to ensure it returns a working JWT.
- Test that protected endpoints return 401 if no token or invalid token is provided, and success if a valid token is present.
- Verify that all other domain endpoints still follow the clean architecture and no business logic has leaked into routers.

## Summary
This plan outlines how to integrate the user registration and authentication pattern from the second project into your original clean architecture system. By adding a `User` domain, related service and repository, schemas, authentication utilities, and a dedicated auth router, you maintain clear separation of concerns while introducing a secure and maintainable user management flow.