import strawberry
from services.UserService import UserService
from schemas.graphql.types.User import (
    UserCreateInput,
    UserLoginInput,
    UserRegisterResponse,
    Token,
)
from typing import cast
from datetime import datetime


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
            id=cast(str, user.id),
            username=cast(str, user.username),
            userSecret=user_secret,
            createdAt=cast(datetime, user.created_at),
            updatedAt=cast(
                datetime | None, user.updated_at
            ),
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
        user = service.authenticate_user(input.userSecret)
        from utils.security import create_access_token

        access_token = create_access_token(
            data={"sub": user.id}
        )
        return Token(accessToken=access_token)
