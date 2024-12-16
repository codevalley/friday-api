from sqlalchemy import Column, String, Integer
from models.BaseModel import EntityMeta


class TestModel(EntityMeta):
    """A simple model for testing the BaseRepository"""

    __tablename__ = "test_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
