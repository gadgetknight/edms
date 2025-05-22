# models/user_models.py

"""
EDSI Veterinary Management System - User and Role Models
Version: 1.1.1
Purpose: Defines User, Role, and UserRole SQLAlchemy models.
         Added 'email' column to User model.
Last Updated: May 21, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v1.1.1 (2025-05-21):
    - Added `email = Column(String(100), unique=True, index=True, nullable=True)` to User model.
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
)


class Role(BaseModel):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255))

    users = relationship(
        "User", secondary=lambda: UserRole.__table__, back_populates="roles"
    )

    def __repr__(self):
        return f"<Role(role_id={self.role_id}, name='{self.name}')>"


class UserRole(Base):
    __tablename__ = "user_roles"
    user_id = Column(String(20), ForeignKey("users.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"), primary_key=True)

    def __repr__(self):
        return f"<UserRole(user_id='{self.user_id}', role_id={self.role_id})>"


class User(BaseModel):
    """User table for login and authentication"""

    __tablename__ = "users"

    user_id = Column(String(20), primary_key=True, index=True)
    password_hash = Column(String(255), nullable=False)
    user_name = Column(String(100))

    # ADDED EMAIL COLUMN HERE
    email = Column(String(100), unique=True, index=True, nullable=True)

    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    printer_id = Column(String(20))
    default_screen_colors = Column(String(100))

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
