from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.orm import relationship

from models.BaseModel import EntityMeta


class Activity(EntityMeta):
    """
    Activity Model represents different types of activities that can be logged as moments.
    Each activity defines its own schema for validating moment data.
    """
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    description = Column(String(1000))
    activity_schema = Column(JSON)  # JSON Schema for validating moment data
    icon = Column(String(255))  # Icon identifier or URL
    color = Column(String(50))  # Color code for UI representation
    
    # Relationships
    moments = relationship("Moment", back_populates="activity", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Activity(id={self.id}, name='{self.name}')>"
