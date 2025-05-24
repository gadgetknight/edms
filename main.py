# main.py

"""
EDSI Veterinary Management System - Main Application Entry Point
Version: 2.0.0
Purpose: Simplified main application with clean Splash → Login → Main Window flow.
         Removed over-engineered complexity and focused on stable foundation.
Last Updated: May 24, 2025
Author: Claude Assistant

Changelog:
- v2.0.0 (2025-05-24):
    - Complete rewrite for Phase 1 (Chunk 1) simplification
    - Removed UserManagementScreen integration
    - Simplified to basic Splash → Login → Main Window flow
    - Removed complex signal/slot connections
    - Fixed circular import issues
    - Streamlined exception handling
    - Removed unused screen management complexity
    - Focused on stable foundation for horse management
    - Clean separation of concerns
    - Comprehensive logging without over-engineering
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
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, QTimer
from sqlalchemy import text

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.database_config import db_manager
from config.app_config import AppConfig
from views.auth.splash_screen import SplashScreen
from views.auth.small_login_dialog import SmallLoginDialog

# Global exception handling
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


class MainWindow(QMainWindow):
    """Simple main window placeholder for horse management"""

    def __init__(self, current_user: str, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setup_ui()

    def setup_ui(self):
        """Setup basic main window UI"""
        self.setWindowTitle(f"EDSI Horse Management - User: {self.current_user}")
        self.setMinimumSize(1000, 700)

        # Simple central widget with welcome message
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        welcome_label = QLabel(
            f"Welcome to EDSI Horse Management\n\nLogged in as: {self.current_user}"
        )
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
                color: #E2E8F0;
            }
        """
        )

        layout.addWidget(welcome_label)

        # Apply dark theme
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #2D3748;
                color: #E2E8F0;
            }
        """
        )

        self.logger.info(f"Main window initialized for user: {self.current_user}")


class EDSIApplication(QApplication):
    """Main application class with simplified flow"""

    def __init__(self):
        super().__init__(sys.argv)

        # Set global exception handler
        sys.excepthook = global_exception_hook

        # Initialize application
        self.current_user_id: Optional[str] = None
        self.splash_screen: Optional[SplashScreen] = None
        self.login_dialog: Optional[SmallLoginDialog] = None
        self.main_window: Optional[MainWindow] = None

        # Setup logging first
        self.setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Log startup info
        self.logger.info(f"Starting {AppConfig.APP_NAME} v{AppConfig.APP_VERSION}")
        self.logger.info(f"Python version: {sys.version}")
        self.logger.info(f"PySide6 version: {self.applicationVersion()}")

        # Set application properties
        self.setApplicationName(AppConfig.APP_NAME)
        self.setApplicationVersion(AppConfig.APP_VERSION)
        self.setOrganizationName("EDSI")

        # Ensure required directories exist
        AppConfig.ensure_directories()

        # Initialize database
        self.initialize_database()

        # Start with splash screen
        self.show_splash_screen()

    def setup_logging(self):
        """Setup application logging"""
        log_config = AppConfig.get_logging_config()

        # Create log directory if needed
        if not os.path.exists(log_config["log_dir"]):
            try:
                os.makedirs(log_config["log_dir"])
            except OSError as e:
                print(f"Error creating log directory: {e}", file=sys.stderr)
                return

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_config["level"])

        # Clear existing handlers
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s"
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # File handler
        try:
            file_handler = RotatingFileHandler(
                log_config["app_log_file"],
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            logging.info("Logging configured (Console and File)")
        except Exception as e:
            print(f"Error setting up file logger: {e}", file=sys.stderr)
            logging.info("Logging configured (Console only)")

    def initialize_database(self):
        """Initialize database connection"""
        self.logger.info("Initializing database...")
        try:
            db_manager.initialize_database()

            # Test connection
            with db_manager.get_session() as session:
                session.execute(text("SELECT 1"))

            self.logger.info("Database initialized successfully")

        except Exception as e:
            self.logger.critical(f"Database initialization failed: {e}", exc_info=True)
            QMessageBox.critical(
                None,
                "Database Error",
                f"Failed to initialize database: {e}\n\nApplication will exit.",
            )
            sys.exit(1)

    def show_splash_screen(self):
        """Display splash screen"""
        self.logger.info("Showing splash screen")

        # Clean up existing screens
        self._cleanup_screens()

        self.splash_screen = SplashScreen()
        self.splash_screen.login_requested.connect(self.show_login_dialog)
        self.splash_screen.exit_requested.connect(self.quit_application)
        self.splash_screen.show()

    def show_login_dialog(self):
        """Show login dialog"""
        self.logger.info("Showing login dialog")

        # Don't create multiple login dialogs
        if self.login_dialog and self.login_dialog.isVisible():
            self.login_dialog.raise_()
            self.login_dialog.activateWindow()
            return

        # Create login dialog
        parent_widget = (
            self.splash_screen
            if self.splash_screen and self.splash_screen.isVisible()
            else None
        )
        self.login_dialog = SmallLoginDialog(parent=parent_widget)
        self.login_dialog.login_successful.connect(self.handle_login_success)
        self.login_dialog.dialog_closed.connect(self.handle_login_dialog_closed)

        # Show modal dialog
        self.login_dialog.setModal(True)
        self.login_dialog.show()

    def handle_login_success(self, user_id: str):
        """Handle successful login"""
        self.current_user_id = user_id
        self.logger.info(f"User '{user_id}' logged in successfully")

        # Close login dialog and splash screen
        if self.login_dialog:
            self.login_dialog.close()
            self.login_dialog = None

        if self.splash_screen:
            self.splash_screen.close()
            self.splash_screen = None

        # Show main window
        self.show_main_window()

    def handle_login_dialog_closed(self):
        """Handle login dialog closure"""
        self.logger.debug("Login dialog closed")

        # If no successful login and no main window, ensure splash is visible
        if not self.current_user_id and not (
            self.main_window and self.main_window.isVisible()
        ):
            if not (self.splash_screen and self.splash_screen.isVisible()):
                self.show_splash_screen()

    def show_main_window(self):
        """Show main application window"""
        if not self.current_user_id:
            self.logger.warning("Attempted to show main window without login")
            self.show_splash_screen()
            return

        self.logger.info(f"Showing main window for user: {self.current_user_id}")

        # Clean up existing screens
        self._cleanup_screens()

        # Create and show main window
        self.main_window = MainWindow(self.current_user_id)
        self.main_window.show()

    def quit_application(self):
        """Quit application cleanly"""
        self.logger.info("Application quit requested")
        self._cleanup_screens()
        self.quit()

    def _cleanup_screens(self):
        """Clean up all open screens"""
        screens = [
            ("splash_screen", self.splash_screen),
            ("login_dialog", self.login_dialog),
            ("main_window", self.main_window),
        ]

        for name, screen in screens:
            if screen and screen.isVisible():
                self.logger.debug(f"Closing {name}")
                screen.close()

        # Clear references
        self.splash_screen = None
        self.login_dialog = None
        # Don't clear main_window reference as it may be reused

    def run(self):
        """Run the application"""
        self.logger.info(f"Starting {AppConfig.APP_NAME} event loop")
        try:
            exit_code = self.exec()
            self.logger.info(f"Application finished with exit code: {exit_code}")
            return exit_code
        except Exception as e:
            self.logger.critical(f"Critical error in event loop: {e}", exc_info=True)
            return 1


def main():
    """Main entry point"""
    try:
        app = EDSIApplication()
        exit_code = app.run()
        logging.info(f"Application exiting with code {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error starting application: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
