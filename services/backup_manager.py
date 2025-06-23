# services/backup_manager.py
"""
EDSI Veterinary Management System - Backup Manager Service
Version: 1.0.2
Purpose: Provides core functionality for backing up and restoring application data.
         Handles the database file and configurable data directories (invoices, statements).
Last Updated: June 23, 2025
Author: Gemini

Changelog:
- v1.0.2 (2025-06-23):
    - Resolved `sqlite3.OperationalError: cannot start a transaction within a transaction` during database restore.
    - Removed explicit `BEGIN TRANSACTION;` and `COMMIT;` from the SQL script wrapper in `restore_backup` to prevent nested transactions.
    - Ensured `PRAGMA foreign_keys = OFF;` and `PRAGMA foreign_keys = ON;` are used during SQL script execution for safe data loading.
- v1.0.1 (2025-06-23):
    - Corrected database access calls from `db_manager.get_session()` to `db_manager().get_session()`
      and `db_manager.close()` to `db_manager().close()` to align with the updated `DatabaseManager` singleton access pattern.
- v1.0.0 (2025-06-23):
    - Initial creation of the BackupManager class.
    - Implemented `create_backup` method to:
        - Dump the SQLite database to an SQL file.
        - Copy specified data directories (invoices, statements, logs, config) to a timestamped backup folder.
    - Implemented `restore_backup` method (placeholder for now, will be detailed later).
    - Uses `AppConfig` and `ConfigManager` to determine source paths.
    - Provides error handling and logging for backup operations.
"""

import os
import shutil
import datetime
import sqlite3
import logging
from typing import Tuple, List, Optional  # Removed unused List, Optional imports.

# Note: sys import is not directly needed in this file for v1.0.0 through v1.0.2 structure.
# If it were, it would be added.

from config.app_config import AppConfig
from config.config_manager import config_manager  # Removed unused ConfigManager import
from config.database_config import db_manager  # Import db_manager function


