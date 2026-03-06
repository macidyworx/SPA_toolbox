"""
PATonline-FINDER.py - Locate and categorize PATonline Excel files by field presence.

Scans Excel files for header fields (Family name, Given name, Unique ID, Username)
and organizes them into corresponding output folder structures:
- No_UniqueID/ - has Family name + Given name + Username (no Unique ID)
- Only_UniqueID/ - has Family name + Given name + Unique ID (no Username)
- [root] - has all four fields

Can be run standalone or imported as a module.
"""

# === IMPORTS ===
import os
import sys
import shutil

# Add project root to path so Helpers can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import wx
from openpyxl import load_workbook
from xlrd import open_workbook
from Helpers.Clean_fields.clean_field import field_cleaner
from Helpers.dog_box import select_work_files, select_output_folder
from water_logged.the_logger import THElogger

# === GLOBAL CONSTANTS ===
TARGET_HEADERS = {
    "Family name": "family_name",
    "Given name": "given_name",
    "Unique ID": "unique_id",
    "Username": "username",
}

SCAN_COLUMNS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']
SCAN_ROWS = range(1, 21)


# === HELPER FUNCTIONS ===
def find_headers(worksheet):
    """
    Scan worksheet cells A1-M20 for target headers (case-insensitive, whitespace-normalized).

    Uses field_cleaner helper for robust text normalization to handle real-world data
    variations (unicode, extra whitespace, mixed case). Normalizes both cell value and
    TARGET_HEADERS keys for reliable matching.

    Args:
        worksheet: openpyxl worksheet object

    Returns:
        dict with keys: has_family_name, has_given_name, has_unique_id, has_username
    """
    found_headers = set()
    # Create normalized lookup: normalize both sides for reliable matching
    normalized_headers = {field_cleaner(k, strip_spaces=True): v for k, v in TARGET_HEADERS.items()}

    for row in SCAN_ROWS:
        for col in SCAN_COLUMNS:
            cell = worksheet[f'{col}{row}']
            if cell.value is not None:
                # Use field_cleaner for robust text normalization (handles unicode, whitespace)
                cell_text = field_cleaner(str(cell.value), strip_spaces=True)
                if cell_text in normalized_headers:
                    found_headers.add(normalized_headers[cell_text])

    return {
        'has_family_name': 'family_name' in found_headers,
        'has_given_name': 'given_name' in found_headers,
        'has_unique_id': 'unique_id' in found_headers,
        'has_username': 'username' in found_headers,
    }


