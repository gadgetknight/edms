# main.py

"""
EDSI Veterinary Management System - Main Application Entry Point
Version: 1.3.1
Purpose: Manages application lifecycle, new interactive splash screen,
         small login dialog, and navigation. Corrects QDialog import
         and splash screen visibility during login.
Last Updated: May 16, 2025
Author: Claude Assistant

Changelog:
- v1.3.1 (2025-05-16):
  - Added QDialog to PySide6.QtWidgets imports.
  - Modified splash screen behavior: it now stays visible behind the SmallLoginDialog.
    - Removed splash_screen.hide() from on_splash_login_clicked.
    - Simplified on_small_login_rejected to exit if login is aborted.
- v1.3.0 (2025-05-16): Implemented new splash screen and small login dialog flow.
- v1.2.0 (2025-05-13): Integrated UserManagementScreen.
- v1.1.0 (2025-05-12): Refactored for new auth flow and PySide6
"""

import sys
import logging
import os
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog  # Added QDialog

# from PySide6.QtCore import QTimer # No longer directly used here

from config.database_config import db_manager
from config.app_config import AppConfig
from views.auth.splash_screen import SplashScreen
from views.auth.small_login_dialog import SmallLoginDialog
from views.horse.horse_unified_management import HorseUnifiedManagement
from views.admin.user_management_screen import UserManagementScreen
from models import *


