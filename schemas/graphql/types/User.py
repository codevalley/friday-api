from datetime import datetime
import strawberry
from typing import Optional


@strawberry.type
class User:
    id: str
    username: str
    created_at: datetime
    updated_at: Optional[datetime] = None


@strawberry.input
class UserCreateInput:
    username: str


@strawberry.input
class UserLoginInput:
    user_secret: str


@strawberry.type
class UserRegisterResponse:
    id: str
    username: str
    user_secret: str
    created_at: datetime
    updated_at: Optional[datetime] = None


@strawberry.type
class Token:
    access_token: str
    token_type: str = "bearer"
