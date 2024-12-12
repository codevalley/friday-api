from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from models.BaseModel import EntityMeta
import uuid


class UserModel(EntityMeta):
    __tablename__ = "users"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    username = Column(
        String, unique=True, index=True, nullable=False
    )
    user_secret = Column(
        String, unique=True, index=True, nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now()
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
