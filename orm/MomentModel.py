from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    JSON,
    ForeignKey,
    String,
    CheckConstraint,
)
from sqlalchemy.orm import relationship, Mapped
from datetime import datetime, timezone
from jsonschema import validate as validate_json_schema
import json
from sqlalchemy.orm import Session
from typing import (
    Any,
    Dict,
    cast,
    TYPE_CHECKING,
    Optional,
)

from orm.BaseModel import EntityMeta

if TYPE_CHECKING:
    from orm.UserModel import User
    from orm.ActivityModel import Activity


class Moment(EntityMeta):
    """Moment Model represents a single moment or event in a person's life.

    Each moment is associated with an activity type and contains data
    specific to that activity. The data must conform to the activity's
    JSON schema.

    Attributes:
        id: Unique identifier
        user_id: ID of the user who created the moment
        activity_id: ID of the associated activity
        data: JSON data conforming to activity's schema
        timestamp: When the moment occurred
        user: User who created the moment
        activity: Associated activity
    """

    __tablename__ = "moments"

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
    activity_id: Mapped[int] = Column(
        Integer,
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Data fields
    data: Mapped[Dict[str, Any]] = Column(
        JSON, nullable=False
    )
    timestamp: Mapped[datetime] = Column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="moments"
    )
    activity: Mapped["Activity"] = relationship(
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
            "data IS NOT NULL",
            name="check_data_not_null",
        ),
        CheckConstraint(
            "user_id IS NOT NULL",
            name="check_user_id_not_null",
        ),
    )

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
        """Validate that the moment data matches the activity's schema.

        Args:
            db: Optional SQLAlchemy session to use. If not provided,
               will attempt to use the session from the instance state.

        Returns:
            True if data is valid

        Raises:
            ValueError: If data is invalid or activity schema is missing
        """
        data = self.data_dict
        if not isinstance(data, dict):
            raise ValueError(
                "moment data must be a valid JSON object"
            )

        # Load activity if not loaded
        from repositories.ActivityRepository import (
            ActivityRepository,
        )

        if not self.activity:
            # Get activity from repository
            session = (
                db
                if db is not None
                else self._sa_instance_state.session
            )
            activity_repo = ActivityRepository(session)
            activity = activity_repo.get_by_user(
                self.activity_id, self.user_id
            )
            if not activity or not activity.activity_schema:
                raise ValueError(
                    "moment must be linked to an activity with a valid schema"
                )
        else:
            activity = self.activity

        try:
            validate_json_schema(
                data, activity.activity_schema
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
