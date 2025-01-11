"""Moment ORM model."""

from typing import TYPE_CHECKING, Optional, Dict, Any, cast
from sqlalchemy import (
    Column,
    Integer,
    JSON,
    ForeignKey,
    DateTime,
    String,
)
from sqlalchemy.orm import relationship, Session
import json
from jsonschema import validate as validate_json_schema
from datetime import datetime, UTC

from orm.BaseModel import EntityMeta

if TYPE_CHECKING:
    from orm.UserModel import User  # noqa: F401
    from orm.NoteModel import Note  # noqa: F401


class Moment(EntityMeta):
    """Moment model class."""

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
    note_id = Column(
        Integer,
        ForeignKey("notes.id", ondelete="SET NULL"),
        nullable=True,
    )
    data = Column(JSON, nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    user = relationship("User", back_populates="moments")
    activity = relationship(
        "Activity", back_populates="moments"
    )
    note = relationship("Note", back_populates="moments")

    def __init__(self, **kwargs):
        """Initialize a moment with validation.

        Args:
            **kwargs: Moment attributes

        Raises:
            ValueError: If any validation fails
        """
        # Validate required fields before initialization
        if not kwargs.get("user_id"):
            raise ValueError("user_id is required")
        if not kwargs.get("activity_id"):
            raise ValueError("activity_id is required")
        if not kwargs.get("data"):
            raise ValueError("data is required")

        # Validate data against activity schema
        data = kwargs.get("data")
        if not isinstance(data, dict):
            raise ValueError(
                "moment data must be a valid JSON object"
            )

        super().__init__(**kwargs)

    def __repr__(self) -> str:
        """String representation of the moment.

        Returns:
            String representation including id, activity_id, and timestamp
        """
        return (
            f"<Moment(id={self.id}, activity_id={self.activity_id}, "
            f"timestamp='{self.timestamp}')>"
        )

    @property
    def data_dict(self) -> Dict[str, Any]:
        """Get moment data as a dictionary.

        Returns:
            Dictionary containing the moment's data
        """
        data = self.data
        if data is None:
            return {}
        if isinstance(data, str):
            return json.loads(data)
        if isinstance(data, dict):
            return data
        return cast(Dict[str, Any], data)

    def validate_data(
        self, db: Optional[Session] = None
    ) -> bool:
        """Validate moment data against activity schema.

        Args:
            db: Optional database session for loading activity

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails
        """
        if not self.data:
            raise ValueError("data is required")

        if not isinstance(self.data, dict):
            raise ValueError(
                "moment data must be a valid JSON object"
            )

        # If we have a database session, load the activity
        # to validate against its schema
        if db and self.activity_id:
            from orm.ActivityModel import Activity

            activity = (
                db.query(Activity)
                .filter_by(id=self.activity_id)
                .first()
            )
            if not activity:
                raise ValueError(
                    f"Activity {self.activity_id} not found"
                )

            try:
                validate_json_schema(
                    self.data, activity.activity_schema
                )
            except Exception as e:
                raise ValueError(
                    f"Invalid moment data: {str(e)}"
                )

        return True

    def set_data(self, data: Dict[str, Any]) -> None:
        """Set moment data with validation.

        Args:
            data: New data to set

        Raises:
            ValueError: If data is invalid according to activity schema
        """
        self.data = data
        self.validate_data()
