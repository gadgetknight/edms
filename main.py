# main.py

"""
EDSI Veterinary Management System - Main Application Entry Point
Version: 1.2.0
Purpose: Manages application lifecycle, authentication flow, and navigation
         between Horse Management and User Management screens using PySide6.
Last Updated: May 13, 2025
Author: Claude Assistant

Changelog:
- v1.2.0 (2025-05-13): Integrated UserManagementScreen.
  - Added import for UserManagementScreen.
  - Added `user_management_screen` attribute to EDSIApplication.
  - Implemented `show_user_management_screen` to display the new screen
    and hide the horse management screen.
  - Implemented `on_user_management_exit` to handle returning from
    user management to horse management.
  - Connected `HorseUnifiedManagement.setup_requested` signal to
    `show_user_management_screen`.
- v1.1.0 (2025-05-12): Refactored for new auth flow and PySide6
- v1.0.2 (2025-05-12): Integrated Unified Horse Management (PyQt6)
- v1.0.1 (2025-05-12): Added Horse Management functionality (PyQt6)
- v1.0.0 (2025-05-12): Initial implementation (PyQt6)
"""

import sys
import logging
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer  # QTimer might not be used directly here anymore

from config.database_config import db_manager
from config.app_config import AppConfig
from views.auth.login_screen import LoginScreen
from views.horse.horse_unified_management import HorseUnifiedManagement
from views.admin.user_management_screen import UserManagementScreen  # New import
from models import *


class EDSIApplication:
    """Main application class managing the application flow and windows."""

    def __init__(self):
        """Initializes the application."""
        self.setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)

        self.app = QApplication(sys.argv)
        self.app.setApplicationName(AppConfig.APP_NAME)
        self.app.setApplicationVersion(AppConfig.APP_VERSION)
        self.logger.info(f"Starting {AppConfig.APP_NAME} v{AppConfig.APP_VERSION}")

        self.initialize_database()

        self.current_user = None

        # Application windows
        self.login_screen = None
        self.horse_management_screen = None
        self.user_management_screen = None  # New screen reference

    def setup_logging(self):
        """Configure application-wide logging."""
        logs_dir = AppConfig.get_logs_dir()
        log_file = os.path.join(logs_dir, "edsi_app.log")
        print(f"Logging to: {log_file}")

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, mode="a"),
                logging.StreamHandler(sys.stdout),
            ],
        )
        # Re-assign logger for this class after basicConfig is set
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Logging configured.")

    def initialize_database(self):
        """Initialize the database connection and create tables if necessary."""
        try:
            self.logger.info("Initializing database...")
            db_manager.initialize_database()
            self.logger.info("Database initialized successfully.")
        except Exception as e:
            self.logger.error(
                f"Fatal Error: Failed to initialize database: {e}", exc_info=True
            )
            # Consider a QMessageBox here for user feedback before exiting
            if QApplication.instance():
                QApplication.instance().quit()
            else:  # If QApplication not yet fully up
                sys.exit(1)

    def run(self):
        """Start the application execution."""
        self.logger.info("Running EDSI Application...")
        self.show_login_screen()
        sys.exit(self.app.exec())

    def show_login_screen(self):
        """Display the login screen."""
        self.logger.debug("Showing Login Screen.")
        if self.login_screen:
            self.login_screen.deleteLater()

        self.login_screen = LoginScreen()
        self.login_screen.login_successful.connect(self.on_login_successful)
        self.login_screen.exit_requested.connect(self.cleanup_and_exit)
        self.login_screen.show()

    def on_login_successful(self, user_id):
        """Handle successful user login."""
        self.current_user = user_id
        self.logger.info(f"User '{self.current_user}' logged in successfully.")

        if self.login_screen:
            self.login_screen.close()
            self.login_screen.deleteLater()
            self.login_screen = None
        self.show_horse_management()

    def show_horse_management(self):
        """Display the main Horse Unified Management screen."""
        if not self.current_user:
            self.logger.error("Cannot show horse management screen: No user logged in.")
            self.show_login_screen()
            return

        self.logger.debug(
            f"Showing Horse Management Screen for user '{self.current_user}'."
        )
        if self.horse_management_screen:
            self.horse_management_screen.deleteLater()

        self.horse_management_screen = HorseUnifiedManagement(
            current_user=self.current_user
        )
        self.horse_management_screen.exit_requested.connect(
            self.on_horse_management_exit
        )
        # Connect the new signal for setup screen
        self.horse_management_screen.setup_requested.connect(
            self.show_user_management_screen
        )
        self.horse_management_screen.show()
        self.logger.info("Horse Management Screen displayed.")

    def on_horse_management_exit(self):
        """Handle the user exiting the Horse Management screen (logoff)."""
        self.logger.info("Exit requested from Horse Management screen (logoff).")
        if self.horse_management_screen:
            self.horse_management_screen.close()
            self.horse_management_screen.deleteLater()
            self.horse_management_screen = None
        self.current_user = None
        self.logger.info("User logged off.")
        self.show_login_screen()

    def show_user_management_screen(self):
        """Hide Horse Management and show User Management screen."""
        if not self.current_user:
            self.logger.error("Cannot show user management: No admin user context.")
            # Optionally, redirect to login or show error
            return

        self.logger.info(
            f"Showing User Management Screen for admin '{self.current_user}'."
        )
        if self.horse_management_screen:
            self.horse_management_screen.hide()

        if self.user_management_screen:  # Clean up old instance if any
            self.user_management_screen.deleteLater()

        self.user_management_screen = UserManagementScreen(
            current_admin_user=self.current_user
        )
        self.user_management_screen.exit_requested.connect(self.on_user_management_exit)
        self.user_management_screen.show()

    def on_user_management_exit(self):
        """Handle exiting the User Management screen."""
        self.logger.info("Exiting User Management Screen.")
        if self.user_management_screen:
            self.user_management_screen.close()
            self.user_management_screen.deleteLater()
            self.user_management_screen = None

        if self.horse_management_screen:
            self.horse_management_screen.show()  # Show horse management again
            self.logger.info("Returned to Horse Management Screen.")
        else:
            # Should not happen if flow is correct, but as a fallback:
            self.logger.warning(
                "Horse management screen not found after exiting user management. Logging off."
            )
            self.on_horse_management_exit()

    def cleanup_and_exit(self):
        """Perform cleanup and exit the application."""
        self.logger.info("Initiating application cleanup and exit.")
        try:
            db_manager.close()
            self.logger.info("Database connection closed.")
        except Exception as e:
            self.logger.error(f"Error closing database connection: {e}", exc_info=True)

        # Close windows if they exist
        if self.user_management_screen:
            self.user_management_screen.close()
        if self.horse_management_screen:
            self.horse_management_screen.close()
        if self.login_screen:
            self.login_screen.close()

        self.logger.info("Exiting application.")
        if QApplication.instance():
            QApplication.instance().quit()
        else:
            sys.exit(0)


def main():
    """Main entry point function."""
    app_instance = EDSIApplication()
    app_instance.run()


if __name__ == "__main__":
    main()
