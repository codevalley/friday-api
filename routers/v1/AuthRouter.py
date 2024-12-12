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
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_200_OK,
)
async def register_user(
    request: UserCreate,
    db: Session = Depends(get_db_connection),
):
    """Register a new user"""
    service = UserService(db)
    return await service.register_user(request)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: UserLoginRequest,
    db: Session = Depends(get_db_connection),
):
    """Login to get an access token"""
    service = UserService(db)
    user = await service.authenticate_user(
        request.user_secret
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.id}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
