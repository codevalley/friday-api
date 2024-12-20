import strawberry
from schemas.graphql.mutations.UserMutation import (
    UserMutation,
)
from schemas.graphql.mutations.ActivityMutation import (
    ActivityMutation,
)
from schemas.graphql.mutations.MomentMutation import (
    MomentMutation,
)
from schemas.graphql.mutations.NoteMutation import (
    NoteMutation,
)


@strawberry.type(description="Mutate all entities")
class Mutation(
    UserMutation,
    ActivityMutation,
    MomentMutation,
    NoteMutation,
):
    """Root mutation type that inherits
    all mutations from specific mutation types"""

    pass
