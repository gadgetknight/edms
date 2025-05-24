# config/database_config.py

"""
EDSI Veterinary Management System - Database Configuration
Version: 2.0.0
Purpose: Simplified database connection and session management using SQLAlchemy.
         Removed over-engineered complexity and focused on stable database operations.
Last Updated: May 24, 2025
Author: Claude Assistant

Changelog:
- v2.0.0 (2025-05-24):
    - Complete rewrite for Phase 1 (Chunk 1) simplification
    - Removed complex Base import issues by using local declarative_base
    - Simplified DatabaseManager class with clear responsibility
    - Removed circular import problems
    - Streamlined table creation process
    - Clean session management with proper context handling
    - Removed unnecessary model imports from create_tables
    - Focused on stable, working database initialization
    - Added proper error handling without over-engineering
    - Simple logging without excessive detail
"""

import logging
import os
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, Session as SQLAlchemySession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

from config.app_config import AppConfig

# Create Base for all models
Base = declarative_base()

# Setup logger
db_logger = logging.getLogger("database_operations")


class DatabaseManager:
    """
    Simplified database manager for EDSI application.
    Handles database initialization, session creation, and table management.
    """

    def __init__(self):
        self.engine = None
        self.SessionLocal: Optional[scoped_session[SQLAlchemySession]] = None
        self.db_url: Optional[str] = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def initialize_database(self, db_url: Optional[str] = None) -> None:
        """
        Initialize database connection and create tables.

        Args:
            db_url: Database URL (optional, uses config default if not provided)
        """
        if self.engine:
            self.logger.info("Database already initialized")
            return

        # Set database URL
        self.db_url = db_url or AppConfig.get_database_url()
        if not self.db_url:
            raise ValueError("DATABASE_URL is not configured")

        self.logger.info(f"Initializing database: {self.db_url}")

        try:
            # Create engine
            self.engine = create_engine(
                self.db_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,  # Verify connections before use
            )

            # Create session factory
            self.SessionLocal = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            )

            self.logger.info("Database engine and session factory created")

            # Create tables
            self.create_tables()

            # Test connection
            self._test_connection()

            # Ensure default admin user always exists
            self._ensure_default_admin_user()

            self.logger.info("Database initialization completed successfully")

        except SQLAlchemyError as e:
            self.logger.error(f"SQLAlchemy error during database initialization: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during database initialization: {e}")
            raise

    def get_session(self) -> SQLAlchemySession:
        """
        Get a database session.

        Returns:
            SQLAlchemy session instance

        Raises:
            RuntimeError: If database is not initialized
        """
        if not self.SessionLocal:
            raise RuntimeError(
                "Database not initialized. Call initialize_database() first."
            )

        return self.SessionLocal()

    def create_tables(self) -> None:
        """
        Create all database tables.

        Raises:
            RuntimeError: If engine is not initialized
        """
        if not self.engine:
            raise RuntimeError("Database engine not initialized")

        try:
            self.logger.info("Creating database tables...")

            # Import models to register them with Base
            # This ensures all model classes are loaded before table creation
            self._import_models()

            # Create all tables
            Base.metadata.create_all(bind=self.engine)

            # Log created tables
            table_names = list(Base.metadata.tables.keys())
            self.logger.info(f"Database tables created: {table_names}")

        except Exception as e:
            self.logger.error(f"Error creating database tables: {e}")
            raise

    def _import_models(self) -> None:
        """
        Import all model classes to ensure they are registered with Base.
        This is called before table creation to ensure all tables are created.
        """
        try:
            # Import essential models for Phase 1
            from models.user_models import User, Role, UserRole
            from models.base_model import BaseModel

            self.logger.debug("Essential models imported for table creation")

            # Additional models can be imported here as needed in future phases
            # from models.horse_models import Horse, HorseOwner, HorseLocation
            # from models.owner_models import Owner, OwnerBillingHistory, OwnerPayment
            # from models.reference_models import Species, StateProvince, Location, etc.

        except ImportError as e:
            self.logger.warning(f"Could not import some models: {e}")
            # Don't raise here - some models might not exist yet in Phase 1

    def _test_connection(self) -> None:
        """
        Test database connection.

        Raises:
            Exception: If connection test fails
        """
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            self.logger.info("Database connection test successful")
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            raise

    def _ensure_default_admin_user(self) -> None:
        """
        Ensure default admin user always exists with correct credentials.
        This creates or updates the ADMIN user to ship with the product.

        Default credentials:
        - Username: ADMIN (case insensitive)
        - Password: admin1234 (case sensitive)
        - Role: admin
        """
        try:
            with self.get_session() as session:
                # Import here to avoid circular imports
                from models.user_models import User, Role, UserRole
                import hashlib

                self.logger.info(
                    "Ensuring default ADMIN user exists with correct credentials"
                )

                # Ensure admin role exists
                admin_role = session.query(Role).filter(Role.name == "admin").first()
                if not admin_role:
                    admin_role = Role(
                        name="admin",
                        description="System Administrator",
                        created_by="SYSTEM",
                        modified_by="SYSTEM",
                    )
                    session.add(admin_role)
                    session.flush()  # Get the role_id
                    self.logger.info("Created admin role")

                # Calculate correct password hash
                correct_password_hash = hashlib.sha256("admin1234".encode()).hexdigest()

                # Check if ADMIN user exists
                admin_user = session.query(User).filter(User.user_id == "ADMIN").first()

                if admin_user:
                    # Update existing ADMIN user to ensure correct credentials
                    updated = False
                    if admin_user.password_hash != correct_password_hash:
                        admin_user.password_hash = correct_password_hash
                        updated = True
                        self.logger.info("Updated ADMIN user password hash")

                    if not admin_user.is_active:
                        admin_user.is_active = True
                        updated = True
                        self.logger.info("Activated ADMIN user")

                    if not admin_user.user_name:
                        admin_user.user_name = "System Administrator"
                        updated = True

                    if updated:
                        admin_user.modified_by = "SYSTEM"
                        self.logger.info(
                            "Updated existing ADMIN user with correct credentials"
                        )
                    else:
                        self.logger.info("ADMIN user already has correct credentials")

                else:
                    # Create new ADMIN user
                    admin_user = User(
                        user_id="ADMIN",
                        password_hash=correct_password_hash,
                        user_name="System Administrator",
                        email="admin@edsi.local",
                        is_active=True,
                        created_by="SYSTEM",
                        modified_by="SYSTEM",
                    )
                    session.add(admin_user)
                    session.flush()  # Ensure user is created and has ID
                    self.logger.info("Created new ADMIN user")

                # Ensure ADMIN user has admin role
                existing_role_link = (
                    session.query(UserRole)
                    .filter(
                        UserRole.user_id == "ADMIN",
                        UserRole.role_id == admin_role.role_id,
                    )
                    .first()
                )

                if not existing_role_link:
                    user_role = UserRole(user_id="ADMIN", role_id=admin_role.role_id)
                    session.add(user_role)
                    self.logger.info("Linked ADMIN user to admin role")

                # Commit all changes
                session.commit()

                self.logger.info(
                    "Default ADMIN user ready (Username: ADMIN, Password: admin1234)"
                )

        except Exception as e:
            self.logger.error(f"Error ensuring default admin user: {e}", exc_info=True)
            # Don't raise here - let the application continue

    def close(self) -> None:
        """
        Close database connections and clean up resources.
        """
        if self.SessionLocal:
            self.SessionLocal.remove()
            self.logger.info("Database sessions closed")

        if self.engine:
            self.engine.dispose()
            self.logger.info("Database engine disposed")

    def get_engine(self):
        """
        Get the database engine.

        Returns:
            SQLAlchemy engine instance
        """
        return self.engine


# Global database manager instance
db_manager = DatabaseManager()


def get_db_session() -> SQLAlchemySession:
    """
    Convenience function to get a database session.

    Returns:
        SQLAlchemy session instance
    """
    return db_manager.get_session()


def init_database(db_url: Optional[str] = None) -> None:
    """
    Convenience function to initialize the database.

    Args:
        db_url: Database URL (optional)
    """
    db_manager.initialize_database(db_url)
