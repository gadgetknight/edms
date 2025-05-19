# config/app_config.py

"""
EDSI Veterinary Management System - Application Configuration
Version: 1.1.1
Purpose: Centralized configuration for application settings, paths, and constants.
         Added missing window size and font size constants.
Last Updated: May 18, 2025
Author: Claude Assistant

Changelog:
- v1.1.1 (2025-05-18):
    - Added MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT.
    - Added DEFAULT_FONT_SIZE, SMALL_FONT_SIZE.
- v1.1.0 (2025-05-17): Added get_database_url() function.
- v1.0.0 (2025-05-12): Initial version with paths and theme colors.
"""

import os
import logging
import sys  # Added for stderr print in case of log dir creation error
from dotenv import load_dotenv

# --- Path Configuration ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path)

# --- Logging Configuration ---
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
APP_LOG_FILE = os.path.join(LOG_DIR, "edsi_app.log")
DB_LOG_FILE = os.path.join(LOG_DIR, "edsi_db.log")

if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except OSError as e:
        print(f"Error creating log directory {LOG_DIR}: {e}", file=sys.stderr)

LOGGING_LEVEL = logging.INFO

# --- Database Configuration ---
DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(PROJECT_ROOT, 'edsi_database.db')}"
)
print(f"Database URL set to: {DATABASE_URL}")


def get_database_url():
    """Returns the configured DATABASE_URL."""
    return DATABASE_URL


# --- Application Information ---
APP_NAME = "EDSI Veterinary Management System"
APP_VERSION = "1.3.1"  # Match version in main.py if it's also there
APP_AUTHOR = "GadgetKnight"

# --- UI Configuration ---
DEFAULT_FONT_FAMILY = "Inter"
# --- ADDED MISSING CONSTANTS ---
DEFAULT_FONT_SIZE = 10  # Default font size in points
SMALL_FONT_SIZE = 9  # Smaller font size for things like status bars
MIN_WINDOW_WIDTH = 900  # Minimum window width for BaseView
MIN_WINDOW_HEIGHT = 700  # Minimum window height for BaseView
# --- END ADDED ---

# Centralized Dark Theme Colors (Hex Codes)
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
DARK_HIGHLIGHT_BG = DARK_PRIMARY_ACTION  # Use primary action for highlight
DARK_HIGHLIGHT_TEXT = "#FFFFFF"
DARK_INPUT_FIELD_BACKGROUND = "#222B38"
DARK_TOOLTIP_BASE = DARK_WIDGET_BACKGROUND  # Added for BaseView palette
DARK_TOOLTIP_TEXT = DARK_TEXT_PRIMARY  # Added for BaseView palette


class AppConfig:
    """
    Provides methods to access application configuration settings.
    """

    @staticmethod
    def get_app_dir() -> str:
        return PROJECT_ROOT

    @staticmethod
    def get_assets_dir() -> str:
        return os.path.join(PROJECT_ROOT, "assets")

    @staticmethod
    def get_logging_config() -> dict:
        return {
            "level": LOGGING_LEVEL,
            "app_log_file": APP_LOG_FILE,
            "db_log_file": DB_LOG_FILE,
            "log_dir": LOG_DIR,
        }

    @staticmethod
    def get_app_info() -> dict:
        return {"name": APP_NAME, "version": APP_VERSION, "author": APP_AUTHOR}
