# main.py

"""
EDSI Veterinary Management System
Main application entry point
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from config.database_config import db_manager
from config.app_config import AppConfig
from views.auth.splash_screen import SplashScreen
from views.auth.login_screen import LoginScreen
from views.main_menu import MainMenu
from models import *  # Import all models to register them


class EDSIApplication:
    """Main application class that manages the application flow"""

    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Create Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(AppConfig.APP_NAME)
        self.app.setApplicationVersion(AppConfig.APP_VERSION)

        # Initialize database
        self.initialize_database()

        # Current user
        self.current_user = None

        # Application windows
        self.splash_screen = None
        self.login_screen = None
        self.main_menu = None

    def setup_logging(self):
        """Configure application logging"""
        import os

        # Create logs directory if it doesn't exist
        logs_dir = AppConfig.get_logs_dir()

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(os.path.join(logs_dir, "edsi.log")),
                logging.StreamHandler(sys.stdout),
            ],
        )

    def initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            self.logger.info("Initializing database...")
            db_manager.initialize_database()
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            sys.exit(1)

    def run(self):
        """Run the application"""
        self.logger.info("Starting EDSI Veterinary Management System")

        # Show splash screen
        self.show_splash_screen()

        # Start the Qt event loop
        sys.exit(self.app.exec())

    def show_splash_screen(self):
        """Display the splash screen"""
        self.splash_screen = SplashScreen()
        self.splash_screen.splash_closed.connect(self.on_splash_closed)
        self.splash_screen.show()

    def on_splash_closed(self):
        """Handle splash screen closure"""
        self.splash_screen.deleteLater()
        self.splash_screen = None
        self.show_login_screen()

    def show_login_screen(self):
        """Display the login screen"""
        self.login_screen = LoginScreen()
        self.login_screen.login_successful.connect(self.on_login_successful)
        self.login_screen.exit_requested.connect(self.on_exit_requested)
        self.login_screen.show()

    def on_login_successful(self, user_id):
        """Handle successful login"""
        self.current_user = user_id
        self.logger.info(f"User '{user_id}' logged in successfully")

        # Close login screen
        self.login_screen.deleteLater()
        self.login_screen = None

        # Show main menu
        self.show_main_menu()

    def on_exit_requested(self):
        """Handle exit request from login screen"""
        self.logger.info("Exit requested from login screen")
        self.cleanup_and_exit()

    def show_main_menu(self):
        """Display the main menu"""
        self.main_menu = MainMenu(self.current_user)

        # Connect menu signals to handlers
        self.main_menu.horse_review_update_selected.connect(self.on_horse_review_update)
        self.main_menu.add_new_horse_selected.connect(self.on_add_new_horse)
        self.main_menu.delete_horse_selected.connect(self.on_delete_horse)
        self.main_menu.table_maintenance_selected.connect(self.on_table_maintenance)
        self.main_menu.print_reports_selected.connect(self.on_print_reports)
        self.main_menu.owners_ar_selected.connect(self.on_owners_ar)
        self.main_menu.system_utilities_selected.connect(self.on_system_utilities)
        self.main_menu.mass_update_selected.connect(self.on_mass_update)
        self.main_menu.logoff_exit_selected.connect(self.on_logoff_exit)
        self.main_menu.logoff_no_exit_selected.connect(self.on_logoff_no_exit)

        self.main_menu.show()

    # Menu handlers (placeholders for now)
    def on_horse_review_update(self):
        """Handle horse review/update selection"""
        self.logger.info("Horse review/update selected")
        # TODO: Implement horse review/update screen
        self.main_menu.show_info(
            "Not Implemented", "Horse review/update feature coming soon!"
        )

    def on_add_new_horse(self):
        """Handle add new horse selection"""
        self.logger.info("Add new horse selected")
        # TODO: Implement add new horse screen
        self.main_menu.show_info(
            "Not Implemented", "Add new horse feature coming soon!"
        )

    def on_delete_horse(self):
        """Handle delete horse selection"""
        self.logger.info("Delete horse selected")
        # TODO: Implement delete horse screen
        self.main_menu.show_info("Not Implemented", "Delete horse feature coming soon!")

    def on_table_maintenance(self):
        """Handle table maintenance selection"""
        self.logger.info("Table maintenance selected")
        # TODO: Implement table maintenance screen
        self.main_menu.show_info(
            "Not Implemented", "Table maintenance feature coming soon!"
        )

    def on_print_reports(self):
        """Handle print reports selection"""
        self.logger.info("Print reports selected")
        # TODO: Implement print reports screen
        self.main_menu.show_info(
            "Not Implemented", "Print reports feature coming soon!"
        )

    def on_owners_ar(self):
        """Handle owners A/R selection"""
        self.logger.info("Owners A/R selected")
        # TODO: Implement owners A/R screen
        self.main_menu.show_info("Not Implemented", "Owners A/R feature coming soon!")

    def on_system_utilities(self):
        """Handle system utilities selection"""
        self.logger.info("System utilities selected")
        # TODO: Implement system utilities screen
        self.main_menu.show_info(
            "Not Implemented", "System utilities feature coming soon!"
        )

    def on_mass_update(self):
        """Handle mass update selection"""
        self.logger.info("Mass update selected")
        # TODO: Implement mass update screen
        self.main_menu.show_info("Not Implemented", "Mass update feature coming soon!")

    def on_logoff_exit(self):
        """Handle logoff and exit"""
        self.logger.info("Logoff and exit selected")
        if self.main_menu.show_question(
            "Confirm Exit", "Are you sure you want to logoff and exit?"
        ):
            self.cleanup_and_exit()

    def on_logoff_no_exit(self):
        """Handle logoff without exit"""
        self.logger.info("Logoff without exit selected")
        if self.main_menu.show_question(
            "Confirm Logoff", "Are you sure you want to logoff?"
        ):
            # Close main menu
            self.main_menu.close()
            self.main_menu.deleteLater()
            self.main_menu = None

            # Reset current user
            self.current_user = None

            # Show login screen again
            self.show_login_screen()

    def cleanup_and_exit(self):
        """Cleanup resources and exit application"""
        self.logger.info("Cleaning up and exiting application")

        # Close database connection
        db_manager.close()

        # Close all windows
        if self.main_menu:
            self.main_menu.close()
        if self.login_screen:
            self.login_screen.close()
        if self.splash_screen:
            self.splash_screen.close()

        # Quit application
        self.app.quit()


def main():
    """Main entry point"""
    app = EDSIApplication()
    app.run()


if __name__ == "__main__":
    main()
