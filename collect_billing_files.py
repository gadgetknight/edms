import os

def collect_project_files():
    """
    Collects the content of specified project files into a single text file.
    """
    # Define the root path of your project
    base_path = r"C:\Projects\EDMS"

    # List of relative file paths to be collected
    files_to_collect = [
        # Core Billing Modules
        "models/financial_models.py",
        "controllers/financial_controller.py",
        "views/horse/tabs/billing_tab.py",
        "views/horse/dialogs/add_charge_dialog.py",
        # Interacting Existing Modules
        "views/horse/horse_unified_management.py",
        # Supporting Models
        "models/horse_models.py",
        "models/owner_models.py",
        "models/reference_models.py",
        "models/user_models.py",
        # Configuration and Initialization
        "models/__init__.py",
        "config/database_config.py",
        "views/horse/tabs/__init__.py",
        "views/horse/dialogs/__init__.py",
    ]

    output_filename = "billing_module_dump.txt"

    print(f"Starting file collection into '{output_filename}'...")

    try:
        with open(output_filename, "w", encoding="utf-8") as outfile:
            for relative_path in files_to_collect:
                # Normalize path for the current OS
                full_path = os.path.join(base_path, os.path.normpath(relative_path))
                
                # Write a header for each file
                header = f"=============== FILE: {relative_path.replace('/', os.sep)} ===============\n\n"
                outfile.write(header)
                
                print(f"Processing: {full_path}")

                try:
                    with open(full_path, "r", encoding="utf-8") as infile:
                        outfile.write(infile.read())
                        outfile.write("\n\n")
                except FileNotFoundError:
                    error_msg = f"ERROR: File not found - {full_path}\n\n"
                    print(error_msg.strip())
                    outfile.write(error_msg)
                except Exception as e:
                    error_msg = f"ERROR: Could not read file {full_path}: {e}\n\n"
                    print(error_msg.strip())
                    outfile.write(error_msg)
            
            # Write an end-of-file marker for clarity
            outfile.write("=============== END OF DUMP ===============\n")

        print(f"\nSuccess! All specified files have been collected into '{output_filename}'.")
        print("Please upload this file in our next chat.")

    except Exception as e:
        print(f"\nAn error occurred while trying to create the output file: {e}")

if __name__ == "__main__":
    collect_project_files()