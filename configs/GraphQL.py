from fastapi import Depends, Request
from strawberry.types import Info
from sqlalchemy.orm import Session
from typing import Optional

from services.ActivityService import ActivityService
from services.MomentService import MomentService
from configs.Database import get_db_connection
from dependencies import get_optional_user
from models.UserModel import User


# GraphQL Dependency Context
async def get_graphql_context(
    request: Request,
    activity_service: ActivityService = Depends(),
    moment_service: MomentService = Depends(),
    db: Session = Depends(get_db_connection),
    current_user: Optional[User] = Depends(get_optional_user),
):
    # Check if it's a GraphiQL request
    is_graphiql = request.headers.get("accept", "").find("text/html") != -1

    return {
        "activity_service": activity_service,
        "moment_service": moment_service,
        "db": db,
        "user": current_user,
        "is_graphiql": is_graphiql,
    }


# Extract ActivityService instance from GraphQL context
def get_ActivityService(info: Info) -> ActivityService:
    return info.context["activity_service"]


# Extract MomentService instance from GraphQL context
def get_MomentService(info: Info) -> MomentService:
    return info.context["moment_service"]


# Extract database session from GraphQL context
def get_db_from_context(info: Info) -> Session:
    return info.context["db"]


# Extract current user from GraphQL context
def get_user_from_context(info: Info) -> Optional[User]:
    return info.context.get("user")
