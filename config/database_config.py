# config/database_config.py

"""
EDSI Veterinary Management System - Database Configuration
Version: 1.1.6
Purpose: Manages database connections, sessions, and engine setup using SQLAlchemy.
         Corrects Base usage to ensure models are registered before table creation.
Last Updated: May 18, 2025
Author: Claude Assistant

Changelog:
- v1.1.6 (2025-05-18):
    - Removed local `Base = declarative_base()` and imported the shared `Base`
      from `models.base_model` to ensure all models are registered with the
      correct metadata before `create_all()` is called.
- v1.1.5 (2025-05-18):
    - Added logging in `create_tables` to list tables known by Base.metadata
      before and after the `create_all()` call for debugging.
- v1.1.4 (2025-05-18):
    - Ensured 'OwnerPayment' is imported in `create_tables` and generic 'Payment' is not.
- v1.1.3 (2025-05-18):
    - (Previous attempt to fix payment import)
- v1.1.2 (2025-05-18):
    - Added `from typing import Optional` to resolve NameError.
- v1.1.1 (2025-05-17):
    - Modified DatabaseManager to use `get_database_url()` from `config.app_config`.
"""

import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session as SQLAlchemySession

# REMOVED: from sqlalchemy.ext.declarative import declarative_base # No longer defining a local Base
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

from .app_config import get_database_url  # AppConfig class is not directly used here

# IMPORT THE CORRECT BASE FROM YOUR MODELS PACKAGE
# This is the Base instance that all your models are registered with.
from models.base_model import Base

db_logger = logging.getLogger("database_operations")

# Basic setup for db_logger if not configured by main app's logging yet
if not db_logger.hasHandlers():
    log_conf_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    if not os.path.exists(log_conf_dir):
        try:
            os.makedirs(log_conf_dir, exist_ok=True)
        except OSError:
            pass
    pass

# Base = declarative_base() # <<<--- CRITICAL: THIS LINE WAS REMOVED


class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal: Optional[scoped_session[SQLAlchemySession]] = None
        self.db_url: Optional[str] = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def initialize_database(self, db_url: Optional[str] = None):
        if self.engine:
            self.logger.info("Database already initialized.")
            return
        if db_url is None:
            self.db_url = get_database_url()
        else:
            self.db_url = db_url
        if not self.db_url:
            self.logger.error(
                "DATABASE_URL is not configured. Cannot initialize database."
            )
            raise ValueError("DATABASE_URL is not configured.")
        self.logger.info(f"Initializing database with URL: {self.db_url}")
        try:
            self.engine = create_engine(self.db_url, echo=False)
            self.SessionLocal = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            )
            self.logger.info(
                "Database engine and session factory created successfully."
            )
            # The import of models within create_tables will populate the shared Base.metadata
            self.create_tables()
        except SQLAlchemyError as e:
            self.logger.error(
                f"SQLAlchemyError during database initialization: {e}", exc_info=True
            )
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error during database initialization: {e}", exc_info=True
            )
            raise

    def get_session(self) -> SQLAlchemySession:
        if not self.SessionLocal:
            self.logger.error(
                "SessionLocal not initialized. Call initialize_database() first."
            )
            raise RuntimeError(
                "Database not initialized. Call initialize_database() first."
            )
        return self.SessionLocal()

    def create_tables(self):
        if not self.engine:
            self.logger.error("Engine not initialized. Cannot create tables.")
            raise RuntimeError("Database engine not initialized.")
        try:
            # This import is crucial. It ensures that all your model files are parsed,
            # their classes defined (inheriting from the correct Base in models.base_model),
            # and thus registered with that Base's metadata.
            from models import (
                User,
                Role,
                UserRole,
                Horse,
                Owner,
                HorseOwner,
                Location,
                Transaction,
                TransactionDetail,
                ChargeCode,
                OwnerPayment,
                Invoice,
                Procedure,
                Drug,
                TreatmentLog,
                CommunicationLog,
                Document,
                Reminder,
                Appointment,
                StateProvince,
                Species,
                SystemConfig,
                HorseLocation,
                HorseBilling,
                OwnerBillingHistory,
            )

            # Now, Base.metadata (referring to the Base from models.base_model)
            # should be populated with your tables.
            self.logger.info(
                f"Models known by Base.metadata before create_all: {list(Base.metadata.tables.keys())}"
            )

            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Database tables created (if they didn't exist).")

            self.logger.info(
                f"Models known by Base.metadata after create_all: {list(Base.metadata.tables.keys())}"
            )

        except Exception as e:
            self.logger.error(f"Error creating database tables: {e}", exc_info=True)
            raise


db_manager = DatabaseManager()
