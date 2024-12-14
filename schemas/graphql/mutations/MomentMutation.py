import strawberry
from strawberry.types import Info
from fastapi import HTTPException

from ..types.Moment import Moment, MomentInput
from schemas.pydantic.MomentSchema import (
    MomentUpdate,
)
from configs.GraphQL import (
    get_MomentService,
    get_user_from_context,
)


@strawberry.type
class MomentMutation:
    @strawberry.mutation
    async def create_moment(
        self, info: Info, moment: MomentInput
    ) -> Moment:
        """Create a new moment"""
        current_user = get_user_from_context(info)
        if not current_user:
            raise HTTPException(
                status_code=401, detail="Unauthorized"
            )
        service = get_MomentService(info)

        # Convert the input to domain model
        moment_data = moment.to_domain()
        db_moment = service.create_moment(
            moment_data=moment_data, user_id=current_user.id
        )
        return Moment.from_db(db_moment)

    @strawberry.mutation
    async def update_moment(
        self,
        info: Info,
        moment_id: int,
        moment: MomentInput,
    ) -> Moment:
        """Update a moment"""
        current_user = get_user_from_context(info)
        if not current_user:
            raise HTTPException(
                status_code=401, detail="Unauthorized"
            )
        service = get_MomentService(info)

        # Convert the input to domain model
        moment_data = moment.to_domain()
        db_moment = service.update_moment(
            moment_id=moment_id,
            moment_data=MomentUpdate(
                data=moment_data.data,
                timestamp=moment_data.timestamp,
            ),
            user_id=current_user.id,
        )
        return Moment.from_db(db_moment)
