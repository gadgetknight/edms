# config/database_config.py

"""
EDSI Veterinary Management System - Database Configuration
Version: 2.0.3 (Example version, update as needed)
Purpose: Simplified database connection and session management using SQLAlchemy.
         Ensures ADMIN user password is set using bcrypt via User.set_password(),
         with robust handling for pre-existing non-bcrypt hashes.
         Added new financial models to _import_models.
Last Updated: June 4, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v2.0.3 (2025-06-04):
    - Added Transaction and Invoice from financial_models to _import_models method
      to ensure their tables are created by Base.metadata.create_all.
- v2.0.2 (2025-05-29):
    - Made _ensure_default_admin_user method more robust:
        - It now tries to check the ADMIN password using bcrypt.
        - If check_password fails (returns False or raises ValueError due to
          invalid hash format like old SHA256), it then calls
          user.set_password() to ensure the password becomes "admin1234"
          hashed with bcrypt.
        - This resolves the "ValueError: Invalid salt" during startup.
- v2.0.1 (2025-05-29):
    - Modified _ensure_default_admin_user method to use user.set_password()
      (which uses bcrypt) for the ADMIN user's password ("admin1234")
      instead of directly setting a SHA-256 hash.
    - Removed hashlib import as it's no longer used.
- v2.0.0 (2025-05-24):
    - Complete rewrite for Phase 1 (Chunk 1) simplification.
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
        """
        if self.engine:
            self.logger.info("Database already initialized")
            return

        self.db_url = db_url or AppConfig.get_database_url()
        if not self.db_url:
            raise ValueError("DATABASE_URL is not configured")

        self.logger.info(f"Initializing database: {self.db_url}")

        try:
            self.engine = create_engine(
                self.db_url,
                echo=False,  # Set to True for SQL logging, False for production
                pool_pre_ping=True,
            )

            self.SessionLocal = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            )

            self.logger.info("Database engine and session factory created")
            self.create_tables()
            self._test_connection()
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
        """
        if not self.SessionLocal:
            raise RuntimeError(
                "Database not initialized. Call initialize_database() first."
            )
        return self.SessionLocal()

    def create_tables(self) -> None:
        """
        Create all database tables.
        """
        if not self.engine:
            raise RuntimeError("Database engine not initialized")

        try:
            self.logger.info("Creating database tables...")
            self._import_models()  # This ensures all models are known to Base
            Base.metadata.create_all(bind=self.engine)
            table_names = list(Base.metadata.tables.keys())
            self.logger.info(f"Database tables created/verified: {table_names}")

        except Exception as e:
            self.logger.error(f"Error creating database tables: {e}")
            raise

    def _import_models(self) -> None:
        """
        Import all model classes to ensure they are registered with Base.
        This is crucial for Base.metadata.create_all() to work correctly.
        """
        try:
            from models.base_model import BaseModel  # Already imported by other models
            from models.user_models import User, Role, UserRole
            from models.horse_models import Horse, HorseOwner, HorseLocation
            from models.owner_models import Owner, OwnerBillingHistory, OwnerPayment

            # The placeholder Invoice from owner_models is implicitly imported if not removed from its __init__ or owner_models.py
            from models.reference_models import (
                StateProvince,
                ChargeCodeCategory,
                ChargeCode,
                Veterinarian,
                Location,
                Procedure,  # Placeholder
                Drug,  # Placeholder
                TreatmentLog,  # Placeholder
                CommunicationLog,  # Placeholder
                Document,  # Placeholder
                Reminder,  # Placeholder
                Appointment,  # Placeholder
                # The placeholder Transaction & TransactionDetail from reference_models might also be imported
                # if not removed from its __init__ or reference_models.py
            )

            # Import new financial models
            from models.financial_models import Transaction, Invoice

            self.logger.debug(
                "Models imported for table creation, including new financial models."
            )
        except ImportError as e:
            self.logger.error(
                f"Critical error: Could not import core models for table creation: {e}",
                exc_info=True,
            )
            # Depending on severity, you might want to raise this error
            # raise ImportError(f"Failed to import essential models: {e}") from e
        except Exception as e:
            self.logger.error(
                f"Unexpected error during model imports for table creation: {e}",
                exc_info=True,
            )

    def _test_connection(self) -> None:
        """
        Test database connection.
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
        Ensure default admin user always exists with correct credentials
        (password hashed using bcrypt via User.set_password).
        Handles pre-existing non-bcrypt hashes for ADMIN by resetting the password.
        """
        try:
            with self.get_session() as session:
                from models.user_models import (
                    User,
                    Role,
                )

                self.logger.info(
                    "Ensuring default ADMIN user exists with bcrypt password."
                )

                admin_role_name = "ADMIN"
                admin_role = (
                    session.query(Role).filter(Role.name == admin_role_name).first()
                )
                if not admin_role:
                    self.logger.warning(
                        f"Role '{admin_role_name}' not found. Creating it now. "
                        "It's recommended to run add_initial_data.py for full role setup."
                    )
                    admin_role = Role(
                        name=admin_role_name,
                        description="System Administrator (auto-created by db_config)",
                        created_by="SYSTEM_DB_CONFIG",
                        modified_by="SYSTEM_DB_CONFIG",
                    )
                    session.add(admin_role)
                    session.flush()
                    self.logger.info(f"Created '{admin_role_name}' role.")

                admin_user = session.query(User).filter(User.user_id == "ADMIN").first()
                default_password = "admin1234"
                admin_default_name = "System Administrator"
                admin_default_email = "admin@edsi.local"

                if admin_user:
                    password_reset_done = False
                    attributes_updated = False

                    try:
                        if not admin_user.check_password(default_password):
                            self.logger.info(
                                "ADMIN user password check failed. Resetting."
                            )
                            admin_user.set_password(default_password)
                            password_reset_done = True
                    except ValueError as e:
                        self.logger.warning(
                            f"ADMIN password hash not bcrypt/valid ({e}). Resetting password."
                        )
                        admin_user.set_password(default_password)
                        password_reset_done = True

                    if password_reset_done:
                        admin_user.modified_by = "SYSTEM_DB_CONFIG_PWD"
                        self.logger.info(
                            "ADMIN user password has been set/reset to a bcrypt hash."
                        )

                    if not admin_user.is_active:
                        admin_user.is_active = True
                        self.logger.info("Activated ADMIN user.")
                        attributes_updated = True

                    if admin_user.user_name != admin_default_name:
                        admin_user.user_name = admin_default_name
                        self.logger.info(
                            f"Set ADMIN user_name to '{admin_default_name}'."
                        )
                        attributes_updated = True

                    if admin_user.email != admin_default_email:
                        admin_user.email = admin_default_email
                        self.logger.info(f"Set ADMIN email to '{admin_default_email}'.")
                        attributes_updated = True

                    if attributes_updated and not password_reset_done:
                        admin_user.modified_by = "SYSTEM_DB_CONFIG_ATTR"

                    if password_reset_done or attributes_updated:
                        self.logger.info("ADMIN user record updated/verified.")
                    else:
                        self.logger.info(
                            "ADMIN user credentials, status, and name are correct."
                        )

                else:
                    self.logger.info("ADMIN user not found. Creating new ADMIN user...")
                    admin_user = User(
                        user_id="ADMIN",
                        user_name=admin_default_name,
                        email=admin_default_email,
                        is_active=True,
                        created_by="SYSTEM_DB_CONFIG",
                        modified_by="SYSTEM_DB_CONFIG",
                    )
                    admin_user.set_password(default_password)
                    session.add(admin_user)
                    session.flush()
                    self.logger.info("Created new ADMIN user with bcrypt password.")

                if admin_role and admin_role not in admin_user.roles:
                    admin_user.roles.append(admin_role)
                    self.logger.info("Linked ADMIN user to ADMIN role.")
                elif not admin_role:
                    self.logger.error(
                        f"Cannot link ADMIN user to '{admin_role_name}' role as role object is missing."
                    )

                session.commit()
                self.logger.info(
                    f"Default ADMIN user ready (Username: ADMIN, Password: {default_password})"
                )

        except Exception as e:
            self.logger.error(f"Error ensuring default admin user: {e}", exc_info=True)
            if "session" in locals() and session.is_active:
                session.rollback()

    def close(self) -> None:
        if self.SessionLocal:
            self.SessionLocal.remove()
            self.logger.info("Database sessions closed")
        if self.engine:
            self.engine.dispose()
            self.logger.info("Database engine disposed")

    def get_engine(self):
        return self.engine


db_manager = DatabaseManager()


def get_db_session() -> SQLAlchemySession:
    return db_manager.get_session()


def init_database(db_url: Optional[str] = None) -> None:
    db_manager.initialize_database(db_url)
