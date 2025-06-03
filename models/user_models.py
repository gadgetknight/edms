# models/user_models.py

"""
EDSI Veterinary Management System - User and Authentication Models
Version: 2.0.1
Purpose: Simplified user authentication models with clean relationships.
         Added password hashing and verification methods to User model.
Last Updated: May 29, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v2.0.1 (2025-05-29):
    - Added bcrypt import for password hashing.
    - Added set_password(self, password) method to User class to hash
      and store passwords using bcrypt.
    - Added check_password(self, password) method to User class to verify
      passwords against the stored bcrypt hash.
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
import bcrypt  # Added for password hashing

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
        doc="Unique role identifier",
    )

    name = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        doc="Role name (e.g., 'ADMIN', 'USER', 'VETERINARIAN')",  # Doc updated
    )

    description = Column(String(255), nullable=True, doc="Role description")

    # Relationships
    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        doc="Users assigned to this role",
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
        String(20), ForeignKey("users.user_id"), primary_key=True, doc="User identifier"
    )

    role_id = Column(
        Integer, ForeignKey("roles.role_id"), primary_key=True, doc="Role identifier"
    )

    def __repr__(self):
        return f"<UserRole(user_id='{self.user_id}', role_id={self.role_id})>"


class User(BaseModel):
    """
    User account for authentication and system access.
    """

    __tablename__ = "users"

    user_id = Column(
        String(20), primary_key=True, index=True, doc="Unique user login identifier"
    )

    password_hash = Column(
        String(255),  # bcrypt hashes are typically 60 chars, 255 is ample
        nullable=False,
        doc="Hashed password for authentication",
    )

    user_name = Column(String(100), nullable=True, doc="Display name for the user")

    email = Column(
        String(100), unique=True, index=True, nullable=True, doc="User email address"
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the user account is active",
    )

    last_login = Column(
        DateTime, nullable=True, doc="Timestamp of last successful login"
    )

    # Optional user preferences (simplified)
    printer_id = Column(String(20), nullable=True, doc="Default printer for this user")

    default_screen_colors = Column(
        String(100), nullable=True, doc="User's preferred screen color scheme"
    )

    # Relationships
    roles = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        doc="Roles assigned to this user",
    )

    def set_password(self, password: str):
        """
        Hashes the provided password and stores it.
        """
        if not password:
            # Or raise an error, depending on policy for empty passwords
            # For now, assuming controller validates non-empty password for new users.
            # If an empty password is to be disallowed universally, raise ValueError here.
            return
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
        # Store the hash as a string
        self.password_hash = hashed_password.decode("utf-8")

    def check_password(self, password: str) -> bool:
        """
        Checks the provided password against the stored hash.
        """
        if not self.password_hash or not password:
            return False
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
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
        return any(
            role.name.upper() == role_name.upper() for role in self.roles
        )  # Made case-insensitive for robustness

    def is_admin(self) -> bool:
        """
        Check if user has admin privileges.

        Returns:
            True if user is an admin, False otherwise
        """
        return self.has_role("ADMIN")  # Ensure "ADMIN" matches the actual role name

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
