# main.py

"""
EDSI Veterinary Management System - Main Application Entry Point
Version: 2.0.5
Purpose: Simplified main application with clean Splash -> Login -> Horse Management flow.
         Corrected UserManagementScreen instantiation to pass current_user_id.
Last Updated: May 26, 2025
Author: Claude Assistant (Modified by Gemini, further modified by Coding partner)

Changelog:
- v2.0.5 (2025-05-26):
    - Modified UserManagementScreen() instantiation in show_user_management_screen
      to pass 'current_user_id' as a positional argument.
- v2.0.4 (2025-05-26):
    - Removed `current_user` keyword argument from `UserManagementScreen()` instantiation.
# ... (previous changelog entries)
"""

import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional
import traceback

from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QDialog,
)
from PySide6.QtCore import (
    Qt,
)
from sqlalchemy import text

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.database_config import db_manager
from config.app_config import AppConfig
from views.auth.splash_screen import SplashScreen
from views.auth.small_login_dialog import SmallLoginDialog
from views.horse.horse_unified_management import HorseUnifiedManagement
from views.admin.user_management_screen import UserManagementScreen

exception_logger = logging.getLogger("GlobalExceptionHook")


def global_exception_hook(exctype, value, tb):
    """Handle uncaught exceptions globally"""
    formatted_traceback = "".join(traceback.format_exception(exctype, value, tb))
    exception_logger.critical(
        f"Unhandled exception: {exctype.__name__}: {value}\n{formatted_traceback}",
        exc_info=(exctype, value, tb),
    )
    app_instance = QApplication.instance()
    if app_instance:
        QMessageBox.critical(
            None,
            "Critical Application Error",
            f"A critical error occurred: {value}\n\nPlease check logs for details.",
        )


