import os
import logging

def collect_all_project_files():
    """
    Scans specified project directories and collects all .py files into a single text file.
    """
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    output_filename = "complete_project_dump.txt"
    
    # Directories to scan for .py files
    dirs_to_scan = [
        "config",
        "controllers",
        "models",
        "views",
    ]

    logging.info(f"Starting collection of all .py files from project root: {base_path}")
    logging.info(f"Output will be saved to: {output_filename}")

    try:
        with open(output_filename, "w", encoding="utf-8") as outfile:
            for dir_name in dirs_to_scan:
                scan_path = os.path.join(base_path, dir_name)
                if not os.path.isdir(scan_path):
                    logging.warning(f"Directory not found, skipping: {scan_path}")
                    continue
                
                for root, _, files in os.walk(scan_path):
                    for file in sorted(files):
                        if file.endswith(".py"):
                            full_path = os.path.join(root, file)
                            relative_path = os.path.relpath(full_path, base_path)
                            
                            header = f"=============== FILE: {relative_path} ===============\n\n"
                            outfile.write(header)
                            logging.info(f"Processing: {relative_path}")
                            
                            try:
                                with open(full_path, "r", encoding="utf-8") as infile:
                                    outfile.write(infile.read())
                                    outfile.write("\n\n")
                            except Exception as e:
                                outfile.write(f"ERROR: Could not read file: {e}\n\n")

        logging.info(f"\nSUCCESS! Project files have been collected into '{output_filename}'.")
        logging.info("Please start a new chat and upload this file.")

    except Exception as e:
        logging.error(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    collect_all_project_files()