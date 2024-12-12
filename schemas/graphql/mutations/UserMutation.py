import strawberry
from typing import Optional
from sqlalchemy.orm import Session

from configs.Database import get_db_connection
from services.UserService import UserService
from schemas.graphql.types.User import (
    User,
    UserCreateInput,
    UserLoginInput,
    UserRegisterResponse,
    Token,
)


@strawberry.type
class UserMutation:
    @strawberry.mutation
    def register_user(
        self,
        input: UserCreateInput,
        info: strawberry.types.Info,
    ) -> UserRegisterResponse:
        """Register a new user"""
        db = info.context["db"]
        service = UserService(db)
        user, user_secret = service.register_user(
            input.username
        )
        return UserRegisterResponse(
            id=user.id,
            username=user.username,
            user_secret=user_secret,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @strawberry.mutation
    def login(
        self,
        input: UserLoginInput,
        info: strawberry.types.Info,
    ) -> Token:
        """Login to get an access token"""
        db = info.context["db"]
        service = UserService(db)
        user = service.authenticate_user(input.user_secret)
        from utils.security import create_access_token

        access_token = create_access_token(
            data={"sub": user.id}
        )
        return Token(access_token=access_token)
