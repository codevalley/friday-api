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
    UserInfoResponse,
)
from schemas.pydantic.CommonSchema import GenericResponse
from utils.security import (
    create_access_token,
    get_current_user,
)
from utils.error_handlers import handle_exceptions
from datetime import timedelta
from typing import Dict

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
    response = UserRegisterResponse.from_domain(
        user, user_secret
    )
    return GenericResponse(
        data=response,
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

    token = Token(
        access_token=access_token,
        token_type="bearer",
    )

    return GenericResponse(
        data=token,
        message="Login successful",
    )


@router.get(
    "/me",
    response_model=GenericResponse[UserInfoResponse],
)
@handle_exceptions
async def get_current_user_info(
    db: Session = Depends(get_db_connection),
    current_user: Dict = Depends(get_current_user),
):
    """Get current user information"""
    service = UserService(db)
    user = service.get_user_by_id(current_user["user_id"])
    response = UserInfoResponse.from_domain(user)
    return GenericResponse(
        data=response,
        message="Current user retrieved successfully",
    )
