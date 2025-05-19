# main.py

"""
EDSI Veterinary Management System - Main Application
Version: 1.3.3
Purpose: Main entry point for the EDSI application.
         Initializes the application, database, logging, and manages screen transitions.
         Corrected SQLAlchemy text execution.
Last Updated: May 18, 2025
Author: Claude Assistant

Changelog:
- v1.3.3 (2025-05-18):
    - Modified `initialize_database` to use `text('SELECT 1')` for SQLAlchemy execution
      to resolve ArgumentError.
    - Added `from sqlalchemy import text`.
- v1.3.2 (2025-05-18):
    - Corrected `setup_logging` to use the imported `LOG_DIR` constant from
      `config.app_config` instead of a non-existent `AppConfig.get_logs_dir()`.
- v1.3.1 (2025-05-16): (User's Base Version from previous interactions)
    - Initial setup for application class, splash screen, login, and screen navigation.
"""

import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional  # Added for type hinting

from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPalette, QColor
from sqlalchemy import text  # <--- Added import for text()

# Add project root to sys.path to allow importing project modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.database_config import db_manager
from config.app_config import (
    AppConfig,
    LOG_DIR,
    APP_LOG_FILE,
    LOGGING_LEVEL,
    APP_NAME,
    APP_VERSION,
    DATABASE_URL,
)

# Import screens after path setup
from views.auth.splash_screen import SplashScreen
from views.auth.small_login_dialog import SmallLoginDialog
from views.horse.horse_unified_management import HorseUnifiedManagement
from views.admin.user_management_screen import UserManagementScreen


class EDSIApplication(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.current_user_id: Optional[str] = None
        self.splash_screen: Optional[SplashScreen] = None
        self.login_dialog: Optional[SmallLoginDialog] = None
        self.horse_management_screen: Optional[HorseUnifiedManagement] = None
        self.user_management_screen: Optional[UserManagementScreen] = None

        self.setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

        self.db_manager = db_manager
        self.initialize_database()

        self.setApplicationName(APP_NAME)
        self.setApplicationVersion(APP_VERSION)
        self.setOrganizationName("EDSI")

        self.show_splash_screen()

    def setup_logging(self):
        """Configures logging for the application."""
        log_directory = LOG_DIR
        app_log_file = APP_LOG_FILE
        log_level_str = os.environ.get("LOG_LEVEL", logging.getLevelName(LOGGING_LEVEL))
        log_level = getattr(logging, log_level_str.upper(), LOGGING_LEVEL)

        if not os.path.exists(log_directory):
            try:
                os.makedirs(log_directory)
            except OSError as e:
                print(
                    f"Error creating log directory {log_directory}: {e}. Logging to console.",
                    file=sys.stderr,
                )
                logging.basicConfig(
                    level=log_level,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)],
                )
                return

        file_handler = RotatingFileHandler(
            app_log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        console_handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        logging.info("Logging configured.")

    def initialize_database(self):
        self.logger.info("Initializing database...")
        try:
            # DATABASE_URL is imported from app_config
            self.db_manager.initialize_database(DATABASE_URL)
            session = self.db_manager.get_session()
            # --- MODIFIED LINE ---
            session.execute(text("SELECT 1"))  # Wrap raw SQL in text()
            # --- END MODIFICATION ---
            session.close()
            self.logger.info("Database initialized successfully.")
        except Exception as e:
            self.logger.critical(f"Failed to initialize database: {e}", exc_info=True)
            QMessageBox.critical(
                None,
                "Database Error",
                f"Could not connect to or initialize the database: {e}\nApplication will exit.",
            )
            sys.exit(1)

    def show_splash_screen(self):
        self.close_all_screens()
        self.splash_screen = SplashScreen()
        self.splash_screen.login_requested.connect(self.show_login_dialog)
        self.splash_screen.exit_requested.connect(self.quit)
        self.splash_screen.show()

    def show_login_dialog(self):
        self.logger.info("Login area clicked on splash screen.")
        if self.login_dialog and self.login_dialog.isVisible():
            self.login_dialog.raise_()
            self.login_dialog.activateWindow()
            return

        self.login_dialog = SmallLoginDialog(parent=self.splash_screen)
        self.login_dialog.login_successful.connect(self.handle_login_success)
        self.login_dialog.exec()

    def handle_login_success(self, user_id: str):
        self.current_user_id = user_id
        self.logger.info(f"User '{user_id}' logged in successfully.")
        if self.login_dialog:
            self.login_dialog.accept()
            self.login_dialog = None
        if self.splash_screen:
            self.splash_screen.close()
            self.splash_screen = None
        self.show_horse_management_screen()

    def show_horse_management_screen(self):
        self.close_all_screens()
        if not self.current_user_id:
            self.logger.warning(
                "Attempted to show horse management screen without a logged-in user."
            )
            self.show_splash_screen()
            return

        self.horse_management_screen = HorseUnifiedManagement(
            current_user=self.current_user_id
        )
        self.horse_management_screen.exit_requested.connect(self.handle_logout)
        self.horse_management_screen.setup_requested.connect(
            self.show_user_management_screen
        )
        self.horse_management_screen.show()
        self.logger.info("Horse Management Screen displayed.")

    def show_user_management_screen(self):
        self.close_all_screens()
        if not self.current_user_id:
            self.logger.warning(
                "Attempted to show user management screen without a logged-in user."
            )
            self.show_splash_screen()
            return

        self.user_management_screen = UserManagementScreen(
            current_user_id=self.current_user_id
        )
        self.user_management_screen.exit_requested.connect(
            self.handle_logout_from_admin
        )
        self.user_management_screen.horse_management_requested.connect(
            self.show_horse_management_screen
        )
        self.user_management_screen.show()
        self.logger.info("User Management Screen displayed.")

    def handle_logout(self):
        self.logger.info(
            f"User '{self.current_user_id}' logging out from Horse Management."
        )
        self.current_user_id = None
        self.show_splash_screen()

    def handle_logout_from_admin(self):
        self.logger.info(
            f"User '{self.current_user_id}' logging out from Admin Screen."
        )
        self.current_user_id = None
        self.show_splash_screen()

    def close_all_screens(self):
        """Closes all main application screens before switching."""
        if self.login_dialog and self.login_dialog.isVisible():
            self.login_dialog.reject()
            self.login_dialog = None
        if self.horse_management_screen:
            self.horse_management_screen.close()
            self.horse_management_screen = None
        if self.user_management_screen:
            self.user_management_screen.close()
            self.user_management_screen = None
        # Splash screen handling is managed by show_splash_screen or handle_login_success

    def run(self):
        """Starts the Qt application event loop."""
        self.logger.info(f"{APP_NAME} event loop started.")
        return self.exec()


def main():
    """Main function to create and run the application."""
    app_instance = EDSIApplication()
    sys.exit(app_instance.run())


if __name__ == "__main__":
    main()
