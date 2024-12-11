from fastapi import Depends
from strawberry.types import Info

from services.ActivityService import ActivityService
from services.MomentService import MomentService


# GraphQL Dependency Context
async def get_graphql_context(
    activity_service: ActivityService = Depends(),
    moment_service: MomentService = Depends(),
):
    return {
        "activity_service": activity_service,
        "moment_service": moment_service,
    }


# Extract ActivityService instance from GraphQL context
def get_ActivityService(info: Info) -> ActivityService:
    return info.context["activity_service"]


# Extract MomentService instance from GraphQL context
def get_MomentService(info: Info) -> MomentService:
    return info.context["moment_service"]
