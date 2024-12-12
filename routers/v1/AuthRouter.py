from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
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
from utils.security import create_access_token

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserRegisterResponse
)
async def register_user(
    request: UserCreate,
    db: Session = Depends(get_db_connection),
):
    """Register a new user"""
    service = UserService(db)
    user, user_secret = service.register_user(
        request.username
    )
    response = UserRegisterResponse(
        id=user.id,
        username=user.username,
        user_secret=user_secret,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
    return response


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: UserLoginRequest,
    db: Session = Depends(get_db_connection),
):
    """Login to get an access token"""
    service = UserService(db)
    user = service.authenticate_user(request.user_secret)

    # Create access token
    access_token = create_access_token(
        data={"sub": user.id}
    )
    return Token(access_token=access_token)
