from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.orm import Session
from configs.Database import get_db_connection
from services.UserService import UserService
from schemas.pydantic.UserSchema import (
    UserCreate,
    UserRegisterResponse,
    UserLoginRequest,
    Token,
)
from schemas.pydantic.CommonSchema import GenericResponse
from utils.security import create_access_token
from utils.error_handlers import handle_exceptions
from datetime import timedelta

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=GenericResponse[UserRegisterResponse],
    status_code=status.HTTP_201_CREATED,
)
@handle_exceptions
async def register_user(
    request: UserCreate,
    db: Session = Depends(get_db_connection),
):
    """Register a new user"""
    service = UserService(db)
    user, user_secret = service.register_user(
        username=request.username
    )
    return GenericResponse(
        data={
            "id": user.id,
            "username": user.username,
            "user_secret": user_secret,  # Return the plain user_secret
        },
        message="User registered successfully",
    )


@router.post(
    "/token",
    response_model=GenericResponse[Token],
)
@handle_exceptions
async def login_for_access_token(
    request: UserLoginRequest,
    db: Session = Depends(get_db_connection),
):
    """Login to get an access token"""
    service = UserService(db)
    user = service.authenticate_user(request.user_secret)

    # Create access token with user ID as subject
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=30),
    )

    return GenericResponse(
        data={
            "access_token": access_token,
            "token_type": "bearer",
        },
        message="Login successful",
    )
