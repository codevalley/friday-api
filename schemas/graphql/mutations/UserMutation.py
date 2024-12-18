"""GraphQL mutations for User-related operations."""

import strawberry
from services.UserService import UserService
from schemas.graphql.types.User import (
    UserCreateInput,
    UserLoginInput,
    UserRegisterResponse,
    Token,
)
from utils.security import create_access_token


@strawberry.type
class UserMutation:
    """GraphQL mutations for user operations."""

    @strawberry.mutation
    def register_user(
        self,
        input: UserCreateInput,
        info: strawberry.types.Info,
    ) -> UserRegisterResponse:
        """Register a new user.

        Args:
            input: User registration data
            info: GraphQL request context

        Returns:
            UserRegisterResponse: Registration response with user details
        """
        db = info.context["db"]
        service = UserService(db)
        user = service.register_user(input.to_domain())
        return UserRegisterResponse.from_domain(user)

    @strawberry.mutation
    def login(
        self,
        input: UserLoginInput,
        info: strawberry.types.Info,
    ) -> Token:
        """Login to get an access token.

        Args:
            input: User login credentials
            info: GraphQL request context

        Returns:
            Token: JWT access token for authentication
        """
        db = info.context["db"]
        service = UserService(db)
        user = service.authenticate_user(input.to_domain())
        access_token = create_access_token(
            data={"sub": str(user.id)}
        )
        return Token(access_token=access_token)
