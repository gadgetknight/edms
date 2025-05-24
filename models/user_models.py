# models/user_models.py

"""
EDSI Veterinary Management System - User and Authentication Models
Version: 2.0.0
Purpose: Simplified user authentication models with clean relationships.
         Removed over-complexity and focused on essential user management.
Last Updated: May 24, 2025
Author: Claude Assistant

Changelog:
- v2.0.0 (2025-05-24):
    - Complete rewrite for Phase 1 (Chunk 1) simplification
    - Simplified User model with essential fields only
    - Clean Role and UserRole relationship management
    - Removed SystemConfig (deferred to future phases)
    - Fixed circular import issues
    - Clean inheritance from BaseModel and Base
    - Simplified field definitions and constraints
    - Focused on working authentication foundation
    - Consistent naming and documentation
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from config.database_config import Base
from models.base_model import BaseModel


class Role(BaseModel):
    """
    User roles for permission management.
    """
    
    __tablename__ = "roles"
    
    role_id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        doc="Unique role identifier"
    )
    
    name = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        doc="Role name (e.g., 'admin', 'user', 'veterinarian')"
    )
    
    description = Column(
        String(255),
        nullable=True,
        doc="Role description"
    )
    
    # Relationships
    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        doc="Users assigned to this role"
    )
    
    def __repr__(self):
        return f"<Role(role_id={self.role_id}, name='{self.name}')>"


class UserRole(Base):
    """
    Association table for User-Role many-to-many relationship.
    This is a simple link table without audit fields.
    """
    
    __tablename__ = "user_roles"
    
    user_id = Column(
        String(20),
        ForeignKey("users.user_id"),
        primary_key=True,
        doc="User identifier"
    )
    
    role_id = Column(
        Integer,
        ForeignKey("roles.role_id"),
        primary_key=True,
        doc="Role identifier"
    )
    
    def __repr__(self):
        return f"<UserRole(user_id='{self.user_id}', role_id={self.role_id})>"


class User(BaseModel):
    """
    User account for authentication and system access.
    """
    
    __tablename__ = "users"
    
    user_id = Column(
        String(20),
        primary_key=True,
        index=True,
        doc="Unique user login identifier"
    )
    
    password_hash = Column(
        String(255),
        nullable=False,
        doc="Hashed password for authentication"
    )
    
    user_name = Column(
        String(100),
        nullable=True,
        doc="Display name for the user"
    )
    
    email = Column(
        String(100),
        unique=True,
        index=True,
        nullable=True,
        doc="User email address"
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the user account is active"
    )
    
    last_login = Column(
        DateTime,
        nullable=True,
        doc="Timestamp of last successful login"
    )
    
    # Optional user preferences (simplified)
    printer_id = Column(
        String(20),
        nullable=True,
        doc="Default printer for this user"
    )
    
    default_screen_colors = Column(
        String(100),
        nullable=True,
        doc="User's preferred screen color scheme"
    )
    
    # Relationships
    roles = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        doc="Roles assigned to this user"
    )
    
    def __repr__(self):
        return f"<User(user_id='{self.user_id}', user_name='{self.user_name}', active={self.is_active})>"
    
    def has_role(self, role_name: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            role_name: Name of the role to check
            
        Returns:
            True if user has the role, False otherwise
        """
        return any(role.name == role_name for role in self.roles)
    
    def is_admin(self) -> bool:
        """
        Check if user has admin privileges.
        
        Returns:
            True if user is an admin, False otherwise
        """
        return self.has_role("admin")
    
    def update_last_login(self) -> None:
        """
        Update the last login timestamp to current time.
        """
        self.last_login = datetime.utcnow()
    
    def deactivate(self) -> None:
        """
        Deactivate the user account.
        """
        self.is_active = False
    
    def activate(self) -> None:
        """
        Activate the user account.
        """
        self.is_active = True