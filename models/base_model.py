# models/base_model.py

"""
EDSI Veterinary Management System - Base Model Definition
Version: 1.0.2
Purpose: Defines the declarative base and a base model class with common audit fields.
Last Updated: May 19, 2025
Author: Claude Assistant

Changelog:
- v1.0.2 (2025-05-19):
    - Added `created_by` and `modified_by` audit columns to BaseModel.
- v1.0.1 (2025-05-17):
    - Initial definition of Base and BaseModel with created_date and modified_date.
"""

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Base for all SQLAlchemy model classes
Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model that provides common audit fields for all tables.
    - created_date: Timestamp of when the record was created.
    - modified_date: Timestamp of when the record was last modified.
    - created_by: User ID of the user who created the record.
    - modified_by: User ID of the user who last modified the record.
    """

    __abstract__ = True  # Indicates that this class should not be mapped to a database table itself

    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    modified_date = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    created_by = Column(
        String(50), nullable=True
    )  # Stores the user_id (e.g., 'ADMIN', 'TM')
    modified_by = Column(String(50), nullable=True)  # Stores the user_id

    def __repr__(self):
        # Generic representation, subclasses might want to override for more specific info
        pk_name = self.__mapper__.primary_key[0].name
        pk_value = getattr(self, pk_name, "Unknown")
        return f"<{self.__class__.__name__} {pk_name}={pk_value}>"
