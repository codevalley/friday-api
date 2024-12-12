import strawberry
from strawberry.types import Info
from configs.GraphQL import (
    get_ActivityService,
    get_MomentService,
)

from schemas.graphql.Activity import (
    Activity,
    ActivityInput,
    ActivityUpdateInput,
)
from schemas.graphql.Moment import (
    Moment,
    MomentInput,
    MomentUpdateInput,
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


@strawberry.type(description="Mutate all entities")
class Mutation(UserMutation):
    @strawberry.field(description="Create a new Activity")
    def create_activity(
        self, activity: ActivityInput, info: Info
    ) -> Activity:
        activity_service = get_ActivityService(info)
        activity_dict = activity.to_dict()
        activity_create = ActivityCreate(**activity_dict)
        return activity_service.create_activity(
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

    @strawberry.field(description="Create a new Moment")
    def create_moment(
        self, moment: MomentInput, info: Info
    ) -> Moment:
        moment_service = get_MomentService(info)
        moment_dict = moment.to_dict()
        moment_create = MomentCreate(**moment_dict)
        return moment_service.create_moment(moment_create)

    @strawberry.field(
        description="Update an existing Moment"
    )
    def update_moment(
        self,
        moment_id: int,
        moment: MomentUpdateInput,
        info: Info,
    ) -> Moment:
        moment_service = get_MomentService(info)
        moment_dict = moment.to_dict()
        moment_update = MomentUpdate(**moment_dict)
        return moment_service.update_moment(
            moment_id, moment_update
        )

    @strawberry.field(description="Delete a Moment")
    def delete_moment(
        self, moment_id: int, info: Info
    ) -> bool:
        moment_service = get_MomentService(info)
        return moment_service.delete_moment(moment_id)
