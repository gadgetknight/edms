# config/database_config.py

"""
EDSI Veterinary Management System - Database Manager Configuration
Version: 1.0.2
Purpose: Manages database connection, session creation, and initial setup.
Last Updated: May 12, 2025
Author: Claude Assistant

Changelog:
- v1.0.2 (2025-05-12): Store lowercase hash for default password.
  - Modified _create_default_user to hash the lowercase version of the
    default password ('admin1234') to support case-insensitive password checks.
- v1.0.1 (2025-05-12): Updated default admin password
  - Changed default password to 'admin1234' as requested.
  - Ensured password hashing uses SHA-256.
- v1.0.0 (2025-05-12): Initial implementation
"""

import os
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base  # Base needs to be imported for metadata creation
from config.app_config import AppConfig  # Import AppConfig for database path
from models.user_models import User


class DatabaseManager:
    """Manages database connection and session creation"""

    def __init__(self, db_path=None):
        """
        Initializes the DatabaseManager.

        Args:
            db_path (str, optional): Path to the database file.
                                     If None, uses the path from AppConfig.
                                     Defaults to None.
        """
        if db_path is None:
            db_path = AppConfig.get_database_path()

        self.database_url = f"sqlite:///{db_path}"
        self.engine = None
        self.session_factory = None
        self.Session = None
        print(f"Database URL set to: {self.database_url}")  # Debug print

    def initialize_database(self):
        """Initialize database connection and create tables"""
        print(f"Initializing database at: {self.database_url}")  # Debug print
        self.engine = create_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},
        )

        Base.metadata.create_all(self.engine)
        print("Database tables created (if they didn't exist).")  # Debug print

        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        print("Database session factory created.")  # Debug print

        self._create_default_user()

    def get_session(self):
        """Get a new database session"""
        if not self.Session:
            raise RuntimeError(
                "Database not initialized. Call initialize_database() first."
            )
        return self.Session()

    def close_session(self):
        """Close the current session"""
        if self.Session:
            self.Session.remove()

    def _create_default_user(self):
        """Create default admin user if none exists, storing lowercase password hash."""
        if not self.Session:
            print("Cannot create default user: Session is not initialized.")
            return

        session = self.get_session()
        try:
            user_count = session.query(User).count()
            print(f"Checking for existing users... Found: {user_count}")  # Debug print
            if user_count == 0:
                print("No users found. Creating default ADMIN user...")  # Debug print
                default_username = "ADMIN"
                default_password = "admin1234"  # Base password
                # --- CHANGE: Convert to lowercase before hashing ---
                password_to_hash = default_password.lower()
                password_hash = hashlib.sha256(
                    password_to_hash.encode("utf-8")
                ).hexdigest()
                # --- END CHANGE ---
                print(
                    f"Password hash generated for default user (from lowercase)."
                )  # Debug print

                admin_user = User(
                    user_id=default_username,
                    password_hash=password_hash,
                    user_name="System Administrator",
                    is_active=True,
                )
                session.add(admin_user)
                session.commit()
                print(
                    f"Created default admin user ({default_username}/{default_password})"
                )
            else:
                # --- Optional: Check if existing ADMIN user has the old hash and update it ---
                admin_user = session.query(User).filter(User.user_id == "ADMIN").first()
                if admin_user:
                    # Generate the expected lowercase hash
                    expected_hash = hashlib.sha256(
                        "admin1234".lower().encode("utf-8")
                    ).hexdigest()
                    if admin_user.password_hash != expected_hash:
                        print(
                            "Updating existing ADMIN user password hash to lowercase version..."
                        )
                        admin_user.password_hash = expected_hash
                        session.commit()
                        print("ADMIN user password hash updated.")
                    else:
                        print(
                            "ADMIN user already has the correct lowercase password hash."
                        )

                print(
                    "Default user check: Users already exist in the database."
                )  # Debug print
        except Exception as e:
            session.rollback()
            print(
                f"Error during default user check/creation: {e}"
            )  # Use print for critical startup errors
        finally:
            self.close_session()

    def close(self):
        """Close database connection pool"""
        if self.engine:
            self.engine.dispose()
            print("Database connection pool disposed.")  # Debug print


# Global database manager instance
db_manager = DatabaseManager()
