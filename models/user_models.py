# models/user_models.py

"""
EDSI Veterinary Management System - User and Role Models
Version: 1.1.0
Purpose: Defines User, Role, and UserRole SQLAlchemy models.
Last Updated: May 18, 2025
Author: Claude Assistant

Changelog:
- v1.1.0 (2025-05-18):
    - Added Role model (role_id, name, description).
    - Added UserRole association model (user_id, role_id).
    - Added relationship 'roles' to User model via UserRole.
    - Added relationship 'users' to Role model via UserRole.
- v1.0.0 (Date Unknown): Initial User and SystemConfig models.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from .base_model import (
    BaseModel,
    Base,
)  # Ensure Base is imported if UserRole is defined using it directly


# --- Role Model ---
class Role(BaseModel):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255))

    # Relationship to users (many-to-many through UserRole)
    # users = relationship("User", secondary="user_roles", back_populates="roles")
    # The secondary table string name "user_roles" will be resolved by SQLAlchemy.
    # Or, if UserRole is defined as a model:
    users = relationship(
        "User", secondary=lambda: UserRole.__table__, back_populates="roles"
    )

    def __repr__(self):
        return f"<Role(role_id={self.role_id}, name='{self.name}')>"


# --- UserRole Association Table/Model ---
# This can be defined as a simple table or as a model class inheriting Base.
# Using a model class is often preferred if you might want to add extra columns
# to the association later (e.g., date_assigned).


class UserRole(Base):  # Inherit from Base directly for association tables
    __tablename__ = "user_roles"
    # No BaseModel features like created_date needed for a simple join table usually

    user_id = Column(String(20), ForeignKey("users.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"), primary_key=True)

    def __repr__(self):
        return f"<UserRole(user_id='{self.user_id}', role_id={self.role_id})>"


# --- User Model ---
class User(BaseModel):
    """User table for login and authentication"""

    __tablename__ = "users"

    user_id = Column(String(20), primary_key=True, index=True)  # Added index
    password_hash = Column(String(255), nullable=False)
    user_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    printer_id = Column(String(20))  # Nullable by default
    default_screen_colors = Column(String(100))  # Nullable by default

    # Relationship to roles (many-to-many through UserRole)
    # The secondary argument points to the UserRole association table/model.
    roles = relationship("Role", secondary=UserRole.__table__, back_populates="users")

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', user_name='{self.user_name}')>"


class SystemConfig(BaseModel):
    """System configuration parameters"""

    __tablename__ = "system_config"

    config_key = Column(String(50), primary_key=True)
    config_value = Column(String(255))
    description = Column(String(255))

    def __repr__(self):
        return f"<SystemConfig(config_key='{self.config_key}', value='{self.config_value}')>"
