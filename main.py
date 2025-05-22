# main.py

"""
EDSI Veterinary Management System - Main Application
Version: 1.3.12
Purpose: Main entry point. Corrected signal connection for returning to Horse Management
         from UserManagementScreen's header button.
Last Updated: May 21, 2025
Author: Claude Assistant (Modified by Gemini)

Changelog:
- v1.3.12 (2025-05-21):
    - Connected UserManagementScreen.horse_management_requested signal to
      EDSIApplication.handle_admin_screen_exit in show_user_management_screen.
- v1.3.11 (2025-05-21):
    - Corrected keyword argument in UserManagementScreen instantiation
      from 'current_user_identifier' to 'current_user_id' to match
      the __init__ signature of UserManagementScreen v1.10.7.
# ... (rest of previous changelog)
"""

import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget
from PySide6.QtCore import Qt, QTimer, qVersion
from sqlalchemy import text

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.database_config import db_manager
from config.app_config import (
    LOG_DIR,
    APP_LOG_FILE,
    LOGGING_LEVEL,
    APP_NAME,
    APP_VERSION,
    DATABASE_URL,
)

from views.auth.splash_screen import SplashScreen
from views.auth.small_login_dialog import SmallLoginDialog
from views.horse.horse_unified_management import HorseUnifiedManagement
from views.admin.user_management_screen import UserManagementScreen

exception_logger = logging.getLogger("GlobalExceptionHook")


def global_exception_hook(exctype, value, tb):
    formatted_traceback = "".join(traceback.format_exception(exctype, value, tb))
    exception_logger.critical(
        f"Unhandled exception caught by global hook:\n"
        f"Type: {exctype.__name__}\nValue: {value}\nTraceback:\n{formatted_traceback}",
        exc_info=(exctype, value, tb),
    )
    app_instance = QApplication.instance()
    if app_instance:
        QMessageBox.critical(
            None,
            "Critical Application Error",
            f"A critical error occurred: {value}\n\nPlease check logs.",
        )


