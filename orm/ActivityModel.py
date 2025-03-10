from datetime import datetime, UTC
from typing import (
    Dict,
    Any,
    List,
    Optional,
    cast,
    TYPE_CHECKING,
)
import json
import re
from jsonschema import validate as validate_json_schema
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    select,
    func,
    DateTime,
    CheckConstraint,
    UniqueConstraint,
    Enum,
)
from sqlalchemy.orm import (
    Mapped,
    relationship,
    column_property,
)
from sqlalchemy.dialects.mysql import JSON

from .BaseModel import EntityMeta
from domain.activity import ProcessingStatus

if TYPE_CHECKING:
    from orm.UserModel import User
from orm.MomentModel import Moment


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
        processing_status: Status of the activity processing
        schema_render: JSON Schema render
        processed_at: Timestamp of when the activity was processed
    """

    __tablename__ = "activities"

    # Regular expression for validating hex color codes
    COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")

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
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        onupdate=lambda: datetime.now(UTC),
    )

    # Computed fields
    moment_count: Mapped[int] = column_property(
        select(func.count(1))
        .select_from(Moment)
        .where(Moment.activity_id == id)
        .correlate_except(Moment)
        .scalar_subquery()
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

    # Constraints that are database-agnostic
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
        UniqueConstraint(
            "name",
            "user_id",
            name="unique_name_per_user",
        ),
    )

    # Add new columns after existing ones
    processing_status: Mapped[str] = Column(
        Enum(ProcessingStatus),
        nullable=False,
        default=ProcessingStatus.NOT_PROCESSED,
        index=True,
    )
    schema_render: Mapped[
        Optional[Dict[str, Any]]
    ] = Column(JSON, nullable=True)
    processed_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    def __init__(self, **kwargs):
        """Initialize an activity with validation.

        Args:
            **kwargs: Activity attributes

        Raises:
            ValueError: If any validation fails
        """
        # Validate required fields before initialization
        if not kwargs.get("user_id"):
            raise ValueError("user_id is required")

        # Validate color if provided
        self.validate_color(kwargs.get("color"))

        # Validate schema if provided
        schema = kwargs.get("activity_schema")
        if schema:
            try:
                self.validate_schema_dict(schema)
            except Exception as e:
                raise ValueError(
                    f"Invalid schema: {str(e)}"
                )

        super().__init__(**kwargs)

    @classmethod
    def validate_color(cls, color: Optional[str]) -> None:
        """Validate the color format.

        Args:
            color: The color value to validate

        Raises:
            ValueError: If color is invalid
        """
        if (
            color is not None
            and not cls.COLOR_PATTERN.match(color)
        ):
            raise ValueError(
                "Color must be a valid hex code (e.g., #FF0000)"
            )

    @classmethod
    def validate_schema_dict(
        cls, schema: Dict[str, Any]
    ) -> bool:
        """Validate a schema dictionary without requiring an instance.

        Args:
            schema: Schema dictionary to validate

        Returns:
            True if valid

        Raises:
            ValueError: If schema is invalid
        """
        if not isinstance(schema, dict):
            raise ValueError(
                "activity_schema must be a valid JSON object"
            )

        meta_schema = {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "properties": {"type": "object"},
            },
            "required": ["type", "properties"],
        }

        try:
            validate_json_schema(schema, meta_schema)
            if schema.get("type") != "object":
                raise ValueError(
                    "activity_schema must be a valid JSON object"
                )
            return True
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(
                f"Invalid JSON Schema: {str(e)}"
            )

    def __repr__(self) -> str:
        """String representation of the activity.

        Returns:
            String representation including id and name
        """
        escaped_name = self.name.replace("'", "\\'")
        return f"<Activity(id={self.id}, name='{escaped_name}')>"

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
