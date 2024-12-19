from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class ActivityResponseBase(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MomentResponseBase(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    activity_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