# === MAIN CLASS ===
class PATonlineFinder:
    """Finds, categorizes, and organizes PATonline Excel files."""

    def __init__(self):
        """Initialize logger and set up configuration."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Look for logging.ini in same directory, fallback to parent (IDswappers)
        config_path = os.path.join(script_dir, "logging.ini")
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(script_dir), "IDswappers", "logging.ini")

        self.logger = THElogger(script_name="PATonline-FINDER", config_file=config_path)

    def categorize_file(self, file_path):
        """
        Determine file category based on header presence.

        Args:
            file_path (str): Path to Excel file

        Returns:
            str: Category name ('all_fields', 'no_unique_id', 'only_unique_id', 'unidentified')
        """
        try:
            # Try to open as xlsx first
            try:
                wb = load_workbook(file_path, read_only=True, data_only=True)
                ws = wb.active
                headers = find_headers(ws)
                wb.close()
            except Exception:
                # Fallback to xlrd for .xls files
                try:
                    wb = open_workbook(file_path, on_demand=True)
                    ws = wb.sheet_by_index(0)
                    # For xlrd, manually scan for headers
                    headers = {
                        'has_family_name': False,
                        'has_given_name': False,
                        'has_unique_id': False,
                        'has_username': False,
                    }
                    # Create normalized lookup: normalize both sides for reliable matching
                    normalized_headers = {field_cleaner(k, strip_spaces=True): v for k, v in TARGET_HEADERS.items()}

                    for row_idx in range(20):
                        for col_idx in range(13):  # A-M = 0-12
                            try:
                                cell_value = ws.cell_value(row_idx, col_idx)
                                if cell_value:
                                    # Use field_cleaner for robust text normalization
                                    cell_text = field_cleaner(str(cell_value), strip_spaces=True)
                                    if cell_text in normalized_headers:
                                        header_key = f"has_{normalized_headers[cell_text]}"
                                        headers[header_key] = True
                            except (IndexError, TypeError):
                                pass
                except Exception:
                    return 'unidentified'

            # Determine category
            has_family = headers['has_family_name']
            has_given = headers['has_given_name']
            has_unique = headers['has_unique_id']
            has_user = headers['has_username']

            # All four fields
            if has_family and has_given and has_unique and has_user:
                return 'all_fields'
            # No Unique ID (has Family + Given + Username)
            elif has_family and has_given and has_user and not has_unique:
                return 'no_unique_id'
            # Only Unique ID (has Family + Given + Unique ID, no Username)
            elif has_family and has_given and has_unique and not has_user:
                return 'only_unique_id'
            else:
                return 'unidentified'

        except Exception as e:
            self.logger.debug(f"Error categorizing {file_path}: {e}")
            return 'unidentified'

    def process_file(self, file_path, output_dir):
        """
        Categorize file and move to appropriate subdirectory.

        Args:
            file_path (str): Path to file to process
            output_dir (str): Root output directory

        Returns:
            bool: True if processed successfully, False otherwise
        """
        category = self.categorize_file(file_path)

        # Only log identified files at INFO level
        if category == 'unidentified':
            return False

        # Determine target directory
        if category == 'all_fields':
            target_dir = output_dir
        elif category == 'no_unique_id':
            target_dir = os.path.join(output_dir, 'No_UniqueID')
        elif category == 'only_unique_id':
            target_dir = os.path.join(output_dir, 'Only_UniqueID')

        # Create target directory if needed
        os.makedirs(target_dir, exist_ok=True)

        # Determine target file path
        filename = os.path.basename(file_path)
        target_path = os.path.join(target_dir, filename)

        # Check if file already exists
        if os.path.exists(target_path):
            result = wx.MessageBox(
                f"{target_path} already exists.\nOverwrite?",
                "File Exists", wx.YES_NO | wx.ICON_WARNING)
            if result != wx.YES:
                self.logger.debug(f"Skipped existing file: {target_path}")
                return False

        # Move file
        try:
            shutil.move(file_path, target_path)
            self.logger.info(f"Processed {filename}: Category={category}, Destination={target_dir}")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to move {filename}: {e}")
            return False

    def run(self):
        """Main workflow: select files, output folder, and process."""
        self.logger.info("PATonline-FINDER started")

        # Prompt user for input files
        files = select_work_files([".xlsx", ".xls"])
        if not files:
            self.logger.info("User cancelled file selection.")
            self.logger.finalize_report()
            return

        # Prompt user for output folder
        output_dir = select_output_folder("Select output folder for PATonline files")
        if not output_dir:
            self.logger.info("User cancelled output folder selection.")
            self.logger.finalize_report()
            return

        self.logger.info(f"Processing {len(files)} file(s) to {output_dir}")

        # Process each file
        processed_count = 0
        for file_path in files:
            if self.process_file(file_path, output_dir):
                processed_count += 1

        self.logger.info(f"Processing complete. {processed_count} file(s) categorized and moved.")
        self.logger.finalize_report()


# === STANDALONE EXECUTION ===
def main():
    """Entry point for standalone execution."""
    print(r"""
================================================================================
     ____  ___  ______              __ _          ___________
    / __ \/   |/_  __/___  ____   / /(_)___     / ____/  _/ /
   / /_/ / /| | / / / __ \/ __ \ / / / / __ \   / /_   / // /
  / ____/ ___ |/ / / /_/ / / / // / / / /_/ /  / __/ _/ // /
 / /   / /  |/ / / /_/ / /_/ // / / / /_/ /   / /   / // /
/_/   /_/  |_/_/  \____/\____//_/_/_/\____/   /_/   /___/_/

================================================================================
""")

    app = wx.App(False)
    finder = PATonlineFinder()
    finder.run()
    app.Destroy()


if __name__ == "__main__":
    main()
