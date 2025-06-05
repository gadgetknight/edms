import os
import datetime

# --- Configuration ---
PROJECT_BASE_PATH = r"C:\projects\edms"
OUTPUT_FILE_NAME = "edms_core_files_for_ai.txt"

# List of files to collect. Paths are relative to PROJECT_BASE_PATH
# Add or remove files as needed.
FILES_TO_COLLECT = [
    # Models
    "models/base_model.py",
    "models/horse_models.py",
    "models/owner_models.py",
    "models/reference_models.py", # Should contain ChargeCode, ChargeCodeCategory
    "models/user_models.py",
    "models/invoice_model.py", # If you have a separate invoice model
    "models/financial_models.py", # If you have other financial models

    # Controllers
    "controllers/horse_controller.py", # Example controller
    # "controllers/financial_controller.py", # If it already exists

    # Config
    "config/database_config.py",
    "config/app_config.py", # Might be useful for context

    # Views (Examples for UI structure and for the screen to be modified)
    "views/horse/horse_unified_management.py",
    "views/admin/dialogs/add_edit_charge_code_dialog.py", # Or another representative dialog
    "views/horse/dialogs/create_link_owner_dialog.py", # Example of a horse-related dialog
    "views/horse/tabs/basic_info_tab.py", # Or another representative tab from HorseUnifiedManagement
    "views/horse/tabs/owners_tab.py",    # Example tab
    "views/horse/tabs/location_tab.py",  # Example tab

    # Main application file (for overall structure context if needed)
    "main.py"
]
# --- End Configuration ---

def collect_files():
    """
    Collects the content of specified project files into a single output file.
    """
    output_content = []
    missing_files = []
    collected_files_count = 0

    output_content.append(f"EDMS Project Files Dump\n")
    output_content.append(f"Collected on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output_content.append(f"Project Base Path: {PROJECT_BASE_PATH}\n")
    output_content.append("=" * 80 + "\n\n")

    for relative_path in FILES_TO_COLLECT:
        full_path = os.path.join(PROJECT_BASE_PATH, relative_path.replace("/", os.sep))
        output_content.append(f"--- File: {relative_path} ---\n")
        
        if os.path.exists(full_path) and os.path.isfile(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    output_content.append(content)
                output_content.append(f"\n--- End File: {relative_path} ---\n\n")
                collected_files_count += 1
                print(f"Successfully collected: {relative_path}")
            except Exception as e:
                output_content.append(f"*** Error reading file {relative_path}: {e} ***\n\n")
                print(f"Error reading file {relative_path}: {e}")
                missing_files.append(f"{relative_path} (Error reading)")
        else:
            output_content.append(f"*** File not found: {relative_path} ***\n\n")
            print(f"File not found: {relative_path}")
            missing_files.append(f"{relative_path} (Not found)")

    output_file_path = os.path.join(os.getcwd(), OUTPUT_FILE_NAME) # Save in the same dir as script
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write("".join(output_content))
        print(f"\nSuccessfully wrote {collected_files_count} file(s) to: {output_file_path}")
        if missing_files:
            print("\nCould not find or access the following files:")
            for mf in missing_files:
                print(f"- {mf}")
    except Exception as e:
        print(f"\nError writing output file {output_file_path}: {e}")

if __name__ == "__main__":
    if not os.path.isdir(PROJECT_BASE_PATH):
        print(f"Error: Project base path '{PROJECT_BASE_PATH}' does not exist or is not a directory.")
        print("Please check the PROJECT_BASE_PATH variable in the script.")
    else:
        collect_files()
