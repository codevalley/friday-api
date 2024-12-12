import strawberry
from typing import Optional, Dict
from datetime import datetime
import json


@strawberry.input
class MomentInput:
    activityId: int = strawberry.field(
        name="activityId"
    )  # GraphQL camelCase
    data: str  # JSON string for the data
    timestamp: Optional[datetime] = None

    @strawberry.field
    def parsed_data(self) -> Dict:
        return json.loads(self.data)


@strawberry.type
class Moment:
    id: int
    activityId: int = strawberry.field(
        name="activityId"
    )  # GraphQL camelCase
    data: str  # JSON string for the data
    timestamp: datetime
    userId: str = strawberry.field(
        name="userId"
    )  # GraphQL camelCase

    @classmethod
    def from_db(cls, db_moment):
        return cls(
            id=db_moment.id,
            activityId=db_moment.activity_id,
            data=json.dumps(
                db_moment.data
            ),  # Convert dict to JSON string
            timestamp=db_moment.timestamp,
            userId=db_moment.user_id,
        )
