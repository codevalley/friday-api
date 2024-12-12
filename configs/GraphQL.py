from fastapi import Depends
from strawberry.types import Info
from sqlalchemy.orm import Session

from services.ActivityService import ActivityService
from services.MomentService import MomentService
from configs.Database import get_db_connection
from dependencies import get_current_user
from models.UserModel import User


# GraphQL Dependency Context
async def get_graphql_context(
    activity_service: ActivityService = Depends(),
    moment_service: MomentService = Depends(),
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    return {
        "activity_service": activity_service,
        "moment_service": moment_service,
        "db": db,
        "user": current_user,
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
def get_user_from_context(info: Info) -> User:
    return info.context["user"]
