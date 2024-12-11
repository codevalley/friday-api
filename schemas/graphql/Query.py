from typing import List, Optional
from datetime import datetime

import strawberry
from strawberry.types import Info
from configs.GraphQL import (
    get_ActivityService,
    get_MomentService,
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
        return activity_service.get_activity(id)

    @strawberry.field(description="List all Activities")
    def getActivities(
        self,
        info: Info,
        skip: int = 0,
        limit: int = 100
    ) -> List[Activity]:
        activity_service = get_ActivityService(info)
        return activity_service.list_activities(skip=skip, limit=limit)

    @strawberry.field(description="Get a Moment by ID")
    def getMoment(
        self, id: int, info: Info
    ) -> Optional[Moment]:
        moment_service = get_MomentService(info)
        return moment_service.get_moment(id)

    @strawberry.field(description="List Moments with filtering and pagination")
    def getMoments(
        self,
        info: Info,
        page: int = 1,
        size: int = 50,
        activityId: Optional[int] = None,
        startTime: Optional[datetime] = None,
        endTime: Optional[datetime] = None
    ) -> MomentConnection:
        moment_service = get_MomentService(info)
        return moment_service.list_moments(
            page=page,
            size=size,
            activity_id=activityId,
            start_time=startTime,
            end_time=endTime
        )

    @strawberry.field(description="Get recently used activities")
    def getRecentActivities(
        self,
        info: Info,
        limit: int = 5
    ) -> List[Activity]:
        moment_service = get_MomentService(info)
        return moment_service.get_recent_activities(limit)
