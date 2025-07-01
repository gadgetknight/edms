# scripts/restore_data.py
"""
EDSI Veterinary Management System - Database Restore Utility
Version: 1.1.0
Purpose: Restores data from a backup.sql file into the SQLite database.
Last Updated: June 10, 2025
Author: Gemini

Changelog:
- v1.1.0 (2025-06-10):
    - Made the script more robust by wrapping the restore commands in a
      transaction and disabling foreign key checks during the import. This
      prevents errors related to table creation order and data dependencies.
- v1.0.0 (2025-06-10):
    - Initial implementation.
"""
import sqlite3
import os
import sys

# This allows the script to find the 'config' module
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

try:
    from config.app_config import AppConfig
except ImportError:
    print(
        "Error: Could not import AppConfig. Make sure the script is run from the project root directory."
    )
    sys.exit(1)


def restore_database():
    """Connects to the database and restores data from the backup.sql file."""
    db_path = AppConfig.DATABASE_URL.split("///")[-1]
    backup_path = os.path.join(AppConfig.PROJECT_ROOT, "backup.sql")

    if not os.path.exists(backup_path):
        print(f"Error: Backup file not found at '{backup_path}'. Cannot restore.")
        return

    if not os.path.exists(db_path):
        print(f"Warning: Database file not found at '{db_path}'.")
        print("A new empty database will be created for the restore process.")
        # This is expected behavior, as the user should delete the old DB first.

    try:
        print(f"Restoring database from '{backup_path}' to '{db_path}'...")
        con = sqlite3.connect(db_path)
        cursor = con.cursor()
        with open(backup_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        # Wrap the script execution to disable foreign keys, which prevents errors
        # with out-of-order data insertion. This makes the restore much safer.
        wrapper_script = f"""
        PRAGMA foreign_keys = OFF;
        BEGIN TRANSACTION;
        {sql_script}
        COMMIT;
        PRAGMA foreign_keys = ON;
        """

        # executescript can run a string containing multiple SQL statements
        cursor.executescript(wrapper_script)

        con.commit()
        con.close()
        print("\nDatabase restore completed successfully.")
        print("Your test data should now be available.")

    except Exception as e:
        print(f"\nAn error occurred during restore: {e}")


if __name__ == "__main__":
    restore_database()