class EDSIApplication:
    """Main application class managing the application flow and windows."""

    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)

        self.app = QApplication(sys.argv)
        self.app.setApplicationName(AppConfig.APP_NAME)
        # Ensure AppConfig.APP_VERSION is correctly reflecting the main.py version if desired
        self.app.setApplicationVersion(
            AppConfig.APP_VERSION
        )  # AppConfig.APP_VERSION is "1.0.0"
        self.logger.info(
            f"Starting {AppConfig.APP_NAME} v1.3.1"
        )  # Log current main.py version

        self.initialize_database()
        self.current_user = None

        self.splash_screen = None
        self.small_login_dialog = None
        self.horse_management_screen = None
        self.user_management_screen = None

    def setup_logging(self):
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
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Logging configured.")

    def initialize_database(self):
        try:
            self.logger.info("Initializing database...")
            db_manager.initialize_database()
            self.logger.info("Database initialized successfully.")
        except Exception as e:
            self.logger.critical(
                f"FATAL ERROR: Failed to initialize database: {e}", exc_info=True
            )
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Database Error")
            msg_box.setText(
                f"Could not initialize the database.\nApplication will exit.\n\nError: {e}\n\nCheck logs for details."
            )
            msg_box.exec()
            sys.exit(1)

    def run(self):
        self.logger.info("Running EDSI Application...")
        self.show_splash_screen()
        sys.exit(self.app.exec())

    def show_splash_screen(self):
        self.logger.debug("Showing Interactive Splash Screen.")
        if self.splash_screen:
            self.splash_screen.deleteLater()

        self.splash_screen = SplashScreen()
        self.splash_screen.login_area_clicked.connect(self.on_splash_login_clicked)
        self.splash_screen.exit_area_clicked.connect(
            lambda: self.cleanup_and_exit("Exit clicked on splash screen.")
        )
        self.splash_screen.show()

    def on_splash_login_clicked(self):
        self.logger.info("Login area clicked on splash screen.")
        # self.splash_screen.hide() # Removed: Splash stays visible behind login dialog
        self.show_small_login_dialog()

    def show_small_login_dialog(self):
        self.logger.debug("Showing Small Login Dialog.")
        if self.small_login_dialog:
            self.small_login_dialog.deleteLater()

        # Pass self.splash_screen as parent if you want it truly modal to splash,
        # or None if application-modal is sufficient.
        self.small_login_dialog = SmallLoginDialog(
            parent=(
                self.splash_screen
                if self.splash_screen and self.splash_screen.isVisible()
                else None
            )
        )
        self.small_login_dialog.login_successful.connect(self.on_login_successful)

        # exec_() makes it modal and blocks until dialog is closed
        # The rejected signal is implicitly handled by exec_ returning QDialog.DialogCode.Rejected
        dialog_result = self.small_login_dialog.exec()

        if dialog_result == QDialog.DialogCode.Accepted:
            # Login was successful (already handled by on_login_successful signal)
            self.logger.debug("SmallLoginDialog accepted (login successful).")
        else:  # Dialog was cancelled or closed via 'X'
            self.on_small_login_rejected()

    def on_small_login_rejected(self):
        self.logger.info("Small login dialog was cancelled or closed by user.")
        # If login is aborted, the splash screen is still visible.
        # The user can then choose to click "Login" again or "Exit" on the splash screen.
        # No need to re-show splash_screen as it was never hidden.
        # No need to exit application here, user can use splash's exit.
        if self.small_login_dialog:  # Clean up dialog if it existed
            self.small_login_dialog.deleteLater()
            self.small_login_dialog = None

    def on_login_successful(self, user_id):
        self.current_user = user_id
        self.logger.info(f"User '{self.current_user}' logged in successfully.")

        if self.small_login_dialog:
            # Dialog will be accepted and close itself, but ensure it's cleaned up
            self.small_login_dialog.deleteLater()
            self.small_login_dialog = None
        if self.splash_screen:
            self.splash_screen.close()  # Now close the splash screen
            self.splash_screen.deleteLater()
            self.splash_screen = None

        self.show_horse_management()

    def show_horse_management(self):
        if not self.current_user:
            self.logger.error("Cannot show horse management screen: No user logged in.")
            self.show_splash_screen()
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
        self.horse_management_screen.setup_requested.connect(
            self.show_user_management_screen
        )
        self.horse_management_screen.show()
        self.logger.info("Horse Management Screen displayed.")

    def on_horse_management_exit(self):
        self.logger.info("Exit requested from Horse Management screen (logoff).")
        if self.horse_management_screen:
            self.horse_management_screen.close()
            self.horse_management_screen.deleteLater()
            self.horse_management_screen = None
        self.current_user = None
        self.logger.info("User logged off.")
        self.show_splash_screen()

    def show_user_management_screen(self):
        if not self.current_user:
            self.logger.error("Cannot show user management: No admin user context.")
            return
        self.logger.info(
            f"Showing User Management Screen for admin '{self.current_user}'."
        )
        if self.horse_management_screen:
            self.horse_management_screen.hide()
        if self.user_management_screen:
            self.user_management_screen.deleteLater()
        self.user_management_screen = UserManagementScreen(
            current_admin_user=self.current_user
        )
        self.user_management_screen.exit_requested.connect(self.on_user_management_exit)
        self.user_management_screen.show()

    def on_user_management_exit(self):
        self.logger.info("Exiting User Management Screen.")
        if self.user_management_screen:
            self.user_management_screen.close()
            self.user_management_screen.deleteLater()
            self.user_management_screen = None
        if self.horse_management_screen:
            self.horse_management_screen.show()
            self.logger.info("Returned to Horse Management Screen.")
        else:
            self.logger.warning(
                "Horse management screen not found after exiting user management. Logging off."
            )
            self.on_horse_management_exit()

    def cleanup_and_exit(self, reason="User requested exit."):
        self.logger.info(f"Initiating application cleanup and exit. Reason: {reason}")
        try:
            db_manager.close()
            self.logger.info("Database connection closed.")
        except Exception as e:
            self.logger.error(f"Error closing database connection: {e}", exc_info=True)

        for widget in QApplication.instance().topLevelWidgets():
            widget.close()
            widget.deleteLater()  # Ensure proper cleanup

        self.logger.info("Exiting application.")
        QApplication.instance().quit()


def main():
    app_instance = EDSIApplication()
    app_instance.run()


if __name__ == "__main__":
    main()
