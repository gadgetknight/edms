# models/base_model.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    Date,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields"""

    __abstract__ = True

    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    modified_date = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
