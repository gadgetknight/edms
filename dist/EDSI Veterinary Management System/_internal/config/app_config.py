# config/app_config.py

"""
EDSI Veterinary Management System - Application Configuration
Version: 2.2.2
Purpose: Centralized configuration for application settings, paths, and constants.
         Now includes configurable path for accounting reports.
Last Updated: June 29, 2025
Author: Gemini

Changelog:
- v2.2.2 (2025-06-29):
    - Added `ACCOUNTING_REPORTS_DIR` constant, using `ConfigManager` for a user-configurable path
      with a fallback to a default project subdirectory.
    - Updated `ensure_directories()` to create the `ACCOUNTING_REPORTS_DIR`.
    - Added `get_accounting_reports_dir()` class method.
- v2.2.1 (2025-06-25):
    - Added new constants: `DOCTOR_STRIPE_PUBLISHABLE_KEY` and `DOCTOR_STRIPE_SECRET_KEY`
      as placeholders for the doctor's Stripe API keys, for use in payment integration.
- v2.2.0 (2025-06-23):
    - Integrated `config_manager` to allow user-configurable paths for:
        - `DATABASE_URL`
        - `LOG_DIR`
        - `ASSETS_DIR` (using relative fallback)
        - `INVOICES_DIR`
        - `STATEMENTS_DIR` (newly added configurable path)
    - Modified path constants to check `config_manager` first, then fallback to project defaults.
    - Updated `ensure_directories()` to create all managed directories.
- v2.1.0 (2025-06-09):
    - Added INVOICES_DIR path constant for storing generated invoice PDFs.
    - Updated ensure_directories() to create the 'invoices' folder on startup.
- v2.0.1 (2025-05-26):
    - Added LOG_MAX_BYTES and LOG_BACKUP_COUNT constants for log file rotation.
    - Included log_max_bytes and log_backup_count in the get_logging_config() dictionary.
    - Updated module-level APP_VERSION constant to "2.0.3" to align with main application.
- v2.0.0 (2025-05-24):
    - Complete rewrite for Phase 1 (Chunk 1) simplification
    - Consolidated all configuration into single AppConfig class
"""

import os
import logging
from typing import Dict, Any

# Import the new ConfigManager for user-configurable paths
from config.config_manager import config_manager, ConfigManager

# --- Core Project Path (always relative to app_config.py location) ---
# This remains the absolute base for default fallbacks
_BASE_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# --- Application Information ---
APP_NAME = "EDSI Veterinary Management System"
APP_VERSION = "2.0.3"
APP_AUTHOR = "EDSI"

# --- Database Configuration ---
# Prioritize user-defined DB path, fallback to project root default
_DEFAULT_DB_PATH = os.path.join(_BASE_PROJECT_ROOT, "edsi_database.db")
DATABASE_URL = f"sqlite:///{config_manager.get_path(ConfigManager.DB_PATH_KEY) or _DEFAULT_DB_PATH}"

# --- Paths (User-configurable with fallbacks) ---
# Prioritize user-defined paths, fallback to project root defaults
PROJECT_ROOT = _BASE_PROJECT_ROOT  # This refers to the application's installed root
LOG_DIR = config_manager.get_path(ConfigManager.LOG_DIR_KEY) or os.path.join(
    _BASE_PROJECT_ROOT, "logs"
)
ASSETS_DIR = config_manager.get_path(ConfigManager.ASSETS_DIR_KEY) or os.path.join(
    _BASE_PROJECT_ROOT, "assets"
)
INVOICES_DIR = config_manager.get_path(ConfigManager.INVOICES_DIR_KEY) or os.path.join(
    _BASE_PROJECT_ROOT, "invoices"
)
STATEMENTS_DIR = config_manager.get_path(
    ConfigManager.STATEMENTS_DIR_KEY
) or os.path.join(_BASE_PROJECT_ROOT, "statements")

# NEW: Accounting Reports Directory
ACCOUNTING_REPORTS_DIR = config_manager.get_path(
    ConfigManager.ACCOUNTING_REPORTS_DIR_KEY
) or os.path.join(_BASE_PROJECT_ROOT, "reports", "accounting")


# --- Logging Configuration (uses LOG_DIR defined above) ---
APP_LOG_FILE = os.path.join(LOG_DIR, "edsi_app.log")
DB_LOG_FILE = os.path.join(LOG_DIR, "edsi_db.log")
LOGGING_LEVEL = logging.INFO
LOG_MAX_BYTES = 1024 * 1024 * 5
LOG_BACKUP_COUNT = 5

