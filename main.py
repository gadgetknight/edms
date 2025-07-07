# main.py

"""
EDSI Veterinary Management System - Main Application Entry Point
Version: 2.1.5
Purpose: Configured to use user-defined paths from AppConfig for logging and database.
         Now imports all top-level managers/controllers directly and passes them
         down using dependency injection to resolve persistent ModuleNotFoundError.
Last Updated: June 30, 2025
Author: Claude Assistant (Modified by Gemini, further modified by Coding partner)

Changelog:
- v2.1.5 (2025-06-30):
    - **CRITICAL BUG FIX (Persistent PermissionError):** Implemented an aggressive check
      at the beginning of `EDSIApplication.setup_logging()` to ensure that if `AppConfig.LOG_DIR`
      resolves to a protected system directory (like 'Program Files'), it is
      overridden to use `tempfile.gettempdir()` for logging. This guarantees logs
      are written to a user-writable location, resolving the recurring `PermissionError`
      on startup for installed applications.
- v2.1.4 (2025-06-30):
    - **BUG FIX**: Corrected typo `_PROJECT_ROOT_FOR_PATHing` to `_PROJECT_ROOT_FOR_PATHING`
      at line 46 to resolve `NameError`.
    - Ensured `_initial_log_dir_fallback` robustly uses `tempfile.gettempdir()`
      for early logging to prevent `PermissionError` when run from protected directories.
- v2.1.3 (2025-06-30):
    - Modified `show_horse_management_screen` and `show_user_management_screen` to
      call `.showMaximized()` on the respective window instances, ensuring these
      screens open in a full-screen (maximized) state by default.
- v2.1.2 (2025-06-30):
    - **CRITICAL BUG FIX (PermissionError on startup from Program Files):** Modified the
      `_initial_log_dir_fallback` in the `if __name__ == "__main__"` block
      to use `tempfile.gettempdir()` for early logging. This ensures that even
      before AppConfig is fully initialized, any initial logs are written to a
      user-writable temporary directory, preventing `PermissionError: Access is denied`
      when the application is installed in protected directories like `Program Files`.
- v2.1.1 (2025-06-23):
    - **CRITICAL BUG FIX (Final Attempt for ModuleNotFoundError):** Moved `sys.path`
      manipulation to the *absolute very top* of the file, before any other imports,
      to guarantee that the project root is added to Python's search path immediately.
      This ensures top-level packages like 'config' and 'services' are discoverable.
"""

import sys
import os
import tempfile

# CRITICAL BUG FIX: Add project root to sys.path at the very beginning of the script.
# This ensures Python can find top-level packages like 'config' and 'services'.
# __file__ gives the path to this script. dirname(__file__) is its directory.
# os.pardir is '..'. So, join(dirname(__file__), os.pardir) goes up one level.
# abspath ensures it's a full path.
_PROJECT_ROOT_FOR_PATHING = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir)
)

if _PROJECT_ROOT_FOR_PATHING not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT_FOR_PATHING)


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

# Now, with the sys.path fixed above, these imports should resolve correctly.
from config.config_manager import config_manager as _config_manager_instance
from services.backup_manager import backup_manager as _backup_manager_instance

# Import AppConfig (which now pulls paths from _config_manager_instance)
from config.database_config import db_manager
from config.app_config import AppConfig

# These imports are dependent on AppConfig's paths being set up correctly
# For instance, SplashScreen may try to load assets.
from views.auth.splash_screen import SplashScreen
from views.auth.small_login_dialog import SmallLoginDialog
from views.horse.horse_unified_management import HorseUnifiedManagement
from views.admin.user_management_screen import UserManagementScreen

# The global exception hook logger is defined here for early availability
exception_logger = logging.getLogger("GlobalExceptionHook")


def global_exception_hook(exctype, value, tb):
    """Handle uncaught exceptions globally and log them."""
    formatted_traceback = "".join(traceback.format_exception(exctype, value, tb))
    exception_logger.critical(
        f"Unhandled exception: {exctype.__name__}: {value}\n{formatted_traceback}",
        exc_info=(exctype, value, tb),
    )
    app_instance = QApplication.instance()
    if app_instance:
        # Show a critical error message box if the QApplication exists
        QMessageBox.critical(
            None,
            "Critical Application Error",
            f"A critical error occurred: {value}\n\nPlease check logs for details.",
        )


