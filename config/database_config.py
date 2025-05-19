# config/database_config.py

"""
EDSI Veterinary Management System - Database Configuration
Version: 1.1.4
Purpose: Manages database connections, sessions, and engine setup using SQLAlchemy.
         Ensures create_tables imports OwnerPayment and not a generic Payment.
Last Updated: May 18, 2025
Author: Claude Assistant

Changelog:
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
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session, Session as SQLAlchemySession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

from .app_config import get_database_url, AppConfig

db_logger = logging.getLogger("database_operations")

if not db_logger.hasHandlers():
    log_conf = AppConfig.get_logging_config()
    db_log_file = log_conf.get("db_log_file", "logs/edsi_db.log")
    log_dir_for_db = os.path.dirname(db_log_file)
    if not os.path.exists(log_dir_for_db):
        try:
            os.makedirs(log_dir_for_db, exist_ok=True)
        except OSError:
            pass
    pass

Base = declarative_base()


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
            # Ensure all models that need tables created are imported here.
            # 'Payment' (generic) has been removed. 'OwnerPayment' is the specific model.
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
                OwnerPayment,  # Use OwnerPayment here
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

            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Database tables created (if they didn't exist).")
        except Exception as e:
            self.logger.error(f"Error creating database tables: {e}", exc_info=True)
            raise


db_manager = DatabaseManager()
