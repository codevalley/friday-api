from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from schemas.base.user_schema import UserData


class UserBase(BaseModel):
    """Base schema for User with common attributes"""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="User's unique username",
    )

    def to_domain(self) -> UserData:
        """Convert to domain model"""
        return UserData.from_dict(self.model_dump())


class UserCreate(UserBase):
    """Schema for creating a new user"""

    pass


class UserRegisterResponse(BaseModel):
    """Response model for user registration"""

    id: str
    username: str
    user_secret: str

    @classmethod
    def from_domain(
        cls, user: UserData
    ) -> "UserRegisterResponse":
        """Create from domain model"""
        return cls(**user.to_dict(include_secret=True))


class UserResponse(BaseModel):
    """Full user response model with timestamps"""

    id: str
    username: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    @classmethod
    def from_domain(cls, user: UserData) -> "UserResponse":
        """Create from domain model"""
        return cls(**user.to_dict())

    class Config:
        from_attributes = True


class UserLoginRequest(BaseModel):
    """Request model for user login"""

    user_secret: str = Field(
        ...,
        description="User's secret key for authentication",
    )


class Token(BaseModel):
    """Token response model"""

    access_token: str
    token_type: str = "bearer"

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
