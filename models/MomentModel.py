from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    JSON,
    ForeignKey,
    String,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from jsonschema import validate as validate_json_schema
import json

from models.BaseModel import EntityMeta


class Moment(EntityMeta):
    """
    Moment Model represents a single moment or event in a person's life.
    Each moment is associated with an activity type and contains data
    specific to that activity.
    """

    __tablename__ = "moments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    activity_id = Column(
        Integer,
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
    )
    data = Column(JSON, nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="moments")
    activity = relationship(
        "Activity", back_populates="moments"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "timestamp IS NOT NULL",
            name="check_timestamp_not_null",
        ),
        CheckConstraint(
            "activity_id IS NOT NULL",
            name="check_activity_id_not_null",
        ),
        CheckConstraint(
            "data IS NOT NULL", name="check_data_not_null"
        ),
        CheckConstraint(
            "user_id IS NOT NULL",
            name="check_user_id_not_null",
        ),
    )

    def __repr__(self):
        return (
            f"<Moment(id={self.id}, activity_id={self.activity_id}, "
            f"timestamp='{self.timestamp}')>"
        )

    @property
    def data_dict(self) -> dict:
        """Return data as a dictionary"""
        if isinstance(self.data, str):
            return json.loads(self.data)
        return self.data

    def validate_data(self):
        """Validate that the moment data matches the activity's schema"""
        if not isinstance(self.data, dict):
            raise ValueError(
                "moment data must be a valid JSON object"
            )

        if (
            not self.activity
            or not self.activity.activity_schema
        ):
            raise ValueError(
                "moment must be linked to an activity with a valid schema"
            )

        try:
            validate_json_schema(
                self.data, self.activity.activity_schema
            )
        except Exception as e:
            raise ValueError(
                f"Invalid moment data: {str(e)}"
            )

        return True
