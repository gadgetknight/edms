# scripts/backup_data.py
"""
EDSI Veterinary Management System - Database Backup Utility
Version: 1.0.0
Purpose: Creates a backup of the entire SQLite database into an SQL text file.
Last Updated: June 10, 2025
Author: Gemini
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


def backup_database():
    """Connects to the database and dumps its content to a backup.sql file."""
    db_path = AppConfig.DATABASE_URL.split("///")[-1]
    backup_path = os.path.join(AppConfig.PROJECT_ROOT, "backup.sql")

    if not os.path.exists(db_path):
        print(f"Error: Database file not found at '{db_path}'. Cannot create backup.")
        return

    try:
        print(f"Backing up database from '{db_path}' to '{backup_path}'...")
        con = sqlite3.connect(db_path)
        with open(backup_path, "w", encoding="utf-8") as f:
            # iterdump() generates an SQL script from the database content
            for line in con.iterdump():
                f.write("%s\n" % line)
        con.close()
        print("\nDatabase backup completed successfully.")
        print(f"Data saved to: {backup_path}")

    except Exception as e:
        print(f"\nAn error occurred during backup: {e}")


if __name__ == "__main__":
    backup_database()
