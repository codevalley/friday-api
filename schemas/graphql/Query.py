from typing import List, Optional
from datetime import datetime

import strawberry
from strawberry.types import Info
from configs.GraphQL import (
    get_ActivityService,
    get_MomentService,
    get_user_from_context,
)

from schemas.graphql.Activity import Activity
from schemas.graphql.Moment import Moment, MomentConnection


@strawberry.type(description="Query all entities")
class Query:
    @strawberry.field(description="Get an Activity by ID")
    def getActivity(
        self, id: int, info: Info
    ) -> Optional[Activity]:
        activity_service = get_ActivityService(info)
        return activity_service.get_activity_graphql(id)

    @strawberry.field(description="List all Activities")
    def getActivities(
        self, info: Info, skip: int = 0, limit: int = 100
    ) -> List[Activity]:
        activity_service = get_ActivityService(info)
        return activity_service.list_activities_graphql(
            skip=skip, limit=limit
        )

    @strawberry.field(description="Get a moment by ID")
    def getMoment(self, id: int, info: Info) -> Optional[Moment]:
        moment_service = get_MomentService(info)
        current_user = get_user_from_context(info)
        return moment_service.get_moment_graphql(id, current_user.id)

    @strawberry.field(description="Get moments with pagination")
    def getMoments(
        self,
        info: Info,
        page: int = 1,
        size: int = 50,
        activity_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> MomentConnection:
        moment_service = get_MomentService(info)
        current_user = get_user_from_context(info)
        return moment_service.list_moments_graphql(
            page=page,
            size=size,
            activity_id=activity_id,
            start_time=start_time,
            end_time=end_time,
            user_id=current_user.id,
        )

    @strawberry.field(
        description="Get recently used activities"
    )
    def getRecentActivities(
        self, info: Info, limit: int = 5
    ) -> List[Activity]:
        moment_service = get_MomentService(info)
        return moment_service.get_recent_activities(limit)
