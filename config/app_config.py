# config/app_config.py

"""Application configuration settings"""

import os


class AppConfig:
    """Main application configuration"""

    # Application Information
    APP_NAME = "EDSI Veterinary Management System"
    APP_VERSION = "1.0.0"  # Will be updated as per main.py

    # Window Settings
    WINDOW_WIDTH = 1024
    WINDOW_HEIGHT = 768
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 600

    # --- Standard Light Theme Colors (Original) ---
    PRIMARY_COLOR = "#0078d4"
    SECONDARY_COLOR = "#6c757d"
    SUCCESS_COLOR = "#28a745"
    WARNING_COLOR = "#ffc107"
    DANGER_COLOR = "#dc3545"
    BACKGROUND_COLOR = "#f8f9fa"  # Main window background for light theme
    SURFACE_COLOR = "#ffffff"  # Cards/panels background for light theme
    TEXT_COLOR = "#212529"  # Default text for light theme
    TEXT_SECONDARY = "#6c757d"  # Secondary text for light theme

    # --- Dark Theme Color Palette (New - Centralized) ---
    DARK_BACKGROUND = "#1e1e1e"  # Deepest background (e.g., main window)
    DARK_WIDGET_BACKGROUND = (
        "#2b2b2b"  # Background for panels, lists, dialogs, tab content
    )
    DARK_INPUT_FIELD_BACKGROUND = "#252525"  # Slightly different for input fields
    DARK_HEADER_FOOTER = "#2d2d2d"  # For headers, footers, status bars
    DARK_BORDER = "#444444"  # Borders for widgets, lines
    DARK_TEXT_PRIMARY = "#e0e0e0"  # Primary text color
    DARK_TEXT_SECONDARY = "#a0a0a0"  # Secondary text (labels, less important info)
    DARK_TEXT_TERTIARY = "#808080"  # Tertiary text (placeholders, disabled text)
    DARK_ITEM_HOVER = "#3a3a3a"  # Hover state for list items, buttons
    DARK_BUTTON_BG = "#444444"  # Default button background
    DARK_BUTTON_HOVER = "#555555"  # Button hover
    DARK_PRIMARY_ACTION = "#3498db"  # Bright blue for primary actions
    DARK_SUCCESS_ACTION = "#28a745"  # Green for success
    DARK_WARNING_ACTION = "#ffc107"  # Yellow for warnings
    DARK_DANGER_ACTION = "#dc3545"  # Red for danger/delete
    DARK_HIGHLIGHT_BG = (
        "#3498db"  # For selected items background (can be same as primary action)
    )
    DARK_HIGHLIGHT_TEXT = "#ffffff"  # Text on highlighted background

    # Fonts
    DEFAULT_FONT_FAMILY = "Arial"  # Consider "Segoe UI" for Windows if available
    DEFAULT_FONT_SIZE = 10  # Points
    HEADING_FONT_SIZE = 14
    SMALL_FONT_SIZE = 8
    MONO_FONT_FAMILY = "Consolas"

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
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def get_database_path():
        return os.path.join(AppConfig.get_app_dir(), "edsi_database.db")

    @staticmethod
    def get_logs_dir():
        logs_dir = os.path.join(AppConfig.get_app_dir(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir

    @staticmethod
    def get_reports_dir():
        reports_dir = os.path.join(AppConfig.get_app_dir(), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        return reports_dir

    @staticmethod
    def get_assets_dir():
        assets_dir = os.path.join(AppConfig.get_app_dir(), "assets")
        os.makedirs(assets_dir, exist_ok=True)  # Ensure it exists
        return assets_dir
