import strawberry
from typing import Optional
from datetime import datetime

from services.ActivityService import ActivityService
from schemas.pydantic.ActivitySchema import ActivityCreate
from schemas.graphql.Activity import Activity, ActivityInput
from configs.GraphQL import get_ActivityService, get_user_from_context


@strawberry.type
class ActivityMutation:
    @strawberry.mutation
    async def create_activity(
        self,
        info: strawberry.Info,
        activity: ActivityInput
    ) -> Activity:
        """Create a new activity"""
        current_user = get_user_from_context(info)
        service = get_ActivityService(info)
        
        # Convert input using to_dict method
        activity_dict = activity.to_dict()
        activity_dict["user_id"] = current_user.id
        activity_data = ActivityCreate(**activity_dict)
        
        db_activity = service.create_activity(activity_data)
        return Activity.from_db(db_activity)