class EDSIApplication(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        sys.excepthook = global_exception_hook
        self.current_user_id: Optional[str] = None  # Ensure this is set at login
        self.splash_screen: Optional[SplashScreen] = None
        self.login_dialog: Optional[SmallLoginDialog] = None
        self.horse_management_screen: Optional[HorseUnifiedManagement] = None
        self.user_management_screen: Optional[UserManagementScreen] = None
        self.active_screen_name: Optional[str] = None
        self.setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Starting {AppConfig.APP_NAME} v{AppConfig.APP_VERSION}")
        self.logger.info(f"Python version: {sys.version}")  # Log Python version
        self.logger.info(
            f"PySide6 version: {self.applicationVersion()}"
        )  # Log PySide6/Qt version
        self.setApplicationName(AppConfig.APP_NAME)
        self.setApplicationVersion(AppConfig.APP_VERSION)
        self.setOrganizationName("EDSI")
        AppConfig.ensure_directories()
        self.initialize_database()
        self.show_splash_screen()

    def setup_logging(self):
        log_config = AppConfig.get_logging_config()
        if not os.path.exists(log_config["log_dir"]):
            try:
                os.makedirs(log_config["log_dir"])
            except OSError as e:
                print(f"Error creating log directory: {e}", file=sys.stderr)
                logging.basicConfig(
                    level=log_config["level"],
                    format="%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)],
                )
                logging.warning(
                    "Log directory creation failed. Logging to console only."
                )
                return
        root_logger = logging.getLogger()
        root_logger.setLevel(log_config["level"])
        if root_logger.hasHandlers():
            root_logger.handlers.clear()
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s"
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        try:
            file_handler = RotatingFileHandler(
                log_config["app_log_file"],
                maxBytes=log_config["log_max_bytes"],
                backupCount=log_config["log_backup_count"],
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            logging.info("Logging configured (Console and File)")
        except Exception as e:
            print(f"Error setting up file logger: {e}", file=sys.stderr)
            logging.info("Logging configured (Console only due to file handler error)")

    def initialize_database(self):
        self.logger.info("Initializing database...")
        try:
            db_manager.initialize_database()
            with db_manager.get_session() as session:
                session.execute(text("SELECT 1"))
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.critical(f"Database initialization failed: {e}", exc_info=True)
            QMessageBox.critical(
                None,
                "Database Error",
                f"Failed to initialize database: {e}\n\nThe application will exit.",
            )
            sys.exit(1)

    def show_splash_screen(self):
        self.logger.info("Showing splash screen")
        self._cleanup_screens(keep_main=False)
        self.splash_screen = SplashScreen()
        self.splash_screen.login_requested.connect(self.show_login_dialog)
        self.splash_screen.exit_requested.connect(self.quit_application)
        self.splash_screen.show()

    def show_login_dialog(self):
        self.logger.info("Showing login dialog")
        if self.login_dialog and self.login_dialog.isVisible():
            self.login_dialog.raise_()
            self.login_dialog.activateWindow()
            return
        parent_widget = (
            self.splash_screen
            if self.splash_screen and self.splash_screen.isVisible()
            else None
        )
        self.login_dialog = SmallLoginDialog(parent=parent_widget)
        self.login_dialog.login_successful.connect(self.handle_login_success)
        self.login_dialog.dialog_closed.connect(self.handle_login_dialog_closed)
        self.login_dialog.setModal(True)
        self.login_dialog.show()

    def handle_login_success(self, user_id: str):  # user_id here is typically username
        self.current_user_id = user_id  # Store the logged-in user's identifier
        self.logger.info(f"User '{user_id}' logged in successfully")
        if self.login_dialog:
            try:
                self.login_dialog.login_successful.disconnect(self.handle_login_success)
                self.login_dialog.dialog_closed.disconnect(
                    self.handle_login_dialog_closed
                )
            except RuntimeError:
                self.logger.debug("Slots already disconnected from login_dialog.")
            self.login_dialog.close()
            self.login_dialog.deleteLater()
            self.login_dialog = None
        if self.splash_screen:
            self.splash_screen.close()
            self.splash_screen.deleteLater()
            self.splash_screen = None
        self.show_horse_management_screen()

    def handle_login_dialog_closed(self):
        self.logger.debug("Login dialog closed signal received.")
        if not self.current_user_id:
            if self.login_dialog:
                self.login_dialog.deleteLater()
                self.login_dialog = None
            if not (self.splash_screen and self.splash_screen.isVisible()):
                self.logger.info("Login dialog closed, no splash. Returning to splash.")
                self.show_splash_screen()
            else:
                self.logger.info("Login dialog closed. Splash screen remains active.")

    def show_horse_management_screen(self):
        if not self.current_user_id:
            self.logger.warning("Attempted to show Horse Management without login.")
            self.show_splash_screen()
            return
        self.logger.info(
            f"Showing Horse Management screen for user: {self.current_user_id}"
        )
        self._cleanup_screens(keep_main=False)
        self.horse_management_screen = HorseUnifiedManagement(
            current_user=self.current_user_id
        )  # Pass user_id
        self.active_screen_name = "Horse Management"
        self.horse_management_screen.exit_requested.connect(self.handle_logout)
        self.horse_management_screen.closing.connect(self.on_main_screen_closing)
        self.horse_management_screen.setup_requested.connect(
            self.show_user_management_screen
        )
        self.horse_management_screen.show()
        self.logger.info("Horse Management Screen shown.")

    def show_user_management_screen(self):
        self.logger.info(
            "Setup icon clicked, attempting to show User Management Screen."
        )
        if not self.current_user_id:
            self.logger.error("Cannot show User Management Screen: No user logged in.")
            QMessageBox.warning(
                None,
                "Authentication Error",
                "No user is currently logged in. Please log in to access setup.",
            )
            return

        if self.user_management_screen and self.user_management_screen.isVisible():
            self.logger.info(
                "User Management Screen is already visible. Activating and raising."
            )
            self.user_management_screen.activateWindow()
            self.user_management_screen.raise_()
            return
        if self.user_management_screen:
            self.logger.info("Re-showing existing User Management Screen instance.")
            self.user_management_screen.show()
            self.user_management_screen.activateWindow()
            self.user_management_screen.raise_()
            return

        self.logger.info("Creating new User Management Screen instance.")
        # MODIFIED: Pass current_user_id as the first positional argument
        self.user_management_screen = UserManagementScreen(self.current_user_id)

        self.user_management_screen.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.user_management_screen.destroyed.connect(
            self.handle_user_management_destroyed
        )

        self.user_management_screen.show()
        self.logger.info("User Management Screen shown.")

    def handle_user_management_destroyed(self):
        self.logger.info(
            "User Management Screen was closed and its instance destroyed."
        )
        self.user_management_screen = None

    def handle_logout(self):
        active_user = self.current_user_id or "Unknown user"
        screen_name = self.active_screen_name or "current screen"
        self.logger.info(f"User '{active_user}' logging out from {screen_name}.")
        self.current_user_id = None
        self.active_screen_name = None
        self.logger.info("Logout requested. Application will now exit.")
        self.quit_application()

    def on_main_screen_closing(self):
        self.logger.info("Main application screen (Horse Management) is closing.")
        if self.current_user_id:
            self.logger.info("Main screen closed by user; initiating application quit.")
            self.quit_application()

    def quit_application(self):
        self.logger.info("Application quit requested.")
        self._cleanup_screens(keep_main=False)
        self.quit()

    def _cleanup_screens(self, keep_main: bool = False):
        self.logger.debug(f"Cleanup screens called. Keep main: {keep_main}")
        if self.user_management_screen:
            self.logger.debug("Cleaning up User Management Screen.")
            try:
                self.user_management_screen.destroyed.disconnect(
                    self.handle_user_management_destroyed
                )
            except RuntimeError:
                pass
            self.user_management_screen.close()
            self.user_management_screen = None
        if self.splash_screen:
            try:
                self.splash_screen.login_requested.disconnect(self.show_login_dialog)
                self.splash_screen.exit_requested.disconnect(self.quit_application)
            except RuntimeError:
                pass
            self.splash_screen.close()
            self.splash_screen.deleteLater()
            self.splash_screen = None
            self.logger.debug("Splash screen cleaned up.")
        if self.login_dialog:
            try:
                self.login_dialog.login_successful.disconnect(self.handle_login_success)
                self.login_dialog.dialog_closed.disconnect(
                    self.handle_login_dialog_closed
                )
            except RuntimeError:
                pass
            self.login_dialog.close()
            self.login_dialog.deleteLater()
            self.login_dialog = None
            self.logger.debug("Login dialog cleaned up.")
        if not keep_main and self.horse_management_screen:
            self.logger.debug("Cleaning up Horse Management Screen.")
            try:
                self.horse_management_screen.exit_requested.disconnect(
                    self.handle_logout
                )
                self.horse_management_screen.closing.disconnect(
                    self.on_main_screen_closing
                )
                self.horse_management_screen.setup_requested.disconnect(
                    self.show_user_management_screen
                )
            except RuntimeError:
                pass
            self.horse_management_screen.close()
            self.horse_management_screen.deleteLater()
            self.horse_management_screen = None
            self.logger.debug("Horse management screen cleaned up.")
        self.logger.debug("Screens cleanup finished.")

    def run(self):
        self.logger.info(f"Starting {AppConfig.APP_NAME} event loop")
        try:
            exit_code = self.exec()
            self.logger.info(f"Application finished with exit code: {exit_code}")
            return exit_code
        except Exception as e:
            self.logger.critical(f"Critical error in event loop: {e}", exc_info=True)
            QMessageBox.critical(
                None,
                "Fatal Error",
                f"A fatal error occurred in the application event loop: {e}\nPlease check logs.",
            )
            return 1


def main():
    if not os.path.exists(AppConfig.LOG_DIR):
        try:
            os.makedirs(AppConfig.LOG_DIR)
        except OSError as e:
            print(
                f"Could not create log directory: {AppConfig.LOG_DIR}. Error: {e}",
                file=sys.stderr,
            )
    try:
        app = EDSIApplication()
        exit_code = app.run()
        logging.info(f"Application exiting with code {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        critical_logger = logging.getLogger("main_entry_point")
        critical_logger.critical(
            f"Fatal error starting or running application: {e}", exc_info=True
        )
        try:
            if not QApplication.instance():
                QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Fatal Application Error",
                f"A fatal error occurred: {e}\nApplication will exit. Check logs.",
            )
        except Exception as mb_error:
            print(
                f"Could not display fatal error message box: {mb_error}",
                file=sys.stderr,
            )
        sys.exit(1)


if __name__ == "__main__":
    if not os.path.exists(AppConfig.LOG_DIR):
        try:
            os.makedirs(AppConfig.LOG_DIR)
        except:
            pass
    logging.basicConfig(
        level=AppConfig.LOGGING_LEVEL,
        format="%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    main_logger = logging.getLogger(__name__)
    main_logger.info("Application main script started.")
    main()
    main_logger.info("Application main script finished.")
