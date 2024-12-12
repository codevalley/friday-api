import strawberry
from strawberry.types import Info
from configs.GraphQL import (
    get_ActivityService,
    get_MomentService,
    get_user_from_context,
)

from schemas.graphql.Activity import (
    Activity,
    ActivityInput,
    ActivityUpdateInput,
)
from schemas.graphql.Moment import (
    Moment,
    MomentInput,
)
from schemas.pydantic.ActivitySchema import (
    ActivityCreate,
    ActivityUpdate,
)
from schemas.pydantic.MomentSchema import (
    MomentCreate,
    MomentUpdate,
)
from schemas.graphql.mutations.UserMutation import (
    UserMutation,
)
from schemas.graphql.mutations.ActivityMutation import (
    ActivityMutation,
)
from schemas.graphql.mutations.MomentMutation import (
    MomentMutation,
)


@strawberry.type(description="Mutate all entities")
class Mutation(
    UserMutation, ActivityMutation, MomentMutation
):
    @strawberry.field(description="Create a new Activity")
    def create_activity(
        self, activity: ActivityInput, info: Info
    ) -> Activity:
        activity_service = get_ActivityService(info)
        current_user = get_user_from_context(info)
        activity_dict = activity.to_dict()
        activity_dict["user_id"] = current_user.id
        activity_create = ActivityCreate(**activity_dict)
        return activity_service.create_activity_graphql(
            activity_create
        )

    @strawberry.field(
        description="Update an existing Activity"
    )
    def update_activity(
        self,
        activity_id: int,
        activity: ActivityUpdateInput,
        info: Info,
    ) -> Activity:
        activity_service = get_ActivityService(info)
        activity_dict = activity.to_dict()
        activity_update = ActivityUpdate(**activity_dict)
        return activity_service.update_activity(
            activity_id, activity_update
        )

    @strawberry.field(description="Delete an Activity")
    def delete_activity(
        self, activity_id: int, info: Info
    ) -> bool:
        activity_service = get_ActivityService(info)
        return activity_service.delete_activity(activity_id)
