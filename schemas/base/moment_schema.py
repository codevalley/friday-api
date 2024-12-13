from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from utils.json_utils import ensure_dict, ensure_string


@dataclass
class MomentData:
    """Base data struct for moment data, works with Python dicts internally"""

    activity_id: int
    data: Dict
    timestamp: Optional[datetime] = None
    id: Optional[int] = None
    user_id: Optional[str] = None

    def __post_init__(self):
        """Validate data after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate the moment data"""
        if (
            not isinstance(self.activity_id, int)
            or self.activity_id <= 0
        ):
            raise ValueError(
                "activity_id must be a positive integer"
            )

        if not isinstance(self.data, dict):
            raise ValueError("data must be a dictionary")

        if self.timestamp is not None and not isinstance(
            self.timestamp, datetime
        ):
            raise ValueError(
                "timestamp must be a datetime object"
            )

        if self.id is not None and (
            not isinstance(self.id, int) or self.id <= 0
        ):
            raise ValueError(
                "id must be a positive integer"
            )

    @classmethod
    def from_dict(cls, data: Dict) -> "MomentData":
        """Create from a dictionary (used by both Pydantic and GraphQL)"""
        activity_id = data.get("activity_id") or data.get(
            "activityId"
        )
        if not activity_id:
            raise ValueError("activity_id is required")

        return cls(
            activity_id=activity_id,
            data=ensure_dict(data.get("data", {})),
            timestamp=data.get("timestamp")
            or datetime.utcnow(),
            id=data.get("id"),
            user_id=data.get("user_id")
            or data.get("userId"),
        )

    def to_dict(self, graphql: bool = False) -> Dict:
        """Convert to dictionary, optionally using GraphQL field naming"""
        base = {
            "data": ensure_dict(self.data),
            "timestamp": self.timestamp
            or datetime.utcnow(),
        }

        if graphql:
            base.update(
                {
                    "activityId": self.activity_id,
                    "userId": self.user_id,
                }
            )
        else:
            base.update(
                {
                    "activity_id": self.activity_id,
                    "user_id": self.user_id,
                }
            )

        if self.id is not None:
            base["id"] = self.id

        return base

    def to_json_dict(self, graphql: bool = False) -> Dict:
        """Convert to dictionary with JSON string for data field"""
        result = self.to_dict(graphql)
        result["data"] = ensure_string(result["data"])
        return result
