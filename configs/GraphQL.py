from fastapi import Depends
from strawberry.types import Info
from sqlalchemy.orm import Session

from services.ActivityService import ActivityService
from services.MomentService import MomentService
from configs.Database import get_db_connection


# GraphQL Dependency Context
async def get_graphql_context(
    activity_service: ActivityService = Depends(),
    moment_service: MomentService = Depends(),
    db: Session = Depends(get_db_connection),
):
    return {
        "activity_service": activity_service,
        "moment_service": moment_service,
        "db": db,
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
