from typing import Dict, Optional, List
from dataclasses import dataclass
import re
from utils.json_utils import ensure_dict, ensure_string


@dataclass
class ActivityData:
    """
    Base data structure for activity data, works with Python dicts internally.
    """

    name: str
    description: str
    activity_schema: Dict
    icon: str
    color: str
    id: Optional[int] = None
    user_id: Optional[str] = None
    moment_count: Optional[int] = None
    moments: Optional[List[Dict]] = None

    def __post_init__(self):
        """Validate data after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate the activity data"""
        # Name validation
        if not isinstance(self.name, str):
            raise ValueError("name must be a string")
        if len(self.name) < 1 or len(self.name) > 255:
            raise ValueError(
                "name must be between 1 and 255 characters"
            )

        # Description validation
        if not isinstance(self.description, str):
            raise ValueError("description must be a string")
        if (
            len(self.description) < 1
            or len(self.description) > 1000
        ):
            raise ValueError(
                "description must be between 1 and 1000 characters"
            )

        # Activity schema validation
        if not isinstance(self.activity_schema, dict):
            raise ValueError(
                "activity_schema must be a dictionary"
            )
        # Could add JSON Schema validation here if needed

        # Icon validation
        if not isinstance(self.icon, str):
            raise ValueError("icon must be a string")
        if len(self.icon) < 1 or len(self.icon) > 255:
            raise ValueError(
                "icon must be between 1 and 255 characters"
            )

        # Color validation
        if not isinstance(self.color, str):
            raise ValueError("color must be a string")
        if not re.match(r"^#[0-9A-Fa-f]{6}$", self.color):
            raise ValueError(
                "color must be a valid hex color code (e.g., #4A90E2)"
            )

        # ID validation
        if self.id is not None:
            if not isinstance(self.id, int) or self.id <= 0:
                raise ValueError(
                    "id must be a positive integer"
                )

        # User ID validation
        if self.user_id is not None:
            if not isinstance(self.user_id, str):
                raise ValueError("user_id must be a string")

        # Moment count validation
        if self.moment_count is not None:
            if (
                not isinstance(self.moment_count, int)
                or self.moment_count < 0
            ):
                raise ValueError(
                    "moment_count must be a non-negative integer"
                )

    @classmethod
    def from_dict(cls, data: Dict) -> "ActivityData":
        """Create from a dictionary (used by both Pydantic and GraphQL)"""
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")

        required_fields = [
            "name",
            "description",
            "activity_schema",
            "icon",
            "color",
        ]
        for field in required_fields:
            snake_case = field
            camel_case = field[0].lower() + field[
                1:
            ].replace("_", "")
            if (
                snake_case not in data
                and camel_case not in data
            ):
                raise ValueError(f"{field} is required")

        return cls(
            name=data["name"],
            description=data["description"],
            activity_schema=ensure_dict(
                data.get("activity_schema")
                or data.get("activitySchema", {})
            ),
            icon=data["icon"],
            color=data["color"],
            id=data.get("id"),
            user_id=data.get("user_id")
            or data.get("userId"),
            moment_count=data.get("moment_count")
            or data.get("momentCount", 0),
            moments=data.get("moments", []),
        )

    def to_dict(self, graphql: bool = False) -> Dict:
        """Convert to dictionary, optionally using GraphQL field naming"""
        if graphql:
            base = {
                "name": self.name,
                "description": self.description,
                "activitySchema": ensure_string(
                    self.activity_schema
                ),
                "icon": self.icon,
                "color": self.color,
                "momentCount": self.moment_count or 0,
            }
            if self.user_id:
                base["userId"] = self.user_id
        else:
            base = {
                "name": self.name,
                "description": self.description,
                "activity_schema": self.activity_schema,
                "icon": self.icon,
                "color": self.color,
                "moment_count": self.moment_count or 0,
            }
            if self.user_id:
                base["user_id"] = self.user_id

        if self.id is not None:
            base["id"] = self.id

        return base

    def to_json_dict(self, graphql: bool = False) -> Dict:
        """Convert to dictionary with JSON strings for schema"""
        result = self.to_dict(graphql)
        if graphql:
            result["activitySchema"] = ensure_string(
                self.activity_schema
            )
        else:
            result["activity_schema"] = ensure_string(
                self.activity_schema
            )
        return result
