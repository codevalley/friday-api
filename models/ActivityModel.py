from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
    CheckConstraint,
    ForeignKey,
    select,
    func,
    DateTime,
)
from sqlalchemy.orm import (
    relationship,
    column_property,
    Mapped,
)
from jsonschema import validate as validate_json_schema
import json
from typing import (
    Any,
    Dict,
    cast,
    List,
    TYPE_CHECKING,
    Optional,
)
from datetime import datetime

from models.BaseModel import EntityMeta
from models.MomentModel import Moment

if TYPE_CHECKING:
    from models.UserModel import User


class Activity(EntityMeta):
    """Activity Model represents different types of activities
    that can be logged.

    Each activity defines its own schema for validating moment data.
    This ensures that all moments logged for this activity conform
    to the expected structure.

    Attributes:
        id: Unique identifier
        user_id: ID of the user who created the activity
        name: Display name of the activity
        description: Optional description
        activity_schema: JSON Schema for validating moment data
        icon: Display icon (emoji)
        color: Display color (hex code)
        moment_count: Number of moments using this activity
        moments: List of moments using this activity
        user: User who created the activity
        created_at: When the activity was created
        updated_at: When the activity was last updated
    """

    __tablename__ = "activities"

    # Primary key
    id: Mapped[int] = Column(
        Integer, primary_key=True, index=True
    )

    # Foreign keys
    user_id: Mapped[str] = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Data fields
    name: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[str] = Column(String(1000))
    activity_schema: Mapped[Dict[str, Any]] = Column(
        JSON, nullable=False
    )
    icon: Mapped[str] = Column(String(255), nullable=False)
    color: Mapped[str] = Column(String(7), nullable=False)

    # Timestamp fields
    created_at: Mapped[datetime] = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime,
        nullable=True,
        default=None,
        onupdate=datetime.utcnow,
    )

    # Computed fields
    moment_count: Mapped[int] = column_property(
        select(func.count(Moment.id))
        .where(Moment.activity_id == id)
        .scalar_subquery()
        .correlate_except(Moment)
    )

    # Relationships
    moments: Mapped[List["Moment"]] = relationship(
        "Moment",
        back_populates="activity",
        cascade="all, delete-orphan",
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="activities"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "name IS NOT NULL AND name != ''",
            name="check_name_not_empty",
        ),
        CheckConstraint(
            "activity_schema IS NOT NULL",
            name="check_schema_not_null",
        ),
        CheckConstraint(
            "icon IS NOT NULL AND icon != ''",
            name="check_icon_not_empty",
        ),
        CheckConstraint(
            "color IS NOT NULL AND color != ''",
            name="check_color_not_empty",
        ),
        CheckConstraint(
            "color ~ '^#[0-9A-Fa-f]{6}$'",
            name="check_color_format",
        ),
    )

    def __repr__(self) -> str:
        """String representation of the activity.

        Returns:
            String representation including id and name
        """
        return (
            f"<Activity(id={self.id}, name='{self.name}')>"
        )

    @property
    def activity_schema_dict(self) -> Dict[str, Any]:
        """Get activity schema as a dictionary.

        Returns:
            Dictionary containing the activity's schema
        """
        schema = self.activity_schema
        if schema is None:
            return {}
        if isinstance(schema, str):
            return json.loads(schema)
        if isinstance(schema, dict):
            return schema
        return cast(Dict[str, Any], schema)

    def validate_schema(self) -> bool:
        """Validate that the activity_schema is a valid JSON Schema.

        Returns:
            True if schema is valid

        Raises:
            ValueError: If schema is invalid or malformed
        """
        schema_dict = self.activity_schema_dict
        if not isinstance(schema_dict, dict):
            raise ValueError(
                "activity_schema must be a valid JSON object"
            )

        # Basic schema validation - should be a valid JSON Schema
        meta_schema = {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "properties": {"type": "object"},
            },
            "required": ["type"],
        }

        try:
            validate_json_schema(schema_dict, meta_schema)
            return True
        except Exception as e:
            raise ValueError(
                f"Invalid JSON Schema: {str(e)}"
            )

    def validate_moment_data(
        self, moment_data: Dict[str, Any]
    ) -> bool:
        """Validate moment data against this activity's schema.

        Args:
            moment_data: The data to validate

        Returns:
            True if data is valid

        Raises:
            ValueError: If data is invalid according to schema
        """
        try:
            schema = self.activity_schema_dict
            validate_json_schema(moment_data, schema)
            return True
        except Exception as e:
            raise ValueError(
                f"Invalid moment data: {str(e)}"
            )

    def set_schema(self, schema: Dict[str, Any]) -> None:
        """Set activity schema with validation.

        Args:
            schema: New schema to set

        Raises:
            ValueError: If schema is invalid
        """
        self.activity_schema = schema
        self.validate_schema()
