from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
    CheckConstraint,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from jsonschema import validate as validate_json_schema

from models.BaseModel import EntityMeta
from models.UserModel import User


class Activity(EntityMeta):
    """
    Activity Model represents different types of activities that can be logged as moments.
    Each activity defines its own schema for validating moment data.
    """

    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    activity_schema = Column(
        JSON, nullable=False
    )  # JSON Schema for validating moment data
    icon = Column(String(255), nullable=False)
    color = Column(String(7), nullable=False)

    # Relationships
    user = relationship("User", back_populates="activities")
    moments = relationship(
        "Moment",
        back_populates="activity",
        cascade="all, delete-orphan",
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
    )

    def __repr__(self):
        return (
            f"<Activity(id={self.id}, name='{self.name}')>"
        )

    def validate_schema(self):
        """Validate that the activity_schema is a valid JSON Schema"""
        if not isinstance(self.activity_schema, dict):
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
            validate_json_schema(
                self.activity_schema, meta_schema
            )
        except Exception as e:
            raise ValueError(
                f"Invalid JSON Schema: {str(e)}"
            )

        return True
