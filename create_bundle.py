import os

def bundle_project_files(base_path, file_paths, output_filename):
    """
    Reads specified project files and bundles their content into a single text file.

    Args:
        base_path (str): The absolute base path of the project directory.
        file_paths (list): A list of file paths relative to the base_path.
        output_filename (str): The name of the output file to create.
    """
    bundled_content = []
    files_processed = 0
    files_not_found = []

    print(f"Starting to bundle files. Base project path: {base_path}")
    print(f"Output will be saved to: {os.path.join(base_path, output_filename)}\n")

    for relative_path in file_paths:
        # Construct the full path to the file
        # On Windows, os.path.join will correctly use backslashes if base_path uses them.
        # If relative_path uses forward slashes, os.path.join handles that too.
        full_path = os.path.join(base_path, *relative_path.split('/'))
        
        header = f"==== FILE: {relative_path} ====\n"
        bundled_content.append(header)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                bundled_content.append(content)
                bundled_content.append("\n\n") # Add some space between files
                print(f"[SUCCESS] Read and added: {relative_path}")
                files_processed += 1
        except FileNotFoundError:
            error_message = f"[ERROR] File not found: {full_path}\n"
            bundled_content.append(error_message)
            files_not_found.append(relative_path)
            print(error_message.strip())
        except Exception as e:
            error_message = f"[ERROR] Could not read file {full_path}: {e}\n"
            bundled_content.append(error_message)
            files_not_found.append(relative_path) # Also count as not found for simplicity
            print(error_message.strip())

    # Write the bundled content to the output file
    output_full_path = os.path.join(base_path, output_filename)
    try:
        with open(output_full_path, 'w', encoding='utf-8') as outfile:
            outfile.write("".join(bundled_content))
        print(f"\nSuccessfully bundled {files_processed} files into: {output_full_path}")
        if files_not_found:
            print("\nCould not find or read the following files:")
            for nf_path in files_not_found:
                print(f"- {nf_path}")
        print("\nYou can now upload this file.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Could not write to output file {output_full_path}: {e}")

if __name__ == "__main__":
    # --- Configuration ---
    # IMPORTANT: Adjust this if your project is not located at C:\projects\edms
    # or if you run this script from a different directory.
    project_base_path = r"C:\projects\edms" 

    # List of files you identified as necessary
    # Using forward slashes for relative paths is common and os.path.join handles it.
    files_to_bundle = [
        "main.py",
        "views/admin/user_management_screen.py",
        "views/base_view.py",
        "views/main_menu.py",
        "views/admin/dialogs/add_edit_user_dialog.py",
        "views/admin/dialogs/add_edit_location_dialog.py",
        "views/admin/dialogs/add_edit_charge_code_dialog.py",
        # Assuming there might be an owner dialog, add if it exists and is relevant:
        # "views/admin/dialogs/add_edit_owner_dialog.py", 
        "controllers/user_controller.py",
        "controllers/location_controller.py",
        "controllers/charge_code_controller.py",
        "controllers/owner_controller.py",
        "config/app_config.py"
    ]

    output_file = "edms_user_management_bundle.txt"
    # --- End Configuration ---

    if not os.path.isdir(project_base_path):
        print(f"[CRITICAL ERROR] The project base path does not exist or is not a directory: {project_base_path}")
        print("Please check the 'project_base_path' variable in the script.")
    else:
        bundle_project_files(project_base_path, files_to_bundle, output_file)

