# config/config_manager.py

"""
EDSI Veterinary Management System - Configuration Manager
Version: 1.0.3
Purpose: Manages user-configurable application paths for database, invoices, statements, and accounting reports.
         Uses a configuration file for persistent storage of these paths.
Last Updated: June 29, 2025
Author: Gemini

Changelog:
- v1.0.3 (2025-06-29):
    - Added `ACCOUNTING_REPORTS_DIR_KEY` constant to define the key for the new
      configurable path for accounting reports.
- v1.0.2 (2025-06-23):
    - **BUG FIX:** Added missing class attribute `ASSETS_DIR_KEY` to the `ConfigManager` class.
      Ensured all path keys (`DB_PATH_KEY`, `LOG_DIR_KEY`, `INVOICES_DIR_KEY`, `STATEMENTS_DIR_KEY`)
      are explicitly defined as class attributes. This resolves the `AttributeError` for `ASSETS_DIR_KEY`.
- v1.0.1 (2025-06-23):
    - **BUG FIX:** Added missing class attributes `DB_PATH_KEY`, `LOG_DIR_KEY`,
      `INVOICES_DIR_KEY`, and `STATEMENTS_DIR_KEY` to the `ConfigManager` class.
      This resolves the `AttributeError: type object 'ConfigManager' has no attribute 'LOG_DIR_KEY'`.
- v1.0.0 (2025-06-23):
    - Initial creation of the ConfigManager class.
    - Implemented methods to load, save, get, and set user-configurable paths.
    - Uses 'config.ini' file for persistence in the user's home directory.
"""

import os
import configparser
import logging
from typing import Optional


class ConfigManager:
    """
    Manages user-configurable application paths (database, invoices, statements).
    Loads configuration from and saves to a 'config.ini' file.
    """

    # Define configuration keys for paths (FIXED: All keys are now present)
    DB_PATH_KEY = "database_path"
    LOG_DIR_KEY = "logs_directory"
    ASSETS_DIR_KEY = "assets_directory"
    INVOICES_DIR_KEY = "invoices_directory"
    STATEMENTS_DIR_KEY = "statements_directory"
    ACCOUNTING_REPORTS_DIR_KEY = (
        "accounting_reports_directory"  # NEW: Key for accounting reports directory
    )

    # Define the default configuration file name
    CONFIG_FILE_NAME = "edms_config.ini"

    def __init__(self):
        """
        Initializes the ConfigManager, setting up the logger and determining
        the path to the configuration file.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        # Store config file in a user-specific and OS-appropriate location
        self.config_file_path = self._get_config_file_path()
        self.config = configparser.ConfigParser()
        self._load_config()

    def _get_config_file_path(self) -> str:
        """
        Determines the appropriate path for the configuration file based on the OS.
        For Windows, it uses APPDATA; for Linux/macOS, it uses ~/.config or ~/.local/share.
        """
        if os.name == "nt":  # Windows
            app_config_dir = os.path.join(
                os.environ.get("APPDATA", os.path.expanduser("~")), "EDMS"
            )
        else:  # Linux, macOS, etc.
            app_config_dir = os.path.join(os.path.expanduser("~"), ".config", "EDMS")

        # Ensure the directory exists
        os.makedirs(app_config_dir, exist_ok=True)

        return os.path.join(app_config_dir, self.CONFIG_FILE_NAME)

    def _load_config(self):
        """
        Loads the configuration from the INI file. If the file or section
        does not exist, it initializes with default (empty) values.
        """
        try:
            self.config.read(self.config_file_path)
            if "Paths" not in self.config:
                self.config["Paths"] = {}
                self.logger.info(
                    f"Initialized 'Paths' section in {self.config_file_path}."
                )
            self.logger.info(f"Configuration loaded from {self.config_file_path}.")
        except Exception as e:
            self.logger.error(
                f"Error loading configuration from {self.config_file_path}: {e}",
                exc_info=True,
            )
            # Ensure 'Paths' section exists even if loading fails
            if "Paths" not in self.config:
                self.config["Paths"] = {}

    def _save_config(self):
        """
        Saves the current configuration to the INI file.
        """
        try:
            with open(self.config_file_path, "w", encoding="utf-8") as configfile:
                self.config.write(configfile)
            self.logger.info(f"Configuration saved to {self.config_file_path}.")
        except Exception as e:
            self.logger.error(
                f"Error saving configuration to {self.config_file_path}: {e}",
                exc_info=True,
            )

    def get_path(self, key: str) -> Optional[str]:
        """
        Retrieves a configured path.

        Args:
            key (str): The key corresponding to the path (e.g., DB_PATH_KEY).

        Returns:
            Optional[str]: The configured path, or None if not set.
        """
        return self.config.get("Paths", key, fallback=None)

    def set_path(self, key: str, path: str):
        """
        Sets a configurable path and saves the configuration.

        Args:
            key (str): The key corresponding to the path.
            path (str): The path to set.
        """
        self.config["Paths"][key] = path
        self._save_config()
        self.logger.info(f"Path '{key}' set to '{path}' and saved.")


# Instantiate the ConfigManager to be used globally
config_manager = ConfigManager()
