from typing import Optional
from pydantic import BaseModel
from .base import MomentResponseBase
from .activity import ActivityResponse


class MomentResponse(MomentResponseBase):
    activity: Optional[ActivityResponse] = None


class MomentList(BaseModel):
    items: list[MomentResponse]
    total: int
