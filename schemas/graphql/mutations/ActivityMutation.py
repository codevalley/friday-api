import strawberry
from fastapi import HTTPException

from schemas.pydantic.ActivitySchema import (
    ActivityCreate,
    ActivityUpdate,
)
from schemas.graphql.types.Activity import (
    Activity,
    ActivityInput,
    ActivityUpdateInput,
)
from configs.GraphQL import (
    get_ActivityService,
    get_user_from_context,
)


@strawberry.type
class ActivityMutation:
    @strawberry.mutation
    async def create_activity(
        self, info: strawberry.Info, activity: ActivityInput
    ) -> Activity:
        """Create a new activity

        Args:
            info: GraphQL request info containing context
            activity: Activity input data

        Returns:
            Created activity

        Raises:
            Exception: If user is not authenticated or validation fails
        """
        current_user = get_user_from_context(info)
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to create activity",
            )

        service = get_ActivityService(info)
        activity_create = ActivityCreate(
            **activity.to_dict()
        )

        try:
            db_activity = service.create_activity_graphql(
                activity_data=activity_create,
                user_id=str(current_user.id),
            )
            return Activity.from_db(db_activity)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid activity data: {str(e)}",
            )

    @strawberry.mutation
    async def update_activity(
        self,
        info: strawberry.Info,
        activity_id: int,
        activity: ActivityUpdateInput,
    ) -> Activity:
        """Update an existing activity

        Args:
            info: GraphQL request info containing context
            activity_id: ID of activity to update
            activity: Updated activity data

        Returns:
            Updated activity

        Raises:
            Exception: If user is not authenticated or validation fails
        """
        current_user = get_user_from_context(info)
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to update activity",
            )

        service = get_ActivityService(info)
        activity_data = ActivityUpdate(**activity.to_dict())

        try:
            db_activity = service.update_activity_graphql(
                activity_id=activity_id,
                activity_data=activity_data,
                user_id=str(current_user.id),
            )
            return Activity.from_db(db_activity)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid activity data: {str(e)}",
            )

    @strawberry.mutation
    async def delete_activity(
        self, info: strawberry.Info, activity_id: int
    ) -> bool:
        """Delete an activity

        Args:
            info: GraphQL request info containing context
            activity_id: ID of activity to delete

        Returns:
            True if deletion was successful

        Raises:
            Exception: If user is not authenticated or activity not found
        """
        current_user = get_user_from_context(info)
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to delete activity",
            )

        service = get_ActivityService(info)
        try:
            return service.delete_activity(
                activity_id=activity_id,
                user_id=str(current_user.id),
            )
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Activity not found: {str(e)}",
            )
