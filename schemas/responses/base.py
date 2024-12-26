from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ActivityResponseBase(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MomentResponseBase(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    activity_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