# --- UI Configuration ---
DEFAULT_FONT_FAMILY = "Inter"
DEFAULT_FONT_SIZE = 10
SMALL_FONT_SIZE = 9
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 700

# --- Dark Theme Colors (Essential Only) ---
DARK_BACKGROUND = "#2D3748"
DARK_WIDGET_BACKGROUND = "#1A202C"
DARK_HEADER_FOOTER = "#222B38"
DARK_BORDER = "#4A5568"
DARK_TEXT_PRIMARY = "#E2E8F0"
DARK_TEXT_SECONDARY = "#A0AEC0"
DARK_TEXT_TERTIARY = "#718096"
DARK_PRIMARY_ACTION = "#3182CE"
DARK_SUCCESS_ACTION = "#38A169"
DARK_WARNING_ACTION = "#DD6B20"
DARK_DANGER_ACTION = "#E53E3E"
DARK_BUTTON_BG = "#4A5568"
DARK_BUTTON_HOVER = "#718096"
DARK_ITEM_HOVER = "#2C3543"
DARK_HIGHLIGHT_BG = "#3182CE"
DARK_HIGHLIGHT_TEXT = "#FFFFFF"
DARK_INPUT_FIELD_BACKGROUND = "#222B38"

# --- NEW: Stripe API Keys for Doctor's Payments (PLACEHOLDERS) ---
# These keys are specific to the doctor's Stripe account (your end-user).
# They will be read by the desktop application and sent to your centralized backend API.
# REPLACE THESE WITH YOUR ACTUAL TEST KEYS FOR TESTING,
# but in a production environment, these should be securely configurable by the user (doctor)
# within the app's settings, and persisted (e.g., in the database for their user account).
DOCTOR_STRIPE_PUBLISHABLE_KEY = "pk_test_51Rc7TLBAHovgkmZiZaCPLCiludBNc4NI8ZmQqlEpyeXNgJ0Vndnla7mXcie7HLxeEyrmBRz4CrjiUcXYlFuFOLDR00k4nIZjGr"
DOCTOR_STRIPE_SECRET_KEY = "sk_test_51Rc7TLBAHovgkmZipgbbrO3O8xg1HwhIxzNSmhlH8tP76L04TTBv4JURXf5jyJceNQGrtSz88zzeafwnmzdW04Jr000oPQqWuc"


