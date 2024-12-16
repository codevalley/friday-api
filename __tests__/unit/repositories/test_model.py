from sqlalchemy import Column, String, Integer
from models.BaseModel import EntityMeta


class TestModel(EntityMeta):
    """A simple model for testing the BaseRepository"""

    __tablename__ = "test_models"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)  # Primary key is already indexed
    name = Column(String(50), unique=True, nullable=False)  # Unique constraint handles duplicates
    description = Column(String(200))
