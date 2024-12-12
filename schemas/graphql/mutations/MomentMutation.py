import strawberry
from typing import Optional
from datetime import datetime
import json

from services.MomentService import MomentService
from schemas.pydantic.MomentSchema import MomentCreate
from schemas.graphql.Moment import Moment, MomentInput
from configs.GraphQL import get_MomentService, get_user_from_context


@strawberry.type
class MomentMutation:
    @strawberry.mutation
    async def create_moment(
        self,
        info: strawberry.Info,
        moment: MomentInput
    ) -> Moment:
        """Create a new moment"""
        current_user = get_user_from_context(info)
        service = get_MomentService(info)
        
        # Convert the input using the to_dict method
        moment_dict = moment.to_dict()
        moment_data = MomentCreate(**moment_dict)
        
        db_moment = service.create_moment(
            moment_data=moment_data,
            user_id=current_user.id
        )
        return Moment.from_db(db_moment)
