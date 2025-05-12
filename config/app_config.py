# config/app_config.py

"""Application configuration settings"""

import os


class AppConfig:
    """Main application configuration"""

    # Application Information
    APP_NAME = "EDSI Veterinary Management System"
    APP_VERSION = "1.0.0"

    # Window Settings
    WINDOW_WIDTH = 1024
    WINDOW_HEIGHT = 768
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 600

    # Colors
    PRIMARY_COLOR = "#0078d4"  # Professional blue
    SECONDARY_COLOR = "#6c757d"  # Neutral gray
    SUCCESS_COLOR = "#28a745"  # Green for confirmations
    WARNING_COLOR = "#ffc107"  # Yellow for warnings
    DANGER_COLOR = "#dc3545"  # Red for errors/critical
    BACKGROUND_COLOR = "#f8f9fa"  # Light gray background
    SURFACE_COLOR = "#ffffff"  # White cards/panels
    TEXT_COLOR = "#212529"  # Dark text
    TEXT_SECONDARY = "#6c757d"  # Gray text

    # Fonts
    DEFAULT_FONT_FAMILY = "Arial"
    DEFAULT_FONT_SIZE = 10
    HEADING_FONT_SIZE = 14
    SMALL_FONT_SIZE = 8
    MONO_FONT_FAMILY = "Consolas"  # For data alignment

    # Database Settings
    DATABASE_BACKUP_ENABLED = True
    DATABASE_BACKUP_FREQUENCY = 24  # hours

    # Session Settings
    SESSION_TIMEOUT = 3600  # seconds (1 hour)
    AUTO_LOGOUT_WARNING = 300  # seconds (5 minutes before logout)

    # Data Validation
    MAX_STRING_LENGTH = 255
    MAX_DESCRIPTION_LENGTH = 500
    MAX_NOTES_LENGTH = 1000

    # File Paths
    @staticmethod
    def get_app_dir():
        """Get application directory"""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def get_database_path():
        """Get database file path"""
        return os.path.join(AppConfig.get_app_dir(), "edsi_database.db")

    @staticmethod
    def get_logs_dir():
        """Get logs directory"""
        logs_dir = os.path.join(AppConfig.get_app_dir(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir

    @staticmethod
    def get_reports_dir():
        """Get reports directory"""
        reports_dir = os.path.join(AppConfig.get_app_dir(), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        return reports_dir