class BackupManager:
    """
    Manages the backup and restoration of EDSI application data.
    This includes the SQLite database, user-defined invoice and statement directories,
    and the application's configuration file.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_current_paths(self) -> dict:
        """
        Retrieves the currently configured paths from AppConfig, which in turn
        gets them from ConfigManager or falls back to defaults.
        """
        # Note: AppConfig.get_database_url() returns 'sqlite:///path', so replace prefix
        db_path = AppConfig.get_database_url().replace("sqlite:///", "")
        log_dir = AppConfig.get_logging_config()["log_dir"]
        invoices_dir = AppConfig.get_invoices_dir()
        statements_dir = AppConfig.get_statements_dir()

        # Get the path where the config file itself is stored by ConfigManager
        config_file_dir = os.path.dirname(config_manager.config_file_path)
        config_file_name = os.path.basename(config_manager.config_file_path)

        return {
            "db_path": db_path,
            "log_dir": log_dir,
            "invoices_dir": invoices_dir,
            "statements_dir": statements_dir,
            "config_file_dir": config_file_dir,  # Directory containing the config.ini
            "config_file_name": config_file_name,  # Name of the config.ini file
        }

    def create_backup(
        self, backup_destination_root: str, current_user_id: str
    ) -> Tuple[bool, str]:
        """
        Creates a full backup of the EDSI application data.

        Args:
            backup_destination_root (str): The root directory where the backup folder will be created.
                                           e.g., C:/Users/User/Documents/EDMS_Backups
            current_user_id (str): The ID of the user initiating the backup for logging/auditing.

        Returns:
            Tuple[bool, str]: A tuple indicating success (True/False) and a message.
        """
        if not os.path.isdir(backup_destination_root):
            try:
                os.makedirs(backup_destination_root, exist_ok=True)
                self.logger.info(
                    f"Created backup destination root: {backup_destination_root}"
                )
            except OSError as e:
                self.logger.error(
                    f"Failed to create backup destination root '{backup_destination_root}': {e}"
                )
                return False, f"Failed to create backup destination: {e}"

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder_name = f"EDMS_Backup_{timestamp}"
        full_backup_path = os.path.join(backup_destination_root, backup_folder_name)

        try:
            os.makedirs(full_backup_path, exist_ok=True)
            self.logger.info(
                f"Starting backup to: {full_backup_path} by user: {current_user_id}"
            )

            paths = self._get_current_paths()
            db_path = paths["db_path"]
            log_dir = paths["log_dir"]
            invoices_dir = paths["invoices_dir"]
            statements_dir = paths["statements_dir"]
            config_file_dir = paths["config_file_dir"]
            config_file_name = paths["config_file_name"]

            # --- 1. Backup Database (SQL dump) ---
            db_backup_file = os.path.join(full_backup_path, "edsi_database_dump.sql")
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    with open(db_backup_file, "w", encoding="utf-8") as f:
                        for line in conn.iterdump():
                            f.write(f"{line}\n")
                    conn.close()
                    self.logger.info(
                        f"Database dumped successfully to {db_backup_file}"
                    )
                except Exception as e:
                    self.logger.error(f"Failed to dump database: {e}")
                    return False, f"Failed to backup database: {e}"
            else:
                self.logger.warning(
                    f"Database file not found at '{db_path}'. Skipping database backup."
                )
                # Don't fail the whole backup if DB isn't there, just warn.

            # --- 2. Backup Data Directories (copy entire folders) ---
            directories_to_backup = [
                (invoices_dir, "invoices"),
                (statements_dir, "statements"),
                (log_dir, "logs"),
            ]

            for src_dir, dest_name in directories_to_backup:
                dest_path = os.path.join(full_backup_path, dest_name)
                if os.path.isdir(src_dir):
                    try:
                        shutil.copytree(src_dir, dest_path, dirs_exist_ok=True)
                        self.logger.info(
                            f"Copied directory '{src_dir}' to '{dest_path}'"
                        )
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to copy directory '{src_dir}' to backup: {e}"
                        )
                        # Don't fail the entire backup for one directory, just log warning
                else:
                    self.logger.warning(
                        f"Source directory '{src_dir}' not found. Skipping backup of '{dest_name}'."
                    )

            # --- 3. Backup Configuration File ---
            config_src_path = os.path.join(config_file_dir, config_file_name)
            config_dest_path = os.path.join(full_backup_path, config_file_name)
            if os.path.isfile(config_src_path):
                try:
                    shutil.copy2(config_src_path, config_dest_path)
                    self.logger.info(
                        f"Copied config file '{config_src_path}' to '{config_dest_path}'"
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to copy config file '{config_src_path}' to backup: {e}"
                    )
            else:
                self.logger.warning(
                    f"Config file '{config_src_path}' not found. Skipping config file backup."
                )

            self.logger.info(f"Full backup successfully created at: {full_backup_path}")
            return True, f"Backup created successfully at: {full_backup_path}"

        except Exception as e:
            self.logger.critical(
                f"An unexpected error occurred during backup creation: {e}",
                exc_info=True,
            )
            # Clean up incomplete backup folder if error occurs
            if os.path.exists(full_backup_path):
                try:
                    shutil.rmtree(full_backup_path)
                    self.logger.info(
                        f"Cleaned up incomplete backup folder: {full_backup_path}"
                    )
                except Exception as cleanup_e:
                    self.logger.error(
                        f"Failed to clean up incomplete backup folder: {cleanup_e}"
                    )
            return False, f"An error occurred during backup: {e}"

    def restore_backup(
        self, backup_source_path: str, current_user_id: str
    ) -> Tuple[bool, str]:
        """
        Restores data from a previously created backup folder.

        Args:
            backup_source_path (str): The full path to the backup folder (e.g., EDMS_Backup_YYYYMMDD_HHMMSS).
            current_user_id (str): The ID of the user initiating the restore.

        Returns:
            Tuple[bool, str]: A tuple indicating success (True/False) and a message.
        """
        self.logger.info(
            f"Starting restore from: {backup_source_path} by user: {current_user_id}"
        )

        if not os.path.isdir(backup_source_path):
            self.logger.error(f"Backup source path not found: {backup_source_path}")
            return False, f"Backup source folder not found: {backup_source_path}"

        try:
            paths = self._get_current_paths()
            db_path = paths["db_path"]
            log_dir = paths["log_dir"]
            invoices_dir = paths["invoices_dir"]
            statements_dir = paths["statements_dir"]
            config_file_dir = paths["config_file_dir"]
            config_file_name = paths["config_file_name"]

            # --- IMPORTANT: Warn user about data loss and recommend backup first ---
            # This logic should be in the UI calling this method, not here.
            # This method assumes the user has already confirmed irreversible action.

            # --- 1. Restore Database ---
            db_sql_backup_file = os.path.join(
                backup_source_path, "edsi_database_dump.sql"
            )
            if os.path.isfile(db_sql_backup_file):
                self.logger.info(
                    f"Restoring database from {db_sql_backup_file} to {db_path}"
                )
                try:
                    # Close any active connections to the database before trying to overwrite/restore
                    # This is critical if the application's DBManager has an open connection.
                    db_manager().close()  # Close current active session/engine if any.

                    # Remove existing DB file before restore, if it exists
                    if os.path.exists(db_path):
                        os.remove(db_path)
                        self.logger.info(f"Removed existing database file: {db_path}")

                    # Ensure the directory for the target DB exists
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)

                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    with open(db_sql_backup_file, "r", encoding="utf-8") as f:
                        sql_script = f.read()

                    # Execute script with foreign key checks off for safety during restore
                    # Removed explicit BEGIN/COMMIT wrapper to avoid nested transaction error.
                    # The SQL dump itself should contain BEGIN/COMMIT.
                    cursor.executescript(
                        "PRAGMA foreign_keys = OFF;\n"
                        + sql_script
                        + "\nPRAGMA foreign_keys = ON;"
                    )

                    conn.commit()
                    conn.close()
                    self.logger.info("Database restored successfully.")
                except Exception as e:
                    self.logger.error(f"Failed to restore database: {e}", exc_info=True)
                    return False, f"Failed to restore database: {e}"
            else:
                self.logger.warning(
                    f"Database SQL dump not found in backup '{backup_source_path}'. Skipping database restore."
                )

            # --- 2. Restore Data Directories ---
            directories_to_restore = [
                ("invoices", invoices_dir),
                ("statements", statements_dir),
                ("logs", log_dir),
            ]

            for src_name, dest_dir in directories_to_restore:
                src_path = os.path.join(backup_source_path, src_name)
                if os.path.isdir(src_path):
                    self.logger.info(
                        f"Restoring directory '{src_path}' to '{dest_dir}'"
                    )
                    try:
                        # Remove existing destination content first to ensure a clean restore
                        if os.path.exists(dest_dir):
                            shutil.rmtree(dest_dir)
                            self.logger.info(
                                f"Removed existing directory '{dest_dir}' before restore."
                            )
                        # Create the destination directory before copying files into it
                        os.makedirs(dest_dir, exist_ok=True)
                        shutil.copytree(src_path, dest_dir, dirs_exist_ok=True)
                        self.logger.info(
                            f"Restored directory '{src_path}' to '{dest_dir}' successfully."
                        )
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to restore directory '{src_path}': {e}"
                        )
                else:
                    self.logger.warning(
                        f"Directory '{src_path}' not found in backup. Skipping restore."
                    )

            # --- 3. Restore Configuration File ---
            config_backup_file = os.path.join(backup_source_path, config_file_name)
            config_dest_path = os.path.join(config_file_dir, config_file_name)

            if os.path.isfile(config_backup_file):
                self.logger.info(
                    f"Restoring config file from '{config_backup_file}' to '{config_dest_path}'"
                )
                try:
                    # Ensure the target directory for config file exists
                    os.makedirs(os.path.dirname(config_dest_path), exist_ok=True)
                    shutil.copy2(config_backup_file, config_dest_path)
                    self.logger.info("Configuration file restored successfully.")
                except Exception as e:
                    self.logger.warning(f"Failed to restore config file: {e}")
            else:
                self.logger.warning(
                    f"Config file not found in backup at '{config_backup_file}'. Skipping config file restore."
                )

            self.logger.info(
                f"Data restore from {backup_source_path} completed successfully."
            )
            return (
                True,
                "Data restored successfully. Please restart the application for changes to take full effect.",
            )

        except Exception as e:
            self.logger.critical(
                f"An unexpected error occurred during restore operation: {e}",
                exc_info=True,
            )
            return False, f"An error occurred during restore: {e}"


# Instantiate the BackupManager to be used globally
backup_manager = BackupManager()
