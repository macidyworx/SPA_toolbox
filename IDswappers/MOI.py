import os
import sys

# Add project root to path so Helpers can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import shutil
import wx
from openpyxl import load_workbook
from xlrd import open_workbook
from xlutils.copy import copy
from Helpers.Clean_fields.clean_field import field_cleaner
from Helpers.dog_box import select_sif, select_work_files, select_output_folder
from water_logged.the_logger import THElogger

# Global constants for headers
FILE_STUDENT_HEADER = "Student" ## Stored as "Surname, Firstname"
FILE_ID_HEADER = "ID"
FILE_DATE_HEADER = "Date"
SIF_SURNAME = "Surname"
SIF_FIRSTNAME = "Firstname"
SIF_STUDENTID = "StudentID"


class MOISwapper:
    """
    MOI (Mathematics Online Interview Insight Platform) Swapper.

    Processes Excel files (.xls and .xlsx) to swap student IDs based on a
    Student Information File (SIF).
    """

    def __init__(self, logger):
        """Initialize MOI Swapper with logger."""
        self.logger = logger
        self.sif_df = None
        self.moi_folder = None
        self.skipped_folder = None
        self.not_found = []
        self.total_checked = 0
        self.total_matched = 0
        self.files_checked = []
        self.files_skipped = []

    def run(self):
        """Execute the MOI swapping process."""
        try:
            # Step 1: Get user inputs using dog_box helpers
            sif_path = select_sif()
            if sif_path is None:
                self.logger.info("User cancelled SIF selection.")
                self.logger.finalize_report()
                return

            files = select_work_files([".xlsx", ".xls", ".xlsm"])
            if not files:
                self.logger.info("No files selected.")
                self.logger.finalize_report()
                return

            # Filter out temporary Excel files
            files = [f for f in files if not os.path.basename(f).startswith('~$')]

            output_dir = select_output_folder("Select output folder for MOI")
            if output_dir is None:
                self.logger.info("User cancelled output folder selection.")
                self.logger.finalize_report()
                return

            self.logger.info(f"Using values: SIF={sif_path}, Files={len(files)}, Output={output_dir}")

            # Step 2: Setup output folder
            output_subfolder = os.path.join(output_dir, "MOIswapped")
            if os.path.exists(output_subfolder):
                result = wx.MessageBox(
                    f"{output_subfolder} already exists.\nRemove it and continue?",
                    "Output Folder Exists", wx.YES_NO | wx.ICON_WARNING)
                if result == wx.YES:
                    shutil.rmtree(output_subfolder)
                else:
                    self.logger.info("User cancelled due to existing output folder.")
                    self.logger.finalize_report()
                    return

            self.moi_folder = output_subfolder
            os.mkdir(self.moi_folder)

            self.skipped_folder = os.path.join(self.moi_folder, "SKIPPED")
            os.makedirs(self.skipped_folder, exist_ok=True)

            # Step 3: Load SIF dataframe
            self.sif_df = pd.read_excel(sif_path, header=1)  # Headers in row 2 (0-indexed as 1)
            self.sif_df[SIF_FIRSTNAME] = self.sif_df[SIF_FIRSTNAME].apply(field_cleaner)
            self.sif_df[SIF_SURNAME] = self.sif_df[SIF_SURNAME].apply(field_cleaner)

            self.logger.info(f"Total files to process: {len(files)}")

            # Step 4-7: Process each file
            for file_count, file in enumerate(files, 1):
                self.logger.info(f"Processing file {file_count}/{len(files)} > {file}")
                self._process_file(file)

            # Step 8: Save report
            self._save_report()

            self.logger.info(f"Total Students Checked --> {self.total_checked}")
            self.logger.info(f"Total Students Matched --> {self.total_matched}")
            self.logger.info(f"Total NOT Found --> {len(self.not_found)}")
            self.logger.info(f"Processing complete. Files saved in {self.moi_folder} folder.")

        except Exception as e:
            self.logger.error(f"Error during MOI processing: {e}")
        finally:
            self.logger.finalize_report()

    def _process_file(self, file):
        """Process a single file (xlsx/xlsm or xls)."""
        # Per-file counters
        file_checked = 0
        file_matched = 0
        file_not_found = 0

        if '.xlsx' in file.lower() or '.xlsm' in file.lower():
            self._process_xlsx(file, file_checked, file_matched, file_not_found)
        elif '.xls' in file.lower():
            self._process_xls(file, file_checked, file_matched, file_not_found)
        else:
            self.logger.info(f"Unsupported file format: {file}. Skipping.")
            self.files_skipped.append(os.path.basename(file))
            shutil.copy(file, os.path.join(self.skipped_folder, os.path.basename(file)))

    def _process_xlsx(self, file, file_checked, file_matched, file_not_found):
        """Process .xlsx/.xlsm file."""
        wb = load_workbook(file)
        ws = wb.active  # Assume first sheet

        # Find "Student" cell
        student_col = None
        header_row = None
        for row in ws.iter_rows():
            for cell in row:
                if cell.value and str(cell.value).lower() == FILE_STUDENT_HEADER.lower():
                    student_col = cell.column_letter
                    header_row = cell.row
                    break
            if student_col:
                break

        if not student_col:
            self.logger.info(f"Warning: '{FILE_STUDENT_HEADER}' header not found in {file}. Skipping.")
            self.files_skipped.append(os.path.basename(file))
            shutil.copy(file, os.path.join(self.skipped_folder, os.path.basename(file)))
            return

        # Find "ID" in the header row
        id_col = None
        for cell in ws[header_row]:
            if cell.value and str(cell.value).lower() == FILE_ID_HEADER.lower():
                id_col = cell.column_letter
                break

        if not id_col:
            self.logger.info(f"Warning: '{FILE_ID_HEADER}' header not found in {file}. Skipping.")
            self.files_skipped.append(os.path.basename(file))
            shutil.copy(file, os.path.join(self.skipped_folder, os.path.basename(file)))
            return

        # Find "Date" in the header row
        date_col = None
        for cell in ws[header_row]:
            if cell.value and str(cell.value).lower().startswith("date"):
                date_col = cell.column_letter
                break

        self.files_checked.append(os.path.basename(file))

        # Process each student row
        for row in range(header_row + 1, ws.max_row + 1):
            name_cell = ws[f"{student_col}{row}"]
            id_cell = ws[f"{id_col}{row}"]
            name = name_cell.value
            if name and isinstance(name, str):
                self.total_checked += 1
                file_checked += 1
                # Parse name: "Brown, Florence" -> Lname=Brown, Fname=Florence
                if ", " in name:
                    lname, fname = name.split(", ", 1)
                    fname = field_cleaner(fname)
                    lname = field_cleaner(lname)
                else:
                    # If not in expected format, skip or handle
                    self.logger.info(f"Warning: Name format not recognized in {file} row {row}: {name}")
                    continue

                # Get date for year
                date_value = ws[f"{date_col}{row}"].value if date_col else None
                year = None
                if date_value:
                    date_str = str(date_value)
                    if '/' in date_str:
                        year = date_str.split('/')[-1].split()[0]
                    elif '-' in date_str:
                        parts = date_str.split('-')
                        if len(parts) >= 3:
                            if len(parts[0]) == 4:  # yyyy-mm-dd format
                                year = parts[0]
                            else:  # dd-mm-yyyy format
                                year = parts[2].split()[0]

                # Find in SIF
                match = self.sif_df[(self.sif_df[SIF_FIRSTNAME] == fname) & (self.sif_df[SIF_SURNAME] == lname)]
                if not match.empty:
                    new_id = match[SIF_STUDENTID].iloc[0]
                    id_cell.value = new_id
                    self.total_matched += 1
                    file_matched += 1
                else:
                    self.not_found.append({'File': file, 'Row': row, 'Name': name, 'Fname': fname, 'Lname': lname, 'Year': year})
                    file_not_found += 1
                    self.logger.info(f"NOT FOUND in SIF dataFrame: {fname} {lname}")

        # Save to MOIswapped
        output_path = os.path.join(self.moi_folder, os.path.basename(file))
        try:
            wb.save(output_path)
        except Exception as e:
            self.logger.error(f"Error saving {output_path}: {e}")
            try:
                wb.save(output_path)
            except Exception as e2:
                self.logger.error(f"Failed again: {e2}. Skipping save for {file}.")

        self.logger.info(f"Students Checked: {file_checked}")
        self.logger.info(f"Students Matched: {file_matched}")
        self.logger.info(f"Students NOT Found: {file_not_found}")

    def _process_xls(self, file, file_checked, file_matched, file_not_found):
        """Process .xls file."""
        rb = open_workbook(file, formatting_info=True)
        wb = copy(rb)
        ws = wb.get_sheet(0)

        # Find header row and columns (0-based indices)
        header_row = None
        student_col = None
        id_col = None
        date_col = None
        sheet = rb.sheet_by_index(0)
        for row_idx in range(sheet.nrows):
            row = sheet.row(row_idx)
            for col_idx, cell in enumerate(row):
                if cell.value and str(cell.value).lower() == FILE_STUDENT_HEADER.lower():
                    student_col = col_idx
                    header_row = row_idx
                elif cell.value and str(cell.value).lower() == FILE_ID_HEADER.lower():
                    id_col = col_idx
                elif cell.value and str(cell.value).lower().startswith("date"):
                    date_col = col_idx
            if student_col is not None and id_col is not None:
                break

        if student_col is None or id_col is None:
            self.logger.info(f"Warning: Required headers not found in {file}. Skipping.")
            self.files_skipped.append(os.path.basename(file))
            shutil.copy(file, os.path.join(self.skipped_folder, os.path.basename(file)))
            return

        self.files_checked.append(os.path.basename(file))

        # Process each student row
        for row_idx in range(header_row + 1, sheet.nrows):
            name = sheet.cell_value(row_idx, student_col)
            if name:
                name = str(name).strip()
                self.total_checked += 1
                file_checked += 1
                # Parse name: "Brown, Florence" -> Lname=Brown, Fname=Florence
                if ", " in name:
                    lname, fname = name.split(", ", 1)
                    fname = field_cleaner(fname)
                    lname = field_cleaner(lname)
                else:
                    # If not in expected format, skip or handle
                    self.logger.info(f"Warning: Name format not recognized in {file} row {row_idx + 1}: {name}")
                    continue

                # Get date for year
                date_value = sheet.cell_value(row_idx, date_col) if date_col is not None else None
                year = None
                if date_value:
                    if isinstance(date_value, float):
                        # xlrd returns dates as floats
                        import xlrd
                        try:
                            date_tuple = xlrd.xldate_as_tuple(date_value, rb.datemode)
                            year = str(date_tuple[0])  # Year is first element
                        except:
                            year = None
                    else:
                        date_str = str(date_value)
                        if '/' in date_str:
                            year = date_str.split('/')[-1].split()[0]
                        elif '-' in date_str:
                            parts = date_str.split('-')
                            if len(parts) >= 3:
                                if len(parts[0]) == 4:  # yyyy-mm-dd format
                                    year = parts[0]
                                else:  # dd-mm-yyyy format
                                    year = parts[2].split()[0]

                # Find in SIF
                match = self.sif_df[(self.sif_df[SIF_FIRSTNAME] == fname) & (self.sif_df[SIF_SURNAME] == lname)]
                if not match.empty:
                    new_id = match[SIF_STUDENTID].iloc[0]
                    ws.write(row_idx, id_col, new_id)
                    self.total_matched += 1
                    file_matched += 1
                else:
                    self.not_found.append({'File': file, 'Row': row_idx + 1, 'Name': name, 'Fname': fname, 'Lname': lname, 'Year': year})
                    file_not_found += 1
                    self.logger.info(f"NOT FOUND in SIF dataFrame: {fname} {lname}")

        # Save to MOIswapped
        output_path = os.path.join(self.moi_folder, os.path.basename(file))
        try:
            wb.save(output_path)
        except Exception as e:
            self.logger.error(f"Error saving {output_path}: {e}")
            try:
                wb.save(output_path)
            except Exception as e2:
                self.logger.error(f"Failed again: {e2}. Skipping save for {file}.")

        self.logger.info(f"Students Checked: {file_checked}")
        self.logger.info(f"Students Matched: {file_matched}")
        self.logger.info(f"Students NOT Found: {file_not_found}")

    def _save_report(self):
        """Save processing report to Excel."""
        if not self.not_found and not self.files_checked and not self.files_skipped:
            return

        # Create summary data
        summary_data = [
            {'Metric': 'Total Files Processed', 'Value': len(self.files_checked)},
            {'Metric': 'Total Matched', 'Value': self.total_matched},
            {'Metric': 'Total NOT Matched', 'Value': len(self.not_found)},
            {'Metric': 'Note', 'Value': 'Numbers will be exaggerated, because students may be checked multiple times if they are in multiple files.'},
        ]
        summary_df = pd.DataFrame(summary_data)

        not_found_df = pd.DataFrame(self.not_found)

        with pd.ExcelWriter(os.path.join(self.moi_folder, "MOI_report.xlsx")) as writer:
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            not_found_df.to_excel(writer, sheet_name='Full List', index=False)

            # Add files lists to Summary sheet
            sheet = writer.sheets['Summary']
            sheet.cell(row=7, column=1).value = "Files Checked"
            for i, file in enumerate(self.files_checked, start=8):
                sheet.cell(row=i, column=1).value = file

            sheet.cell(row=7, column=2).value = "Files Skipped"
            for i, file in enumerate(self.files_skipped, start=8):
                sheet.cell(row=i, column=2).value = file


def main():
    """Main entry point for MOI Swapper."""
    print(r"""
===================================================================================================
___  ________ _____            ___________
|  \/  |  _  |_   _|          |_   _|  _  \
| .  . | | | | | |    ______    | | | | | |_____      ____ _ _ __  _ __   ___ _ __
| |\/| | | | | | |   |______|   | | | | / __\ \ /\ / / _` | '_ \| '_ \ / _ \ '__|
| |  | \ \_/ /_| |_            _| |_| |/ /\__ \\ V  V / (_| | |_) | |_) |  __/ |
\_|  |_/\___/ \___/            \___/|___/ |___/ \_/\_/ \__,_| .__/| .__/ \___|_|
                                                            | |   | |
                                                            |_|   |_|
===================================================================================================
""")

    # Initialize logger
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "logging.ini")
    logger = THElogger(script_name="MOI", config_file=config_path)

    # Run MOI Swapper
    swapper = MOISwapper(logger)
    swapper.run()


if __name__ == "__main__":
    main()