class EDSIApplication(QApplication):
    """
    Main application class for the EDSI Veterinary Management System.
    Handles application lifecycle, logging, database initialization, and screen flow.
    """

    def __init__(self, config_manager_instance, backup_manager_instance):
        super().__init__(sys.argv)
        # Set the global exception hook early
        sys.excepthook = global_exception_hook

        self._config_manager = config_manager_instance
        self._backup_manager = backup_manager_instance

        self.current_user_id: Optional[str] = None
        self.splash_screen: Optional[SplashScreen] = None
        self.login_dialog: Optional[SmallLoginDialog] = None
        self.horse_management_screen: Optional[HorseUnifiedManagement] = None
        self.user_management_screen: Optional[UserManagementScreen] = None
        self.active_screen_name: Optional[str] = None

        # Ensure core application directories exist (now uses AppConfig's resolved paths)
        AppConfig.ensure_directories()

        # Set basic application info
        self.setApplicationName(AppConfig.APP_NAME)
        self.setApplicationVersion(AppConfig.APP_VERSION)
        self.setOrganizationName("EDSI")

        # Initialize the logger for this instance *before* calling setup_logging
        self.logger = logging.getLogger(self.__class__.__name__)

        # Setup logging using the paths resolved by AppConfig
        self.setup_logging()

        self.logger.info(f"Starting {AppConfig.APP_NAME} v{AppConfig.APP_VERSION}")
        self.logger.info(f"Python version: {sys.version}")
        self.logger.info(f"PySide6 version: {self.applicationVersion()}")

        # Initialize the database using the URL from AppConfig
        self.initialize_database()

        # Start the application flow with the splash screen
        self.show_splash_screen()

    def setup_logging(self):
        """
        Configures application logging to both console and a rotating file.
        Uses log directory and file paths from AppConfig.
        """
        log_config = AppConfig.get_logging_config()

        # NEW: Aggressive check for log directory if it resolves to Program Files
        # This prevents PermissionError on installed applications.
        final_log_dir = log_config["log_dir"]
        program_files_env = os.environ.get("ProgramFiles", "")
        program_files_x86_env = os.environ.get("ProgramFiles(x86)", "")

        # Check if the resolved log_dir starts with Program Files paths
        if (
            program_files_env
            and final_log_dir.lower().startswith(program_files_env.lower())
        ) or (
            program_files_x86_env
            and final_log_dir.lower().startswith(program_files_x86_env.lower())
        ):

            # If it's in Program Files, override to a user-writable temp directory
            # We don't use AppData directly here as AppConfig might not yet be fully configured for paths.
            temp_log_dir = os.path.join(tempfile.gettempdir(), "EDMS_runtime_logs")
            os.makedirs(temp_log_dir, exist_ok=True)  # Ensure it exists

            self.logger.warning(
                f"AppConfig.LOG_DIR '{final_log_dir}' resolved to a protected location. "
                f"Overriding to user-writable temporary directory: '{temp_log_dir}' for runtime logging."
            )
            final_log_dir = temp_log_dir
            log_config["app_log_file"] = os.path.join(final_log_dir, "edsi_app.log")
            log_config["db_log_file"] = os.path.join(final_log_dir, "edsi_db.log")
            log_config["log_dir"] = (
                final_log_dir  # Update log_config with the safe path
            )

        # Ensure the log directory exists BEFORE setting up file handlers.
        if not os.path.exists(final_log_dir):
            try:
                os.makedirs(final_log_dir)
            except OSError as e:
                # If log directory creation fails, fall back to console-only logging
                print(
                    f"Error creating log directory '{final_log_dir}': {e}",
                    file=sys.stderr,
                )
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

        # Clear existing handlers to prevent duplicate logs if called multiple times
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s"
        )

        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # Add file handler with rotation
        try:
            file_handler = RotatingFileHandler(
                log_config["app_log_file"],
                maxBytes=log_config["log_max_bytes"],
                backupCount=log_config["log_backup_count"],
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            self.logger.info("Logging configured (Console and File)")
        except Exception as e:
            print(f"Error setting up file logger: {e}", file=sys.stderr)
            self.logger.info(
                "Logging configured (Console only due to file handler error)"
            )

    def initialize_database(self):
        """
        Initializes the database connection using the URL from AppConfig.
        Ensures the database is accessible before proceeding.
        """
        self.logger.info("Initializing database...")
        try:
            # db_manager is a function that returns the instance, so call it first
            db_manager().initialize_database()
            # Perform a simple query to verify connection
            with db_manager().get_session() as session:
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
        """Displays the application splash screen."""
        self.logger.info("Showing splash screen")
        self._cleanup_screens(keep_main=False)
        self.splash_screen = SplashScreen()
        self.splash_screen.login_requested.connect(self.show_login_dialog)
        self.splash_screen.exit_requested.connect(self.quit_application)
        self.splash_screen.show()

    def show_login_dialog(self):
        """Displays the login dialog, potentially over the splash screen."""
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

    def handle_login_success(self, user_id: str):
        """Handles a successful login event."""
        self.current_user_id = user_id
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
        """Handles the event when the login dialog is closed without a successful login."""
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
        """Displays the main horse management screen."""
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
        )
        self.active_screen_name = "Horse Management"

        self.horse_management_screen.exit_requested.connect(self.handle_logout)
        self.horse_management_screen.closing.connect(self.on_main_screen_closing)
        self.horse_management_screen.setup_requested.connect(
            self.show_user_management_screen
        )
        self.horse_management_screen.showMaximized()
        self.logger.info("Horse Management Screen shown.")

    def show_user_management_screen(self):
        """Displays the user and system management screen."""
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
        self.user_management_screen = UserManagementScreen(
            current_user_id=self.current_user_id,
            config_manager_instance=self._config_manager,
            backup_manager_instance=self._backup_manager,
        )

        self.user_management_screen.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.user_management_screen.destroyed.connect(
            self.handle_user_management_destroyed
        )

        self.user_management_screen.showMaximized()
        self.logger.info("User Management Screen shown.")

    def handle_user_management_destroyed(self):
        """Slot to reset reference when User Management Screen is destroyed."""
        self.logger.info(
            "User Management Screen was closed and its instance destroyed."
        )
        self.user_management_screen = None

    def handle_logout(self):
        """Handles user logout request."""
        active_user = self.current_user_id or "Unknown user"
        screen_name = self.active_screen_name or "current screen"
        self.logger.info(f"User '{active_user}' logging out from {screen_name}.")
        self.current_user_id = None
        self.active_screen_name = None
        self.logger.info("Logout requested. Application will now exit.")
        self.quit_application()

    def on_main_screen_closing(self):
        """Handles closure of the main application screen (Horse Management)."""
        self.logger.info("Main application screen (Horse Management) is closing.")
        if self.current_user_id:
            self.logger.info("Main screen closed by user; initiating application quit.")
            self.quit_application()

    def quit_application(self):
        """Initiates a clean shutdown of the entire application."""
        self.logger.info("Application quit requested.")
        self._cleanup_screens(keep_main=False)
        self.quit()

    def _cleanup_screens(self, keep_main: bool = False):
        """
        Closes and deletes existing screen instances.
        Args:
            keep_main (bool): If True, the HorseUnifiedManagement screen will not be closed.
        """
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
                self.splash_screen.exit_requested.connect(self.quit_application)
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
        """Starts the QApplication event loop."""
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
    """Main entry point function for the application."""
    # This block requires _config_manager_instance to be available.
    # AppConfig.LOG_DIR depends on _config_manager_instance.
    # To handle potential issues with _config_manager_instance not being fully
    # initialized (e.g., if it attempts to load config.ini which depends on AppConfig
    # in a circular way during global import), we must manage this carefully.

    # 1. Instantiate ConfigManager (which also handles its own file loading)
    # This needs to be done *before* AppConfig is initialized if AppConfig uses it immediately.
    # The global _config_manager_instance from config.config_manager is already instantiated.
    # So we just refer to it.
    _injected_config_manager = _config_manager_instance

    # 2. Inject ConfigManager into AppConfig
    # This must happen before AppConfig.ensure_directories() and AppConfig.get_logging_config()
    # AppConfig.set_config_manager_instance(_injected_config_manager) # Line was not present in 2.1.0 (from your dump)

    # Now that AppConfig is configured with _injected_config_manager, its paths are ready.
    # We can ensure the log directory exists and set up initial logging.
    if not os.path.exists(AppConfig.LOG_DIR):
        try:
            os.makedirs(AppConfig.LOG_DIR)
        except OSError as e:
            print(
                f"Could not create log directory: {AppConfig.LOG_DIR}. Error: {e}",
                file=sys.stderr,
            )

    logging.basicConfig(
        level=AppConfig.LOGGING_LEVEL,
        format="%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    main_logger = logging.getLogger(__name__)
    main_logger.info("Application main script started.")

    try:
        # 3. Instantiate DatabaseManager, injecting AppConfig and ConfigManager
        # DatabaseManager needs AppConfig for its DB_URL and ConfigManager for internal config queries.
        from config.database_config import set_db_manager_instance, DatabaseManager

        set_db_manager_instance(DatabaseManager(AppConfig, _injected_config_manager))

        # Pass the instantiated manager instances to the QApplication constructor
        app = EDSIApplication(
            config_manager_instance=_injected_config_manager,
            backup_manager_instance=_backup_manager_instance,  # This assumes _backup_manager_instance is globally available from a successful import
        )
        exit_code = app.run()
        main_logger.info(f"Application exiting with code {exit_code}")
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
    # Ensure initial log directory for main's own logging is robust
    # Using a platform-appropriate temporary directory for early logging
    _initial_log_dir_fallback = os.path.join(tempfile.gettempdir(), "EDMS_temp_logs")
    os.makedirs(_initial_log_dir_fallback, exist_ok=True)

    # Configure basic logging for the `__main__` block.
    # This is a fallback/initial logging that will be reconfigured
    # more thoroughly by `EDSIApplication.setup_logging` once the app starts.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            # Also add a file handler for this very early fallback, in case of critical startup errors
            logging.FileHandler(
                os.path.join(_initial_log_dir_fallback, "edms_startup_fallback.log"),
                mode="a",
            ),
        ],
    )

    main_logger_for_init = logging.getLogger(__name__)
    main_logger_for_init.info("Application main script invoked from __main__ block.")
    main_logger_for_init.info(f"Early logging fallback to: {_initial_log_dir_fallback}")

    # Call main function to start the application logic
    main()

    main_logger_for_init.info("Application main script finished execution.")
