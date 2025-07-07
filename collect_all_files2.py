import os
import logging

def write_file_to_dump(outfile, full_path, base_path):
    """
    Writes the content of a single file to the output file, with a header.
    
    Args:
        outfile: The file object for the output dump file.
        full_path (str): The absolute path to the file to be read.
        base_path (str): The root project path, used for creating a relative path in the header.
    """
    try:
        # Create a relative path for cleaner headers in the output file
        relative_path = os.path.relpath(full_path, base_path)
        
        # Create and write the header for the file
        header = f"=============== FILE: {relative_path.replace(os.sep, '/')} ===============\n\n"
        outfile.write(header)
        logging.info(f"Processing: {relative_path}")
        
        # Open the source file, read its content, and write to the dump file
        with open(full_path, "r", encoding="utf-8", errors="ignore") as infile:
            outfile.write(infile.read())
            outfile.write("\n\n")
            
    except Exception as e:
        error_message = f"ERROR: Could not read file {relative_path}: {e}\n\n"
        outfile.write(error_message)
        logging.error(error_message)

def collect_all_project_files():
    """
    Scans a specified project directory to collect specific root files and all .py 
    files from subdirectories into a single text file.
    """
    # --- Configuration ---
    # IMPORTANT: Change this to the absolute path of your project's root folder.
    PROJECT_ROOT = r"c:\projects\edms"
    OUTPUT_FILENAME = "complete_project_dump.txt"
    
    # List of specific files to include from the PROJECT_ROOT
    FILES_TO_INCLUDE_FROM_ROOT = [
        "main.py",
    ]

    # List of subdirectories to scan recursively for .py files
    DIRS_TO_SCAN = [
        "config",
        "reports",
        "controllers",
        "models",
        "views",
        "scripts",
    ]
    # ---------------------

    logging.basicConfig(level=logging.INFO, format='%(message)s')

    # Ensure the project root directory exists
    if not os.path.isdir(PROJECT_ROOT):
        logging.error(f"FATAL: Project root directory not found: {PROJECT_ROOT}")
        return

    logging.info(f"Starting file collection from project root: {PROJECT_ROOT}")
    output_path = os.path.join(PROJECT_ROOT, OUTPUT_FILENAME)
    logging.info(f"Output will be saved to: {output_path}")

    try:
        with open(output_path, "w", encoding="utf-8") as outfile:
            # 1. Process specific files from the root directory
            for filename in FILES_TO_INCLUDE_FROM_ROOT:
                full_path = os.path.join(PROJECT_ROOT, filename)
                if os.path.isfile(full_path):
                    write_file_to_dump(outfile, full_path, PROJECT_ROOT)
                else:
                    logging.warning(f"Root file not found, skipping: {full_path}")
            
            # 2. Process all .py files in the specified subdirectories
            for dir_name in DIRS_TO_SCAN:
                scan_path = os.path.join(PROJECT_ROOT, dir_name)
                if not os.path.isdir(scan_path):
                    logging.warning(f"Directory not found, skipping: {scan_path}")
                    continue
                
                for root, _, files in os.walk(scan_path):
                    for file in sorted(files):
                        if file.endswith(".py"):
                            full_path = os.path.join(root, file)
                            write_file_to_dump(outfile, full_path, PROJECT_ROOT)

        logging.info(f"\nSUCCESS! Project files have been collected into '{output_path}'.")
        logging.info("You can now use this file.")

    except Exception as e:
        logging.error(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    collect_all_project_files()