class AppConfig:
    """
    Centralized application configuration class.
    Provides clean access to all application settings.
    """

    # Application Info
    APP_NAME = APP_NAME
    APP_VERSION = APP_VERSION
    APP_AUTHOR = APP_AUTHOR

    # Paths
    PROJECT_ROOT = PROJECT_ROOT
    LOG_DIR = LOG_DIR
    ASSETS_DIR = ASSETS_DIR
    INVOICES_DIR = INVOICES_DIR
    STATEMENTS_DIR = STATEMENTS_DIR
    ACCOUNTING_REPORTS_DIR = ACCOUNTING_REPORTS_DIR  # NEW: Added to AppConfig class

    # Database
    DATABASE_URL = DATABASE_URL

    # Logging
    APP_LOG_FILE = APP_LOG_FILE
    DB_LOG_FILE = DB_LOG_FILE
    LOGGING_LEVEL = LOGGING_LEVEL
    LOG_MAX_BYTES = LOG_MAX_BYTES
    LOG_BACKUP_COUNT = LOG_BACKUP_COUNT

    # UI Settings
    DEFAULT_FONT_FAMILY = DEFAULT_FONT_FAMILY
    DEFAULT_FONT_SIZE = DEFAULT_FONT_SIZE
    SMALL_FONT_SIZE = SMALL_FONT_SIZE
    MIN_WINDOW_WIDTH = MIN_WINDOW_WIDTH
    MIN_WINDOW_HEIGHT = MIN_WINDOW_HEIGHT

    # Theme Colors
    DARK_BACKGROUND = DARK_BACKGROUND
    DARK_WIDGET_BACKGROUND = DARK_WIDGET_BACKGROUND
    DARK_HEADER_FOOTER = DARK_HEADER_FOOTER
    DARK_BORDER = DARK_BORDER
    DARK_TEXT_PRIMARY = DARK_TEXT_PRIMARY
    DARK_TEXT_SECONDARY = DARK_TEXT_SECONDARY
    DARK_TEXT_TERTIARY = DARK_TEXT_TERTIARY
    DARK_PRIMARY_ACTION = DARK_PRIMARY_ACTION
    DARK_SUCCESS_ACTION = DARK_SUCCESS_ACTION
    DARK_WARNING_ACTION = DARK_WARNING_ACTION
    DARK_DANGER_ACTION = DARK_DANGER_ACTION
    DARK_BUTTON_BG = DARK_BUTTON_BG
    DARK_BUTTON_HOVER = DARK_BUTTON_HOVER
    DARK_ITEM_HOVER = DARK_ITEM_HOVER
    DARK_HIGHLIGHT_BG = DARK_HIGHLIGHT_BG
    DARK_HIGHLIGHT_TEXT = DARK_HIGHLIGHT_TEXT
    DARK_INPUT_FIELD_BACKGROUND = DARK_INPUT_FIELD_BACKGROUND

    # NEW: Doctor's Stripe API Keys
    DOCTOR_STRIPE_PUBLISHABLE_KEY = DOCTOR_STRIPE_PUBLISHABLE_KEY
    DOCTOR_STRIPE_SECRET_KEY = DOCTOR_STRIPE_SECRET_KEY

    @classmethod
    def get_database_url(cls) -> str:
        return cls.DATABASE_URL

    @classmethod
    def get_app_dir(cls) -> str:
        return cls.PROJECT_ROOT

    @classmethod
    def get_assets_dir(cls) -> str:
        return cls.ASSETS_DIR

    @classmethod
    def get_invoices_dir(cls) -> str:
        return cls.INVOICES_DIR

    @classmethod
    def get_statements_dir(cls) -> str:
        return cls.STATEMENTS_DIR

    @classmethod
    def get_accounting_reports_dir(
        cls,
    ) -> str:  # NEW: Getter for accounting reports directory
        return cls.ACCOUNTING_REPORTS_DIR

    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "level": cls.LOGGING_LEVEL,
            "app_log_file": os.path.join(cls.LOG_DIR, "edsi_app.log"),
            "db_log_file": os.path.join(cls.LOG_DIR, "edsi_db.log"),
            "log_dir": cls.LOG_DIR,
            "log_max_bytes": cls.LOG_MAX_BYTES,
            "log_backup_count": cls.LOG_BACKUP_COUNT,
        }

    @classmethod
    def get_ui_config(cls) -> Dict[str, Any]:
        return {
            "font_family": cls.DEFAULT_FONT_FAMILY,
            "font_size": cls.DEFAULT_FONT_SIZE,
            "small_font_size": cls.SMALL_FONT_SIZE,
            "min_window_width": cls.MIN_WINDOW_WIDTH,
            "min_window_height": cls.MIN_WINDOW_HEIGHT,
        }

    @classmethod
    def get_theme_colors(cls) -> Dict[str, str]:
        return {
            "background": cls.DARK_BACKGROUND,
            "widget_background": cls.DARK_WIDGET_BACKGROUND,
            "header_footer": cls.DARK_HEADER_FOOTER,
            "border": cls.DARK_BORDER,
            "text_primary": cls.DARK_TEXT_PRIMARY,
            "text_secondary": cls.DARK_TEXT_SECONDARY,
            "text_tertiary": cls.DARK_TEXT_TERTIARY,
            "primary_action": cls.DARK_PRIMARY_ACTION,
            "success_action": cls.DARK_SUCCESS_ACTION,
            "warning_action": cls.DARK_WARNING_ACTION,
            "danger_action": cls.DARK_DANGER_ACTION,
            "button_bg": cls.DARK_BUTTON_BG,
            "button_hover": DARK_BUTTON_HOVER,
            "item_hover": DARK_ITEM_HOVER,
            "highlight_bg": DARK_HIGHLIGHT_BG,
            "highlight_text": DARK_HIGHLIGHT_TEXT,
            "input_field_background": DARK_INPUT_FIELD_BACKGROUND,
        }

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure required directories exist, including user-configurable ones."""
        directories = [
            cls.LOG_DIR,
            cls.ASSETS_DIR,
            cls.INVOICES_DIR,
            cls.STATEMENTS_DIR,
            cls.ACCOUNTING_REPORTS_DIR,  # NEW: Ensure accounting reports directory exists
        ]

        for directory in directories:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                    logging.info(f"Created directory: {directory}")
                except OSError as e:
                    logging.error(f"Failed to create directory {directory}: {e}")
