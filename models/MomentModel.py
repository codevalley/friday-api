from sqlalchemy import Column, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from models.BaseModel import EntityMeta


class Moment(EntityMeta):
    """
    Moment Model represents a single moment or event in a person's life.
    Each moment is associated with an activity type and contains data specific to that activity.
    """
    __tablename__ = "moments"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), index=True, default=datetime.utcnow)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    data = Column(JSON)  # Flexible schema based on activity type
    
    # Relationships
    activity = relationship("Activity", back_populates="moments")

    def __repr__(self):
        return f"<Moment(id={self.id}, activity_id={self.activity_id}, timestamp='{self.timestamp}')>"
