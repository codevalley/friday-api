from typing import Type
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeMeta

from configs.Database import Engine

# Create base with type information
Base = declarative_base()
EntityMeta: Type[DeclarativeMeta] = Base


def init():
    EntityMeta.metadata.create_all(bind=Engine)
