"""GraphQL mutations."""

import strawberry

from .mutations.UserMutation import UserMutation
from .mutations.ActivityMutation import ActivityMutation
from .mutations.MomentMutation import MomentMutation
from .mutations.NoteMutation import NoteMutation
from .mutations.TaskMutation import TaskMutation


@strawberry.type
class Mutation(
    UserMutation,
    ActivityMutation,
    MomentMutation,
    NoteMutation,
    TaskMutation,
):
    """Root mutation type."""

    pass
