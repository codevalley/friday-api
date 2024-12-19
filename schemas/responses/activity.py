from typing import Optional, List
from .base import ActivityResponseBase
from .moment import MomentResponse


class ActivityResponse(ActivityResponseBase):
    moments: Optional[List[MomentResponse]] = None
