# models/base_model.py

"""
EDSI Veterinary Management System - Base Model Definition
Version: 2.0.0
Purpose: Simplified base model with essential audit fields and clean declarative base.
         Removed over-complexity and focused on stable foundation.
Last Updated: May 24, 2025
Author: Claude Assistant

Changelog:
- v2.0.0 (2025-05-24):
    - Complete rewrite for Phase 1 (Chunk 1) simplification
    - Removed circular import issues by importing Base from database_config
    - Simplified BaseModel with essential audit fields only
    - Clean datetime handling without over-engineering
    - Removed unnecessary complexity in __repr__ method
    - Clear separation between Base and BaseModel
    - Focused on stable, working foundation
    - Consistent audit field naming and types
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, String
from config.database_config import Base


class BaseModel(Base):
    """
    Abstract base model providing common audit fields for all database tables.

    Provides:
    - created_date: When the record was created
    - modified_date: When the record was last modified
    - created_by: User ID who created the record
    - modified_by: User ID who last modified the record
    """

    __abstract__ = True  # This class should not be mapped to a database table

    # Audit fields
    created_date = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Timestamp when record was created",
    )

    modified_date = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Timestamp when record was last modified",
    )

    created_by = Column(
        String(50), nullable=True, doc="User ID who created this record"
    )

    modified_by = Column(
        String(50), nullable=True, doc="User ID who last modified this record"
    )

    def __repr__(self):
        """
        Simple string representation of the model instance.
        Uses the first primary key column for identification.
        """
        try:
            # Get the primary key column name and value
            primary_key = self.__mapper__.primary_key[0]
            pk_name = primary_key.name
            pk_value = getattr(self, pk_name, "Unknown")

            return f"<{self.__class__.__name__}({pk_name}={pk_value})>"

        except (IndexError, AttributeError):
            # Fallback if primary key detection fails
            return f"<{self.__class__.__name__}(id=Unknown)>"

    def update_modified_by(self, user_id: str) -> None:
        """
        Update the modified_by field with the given user_id.

        Args:
            user_id: The ID of the user making the modification
        """
        self.modified_by = user_id
        # Note: modified_date will be automatically updated by SQLAlchemy onupdate

    def set_created_by(self, user_id: str) -> None:
        """
        Set the created_by field with the given user_id.
        This should only be called when creating new records.

        Args:
            user_id: The ID of the user creating the record
        """
        self.created_by = user_id
        if not self.modified_by:
            self.modified_by = user_id