class EDSIApplication(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        sys.excepthook = global_exception_hook
        self.current_user_id: Optional[str] = None
        self.splash_screen: Optional[SplashScreen] = None
        self.login_dialog: Optional[SmallLoginDialog] = None
        self.horse_management_screen: Optional[HorseUnifiedManagement] = None
        self.user_management_screen: Optional[UserManagementScreen] = None
        self.setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(
            f"Starting {APP_NAME} v{APP_VERSION}"
        )  # APP_VERSION should be updated here too
        self.logger.info(f"Python version: {sys.version}")
        self.logger.info(f"Qt version: {qVersion()}")
        self.db_manager = db_manager
        self.initialize_database()
        self.setApplicationName(APP_NAME)
        self.setApplicationVersion(APP_VERSION)  # And here
        self.setOrganizationName("EDSI")
        self.show_splash_screen()

    def setup_logging(self):
        log_directory = LOG_DIR
        app_log_file = APP_LOG_FILE
        log_level_str = os.environ.get("LOG_LEVEL", logging.getLevelName(LOGGING_LEVEL))
        log_level = getattr(logging, log_level_str.upper(), LOGGING_LEVEL)
        log_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s"
        )
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        if root_logger.hasHandlers():
            root_logger.handlers.clear()
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_formatter)
        root_logger.addHandler(console_handler)
        if not os.path.exists(log_directory):
            try:
                os.makedirs(log_directory)
            except OSError as e:
                print(
                    f"CRITICAL: Error creating log directory {log_directory}: {e}. File logging disabled.",
                    file=sys.stderr,
                )
                logging.info("Logging configured (Console only).")
                return
        try:
            file_handler = RotatingFileHandler(
                app_log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
            file_handler.setFormatter(log_formatter)
            root_logger.addHandler(file_handler)
            logging.info("Logging configured (Console and File).")
        except Exception as e:
            print(
                f"CRITICAL: Error setting up file logger {app_log_file}: {e}. File logging disabled.",
                file=sys.stderr,
            )
            logging.info("Logging configured (Console only due to file handler error).")

    def initialize_database(self):
        self.logger.info("Initializing database...")
        try:
            self.db_manager.initialize_database(DATABASE_URL)
            with self.db_manager.get_session() as session:
                session.execute(text("SELECT 1"))
            self.logger.info("Database initialized successfully.")
        except Exception as e:
            self.logger.critical(f"Failed to initialize database: {e}", exc_info=True)
            QMessageBox.critical(
                None, "Database Error", f"Database error: {e}\nApp will exit."
            )
            sys.exit(1)

    def show_splash_screen(self):
        self.logger.debug("Attempting to show splash screen.")
        self.close_all_screens()
        self.splash_screen = SplashScreen()
        self.splash_screen.login_requested.connect(self.show_login_dialog)
        self.splash_screen.exit_requested.connect(self.quit_application)
        self.splash_screen.show()
        self.logger.info("Splash screen displayed.")

    def show_login_dialog(self):
        self.logger.info("Login area clicked on splash screen.")
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

    def handle_login_dialog_closed(self):
        self.logger.debug("Login dialog reported closed.")
        if not self.current_user_id and not (
            (self.horse_management_screen and self.horse_management_screen.isVisible())
            or (self.user_management_screen and self.user_management_screen.isVisible())
        ):
            if not (self.splash_screen and self.splash_screen.isVisible()):
                self.logger.info(
                    "Login dialog closed without login success and no screens active."
                )

    def handle_login_success(self, user_id: str):
        self.current_user_id = user_id
        self.logger.info(f"User '{self.current_user_id}' logged in successfully.")
        if self.login_dialog:
            self.login_dialog.close()
            self.login_dialog = None
        if self.splash_screen:
            self.splash_screen.close()
            self.splash_screen = None
        self.show_horse_management_screen()

    def handle_main_screen_closure_signal(self):
        self.logger.warning(
            "DIAGNOSTIC: HorseUnifiedManagement screen emitted 'closing' signal!"
        )

    def show_horse_management_screen(self):
        self.logger.debug("Attempting to show Horse Management Screen.")
        self.close_all_screens()
        if not self.current_user_id:
            self.logger.warning(
                "Attempted to show horse management screen without login. Navigating to splash."
            )
            self.show_splash_screen()
            return
        self.horse_management_screen = HorseUnifiedManagement(
            current_user=self.current_user_id
        )
        if hasattr(self.horse_management_screen, "closing"):
            self.horse_management_screen.closing.connect(
                self.handle_main_screen_closure_signal
            )
        self.horse_management_screen.exit_requested.connect(self.handle_logout)
        self.horse_management_screen.setup_requested.connect(
            self.show_user_management_screen
        )
        self.logger.info("About to call self.horse_management_screen.show()")
        self.horse_management_screen.show()
        self.logger.info("Horse Management Screen show() called.")

    def show_user_management_screen(self):
        self.logger.debug("Attempting to show User Management Screen.")

        if self.horse_management_screen and self.horse_management_screen.isVisible():
            self.logger.debug(
                "Hiding HorseUnifiedManagement screen before showing UserManagementScreen."
            )
            self.horse_management_screen.hide()
        else:
            self.close_all_screens()

        if not self.current_user_id:
            self.logger.warning(
                "Attempted to show user management screen without login. Navigating to splash."
            )
            self.show_splash_screen()
            return

        self.user_management_screen = UserManagementScreen(
            current_user_id=self.current_user_id
        )
        # Connect the footer button's exit_requested signal
        self.user_management_screen.exit_requested.connect(
            self.handle_admin_screen_exit
        )
        # Connect the header button's horse_management_requested signal
        if hasattr(self.user_management_screen, "horse_management_requested"):
            self.user_management_screen.horse_management_requested.connect(
                self.handle_admin_screen_exit  # Re-use same handler as it shows horse screen
            )
        else:
            self.logger.warning(
                "UserManagementScreen does not have 'horse_management_requested' signal."
            )

        self.user_management_screen.show()
        self.logger.info("User Management Screen displayed.")

    def handle_logout(self):
        self.logger.info(
            f"User '{self.current_user_id}' logging out from Horse Management."
        )
        self.current_user_id = None
        self.show_splash_screen()

    def handle_admin_screen_exit(self):
        self.logger.info(
            f"Exiting Admin Screen. User: '{self.current_user_id}'. Returning to Horse Management."
        )
        if self.user_management_screen:
            self.user_management_screen.close()
            self.user_management_screen = None

        if self.horse_management_screen:
            self.logger.debug("Re-showing existing HorseUnifiedManagement screen.")
            self.horse_management_screen.show()
            self.horse_management_screen.activateWindow()
        else:
            self.logger.debug(
                "No existing HorseUnifiedManagement screen, creating new."
            )
            self.show_horse_management_screen()

    def close_all_screens(self, exclude: Optional[QWidget] = None):
        self.logger.debug(
            f"close_all_screens called, excluding: {exclude.__class__.__name__ if exclude else 'None'}"
        )

        screen_attrs = [
            "login_dialog",
            "user_management_screen",
            "horse_management_screen",
            "splash_screen",
        ]

        for attr_name in screen_attrs:
            screen_instance = getattr(self, attr_name, None)
            if (
                screen_instance
                and screen_instance is not exclude
                and screen_instance.isVisible()
            ):
                self.logger.debug(f"Closing {attr_name}.")
                screen_instance.close()
                setattr(self, attr_name, None)

    def quit_application(self):
        self.logger.info("Quit application requested.")
        self.close_all_screens()
        self.quit()

    def run(self):
        self.logger.info(f"Starting {APP_NAME} event loop (sys.excepthook is set)...")
        try:
            # Update APP_VERSION here to match class attribute if necessary
            # self.setApplicationVersion(APP_VERSION) # Already set in __init__
            exit_code = self.exec()
            self.logger.info(f"{APP_NAME} event loop finished. Exit code: {exit_code}")
            return exit_code
        except Exception as e:
            self.logger.critical(
                f"CRITICAL UNCAUGHT ERROR IN EXEC LOOP: {e}", exc_info=True
            )
            return 1


def main():
    # Ensure APP_VERSION is consistent if used elsewhere before EDSIApplication instantiation
    app_instance = EDSIApplication()
    exit_code = app_instance.run()
    logging.info(f"Application exiting with code {exit_code}.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

