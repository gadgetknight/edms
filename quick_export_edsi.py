#!/usr/bin/env python3
"""
Quick EDSI Export Script

A simple script to export all EDSI Python files to a single text file.
Version: 1.0.0
Last Updated: May 12, 2025
"""

import os
from datetime import datetime


def create_edsi_export():
    """Export all EDSI Python files to edsi_all_code.txt"""

    # Define the files we want to export in order
    files_to_export = [
        # Core application
        "main.py",
        # Configuration
        "config/__init__.py",
        "config/app_config.py",
        "config/database_config.py",
        # Models
        "models/__init__.py",
        "models/base_model.py",
        "models/user_models.py",
        "models/reference_models.py",
        "models/horse_models.py",
        "models/owner_models.py",
        # Controllers
        "controllers/__init__.py",
        "controllers/horse_controller.py",
        # Base view
        "views/__init__.py",
        "views/base_view.py",
        # Authentication views
        "views/auth/splash_screen.py",
        "views/auth/login_screen.py",
        # Main menu
        "views/main_menu.py",
        # Horse views
        "views/horse/__init__.py",
        "views/horse/horse_unified_management.py",
        # Requirements
        "requirements.txt",
    ]

    output_file = "edsi_all_code.txt"

    with open(output_file, "w", encoding="utf-8") as outfile:
        # Header
        outfile.write("EDSI Veterinary Management System - Complete Code Export\n")
        outfile.write("=" * 70 + "\n")
        outfile.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        outfile.write(f"Total Files: {len(files_to_export)}\n")
        outfile.write("=" * 70 + "\n\n")

        # Export each file
        for i, file_path in enumerate(files_to_export, 1):
            outfile.write(f"\n{'='*80}\n")
            outfile.write(f"FILE {i}/{len(files_to_export)}: {file_path}\n")
            outfile.write(f"{'='*80}\n\n")

            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as infile:
                        content = infile.read()
                        outfile.write(content)
                        if not content.endswith("\n"):
                            outfile.write("\n")
                except Exception as e:
                    outfile.write(f"ERROR: Could not read {file_path}: {e}\n")
            else:
                outfile.write(f"ERROR: File not found: {file_path}\n")

            outfile.write(f"\n{'='*80}\n")
            outfile.write(f"END OF {file_path}\n")
            outfile.write(f"{'='*80}\n\n")

    print(f"Export complete! All EDSI Python files saved to: {output_file}")
    print(f"File size: {os.path.getsize(output_file):,} bytes")
    print("\nFiles exported:")
    for file_path in files_to_export:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (not found)")


if __name__ == "__main__":
    print("EDSI Code Export Starting...")
    create_edsi_export()
    print("Done!")
