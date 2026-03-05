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
FILE_FNAME = "Given name"
FILE_LNAME = "Family name"
FILE_ID_HEADER = "Unique ID"
FILE_DATE_HEADER = ["Completed", "Date"]
SIF_SURNAME = "Surname"
SIF_FIRSTNAME = "Firstname"
SIF_STUDENTID = "StudentID"


class PATSwapper:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "logging.ini")
        self.logger = THElogger(script_name="PATdownloads", config_file=config_path)

    def run(self):
        # Get user inputs via dog_box
        sif_path = select_sif()
        if not sif_path:
            self.logger.info("User cancelled SIF selection.")
            self.logger.finalize_report()
            return

        files = select_work_files([".xlsx", ".xls"])
        if not files:
            self.logger.info("No working files selected.")
            self.logger.finalize_report()
            return

        output_dir = select_output_folder("Select output folder for PAT")
        if not output_dir:
            self.logger.info("User cancelled output folder selection.")
            self.logger.finalize_report()
            return

        pat_folder = os.path.join(output_dir, "PATswapped")

        # Handle existing output subfolder
        if os.path.exists(pat_folder):
            result = wx.MessageBox(
                f"{pat_folder} already exists.\nRemove it and continue?",
                "Output Folder Exists", wx.YES_NO | wx.ICON_WARNING)
            if result == wx.YES:
                shutil.rmtree(pat_folder)
            else:
                self.logger.info("User cancelled due to existing output folder.")
                self.logger.finalize_report()
                return

        os.makedirs(pat_folder, exist_ok=True)
        skipped_folder = os.path.join(pat_folder, "SKIPPED")
        os.makedirs(skipped_folder, exist_ok=True)

        self.logger.info(f"Using values: SIF={sif_path}, Output={output_dir}")

        # Load SIF dataframe
        sif_df = pd.read_excel(sif_path, header=1)
        sif_df[SIF_FIRSTNAME] = sif_df[SIF_FIRSTNAME].apply(field_cleaner)
        sif_df[SIF_SURNAME] = sif_df[SIF_SURNAME].apply(field_cleaner)

        # Filter files (remove temp files)
        files = [f for f in files if not os.path.basename(f).startswith('~$') and os.path.isfile(f)]

        self.logger.info(f"Total files to process: {len(files)}")

        # List to log not found students
        not_found = []

        # Counters
        total_checked = 0
        total_matched = 0

        # Track files
        files_checked = []
        files_skipped = []

        # Process each file
        file_count = 0
        for file in files:
            file_count += 1
            self.logger.info(f"Processing file {file_count}/{len(files)} > {file}")

            # Per-file counters
            file_checked = 0
            file_matched = 0
            file_not_found = 0

            if file.lower().endswith('.xlsx'):
                wb = load_workbook(file)
                ws = wb.active

                # Find header row and columns
                header_row = None
                fname_col = None
                lname_col = None
                id_col = None
                date_col = None
                for row in ws.iter_rows():
                    for cell in row:
                        if cell.value == FILE_FNAME:
                            fname_col = cell.column_letter
                            header_row = cell.row
                        elif cell.value == FILE_LNAME:
                            lname_col = cell.column_letter
                        elif cell.value == FILE_ID_HEADER:
                            id_col = cell.column_letter
                        elif cell.value in FILE_DATE_HEADER:
                            date_col = cell.column_letter
                    if fname_col and lname_col and id_col:
                        break

                if not fname_col or not lname_col or not id_col:
                    self.logger.error(f"Required headers not found in {file}. Skipping.")
                    files_skipped.append(os.path.basename(file))
                    shutil.copy(file, os.path.join(skipped_folder, os.path.basename(file)))
                    continue

                files_checked.append(os.path.basename(file))

                # Process each student row
                for row in range(header_row + 1, ws.max_row + 1):
                    fname_cell = ws[f"{fname_col}{row}"]
                    lname_cell = ws[f"{lname_col}{row}"]
                    id_cell = ws[f"{id_col}{row}"]
                    fname = fname_cell.value
                    lname = lname_cell.value
                    if fname and lname and isinstance(fname, str) and isinstance(lname, str):
                        fname = field_cleaner(fname)
                        lname = field_cleaner(lname)
                        total_checked += 1
                        file_checked += 1
                        # Find in SIF
                        match = sif_df[(sif_df[SIF_FIRSTNAME] == fname) & (sif_df[SIF_SURNAME] == lname)]
                        if not match.empty:
                            new_id = match[SIF_STUDENTID].iloc[0]
                            id_cell.value = new_id
                            total_matched += 1
                            file_matched += 1
                        else:
                            date_value = ws[f"{date_col}{row}"].value if date_col else None
                            year = None
                            if date_value:
                                date_str = str(date_value)
                                if '/' in date_str:
                                    year = date_str.split('/')[-1].split()[0]
                                elif '-' in date_str:
                                    parts = date_str.split('-')
                                    if len(parts) >= 3:
                                        if len(parts[0]) == 4:
                                            year = parts[0]
                                        else:
                                            year = parts[2].split()[0]
                            not_found.append({'File': file, 'Row': row, 'Fname': fname, 'Lname': lname, 'Year': year})
                            file_not_found += 1
                            self.logger.info(f"NOT FOUND in SIF: {fname} {lname}")

                # Save to PATswapped
                output_path = os.path.join(pat_folder, os.path.basename(file))
                try:
                    wb.save(output_path)
                except Exception as e:
                    self.logger.error(f"Error saving {output_path}: {e}")
                    input("Please close the file in Excel and press Enter to retry.")
                    try:
                        wb.save(output_path)
                    except Exception as e2:
                        self.logger.error(f"Failed again: {e2}. Skipping save for {file}.")
                self.logger.info(f"Students Checked: {file_checked}")
                self.logger.info(f"Students Matched: {file_matched}")
                self.logger.info(f"Students NOT Found: {file_not_found}")

            elif file.lower().endswith('.xls'):
                rb = open_workbook(file, formatting_info=True)
                wb = copy(rb)
                ws = wb.get_sheet(0)

                # Find header row and columns (0-based indices)
                header_row = None
                fname_col = None
                lname_col = None
                id_col = None
                date_col = None
                sheet = rb.sheet_by_index(0)
                for row_idx in range(sheet.nrows):
                    row = sheet.row(row_idx)
                    for col_idx, cell in enumerate(row):
                        if cell.value == FILE_FNAME:
                            fname_col = col_idx
                            header_row = row_idx
                        elif cell.value == FILE_LNAME:
                            lname_col = col_idx
                        elif cell.value == FILE_ID_HEADER:
                            id_col = col_idx
                        elif cell.value in FILE_DATE_HEADER:
                            date_col = col_idx
                    if fname_col is not None and lname_col is not None and id_col is not None:
                        break

                if fname_col is None or lname_col is None or id_col is None:
                    self.logger.error(f"Required headers not found in {file}. Skipping.")
                    files_skipped.append(os.path.basename(file))
                    shutil.copy(file, os.path.join(skipped_folder, os.path.basename(file)))
                    continue

                files_checked.append(os.path.basename(file))

                # Process each student row
                for row_idx in range(header_row + 1, sheet.nrows):
                    fname = sheet.cell_value(row_idx, fname_col)
                    lname = sheet.cell_value(row_idx, lname_col)
                    if fname and lname:
                        fname = field_cleaner(fname)
                        lname = field_cleaner(lname)
                        total_checked += 1
                        file_checked += 1
                        # Find in SIF
                        match = sif_df[(sif_df[SIF_FIRSTNAME] == fname) & (sif_df[SIF_SURNAME] == lname)]
                        if not match.empty:
                            new_id = match[SIF_STUDENTID].iloc[0]
                            ws.write(row_idx, id_col, new_id)
                            total_matched += 1
                            file_matched += 1
                        else:
                            date_value = sheet.cell_value(row_idx, date_col) if date_col is not None else None
                            year = None
                            if date_value:
                                date_str = str(date_value)
                                if '/' in date_str:
                                    year = date_str.split('/')[-1].split()[0]
                                elif '-' in date_str:
                                    parts = date_str.split('-')
                                    if len(parts) >= 3:
                                        if len(parts[0]) == 4:
                                            year = parts[0]
                                        else:
                                            year = parts[2].split()[0]
                            not_found.append({'File': file, 'Row': row_idx + 1, 'Fname': fname, 'Lname': lname, 'Year': year})
                            file_not_found += 1
                            self.logger.info(f"NOT FOUND in SIF: {fname} {lname}")

                # Save to PATswapped
                output_path = os.path.join(pat_folder, os.path.basename(file))
                try:
                    wb.save(output_path)
                except Exception as e:
                    self.logger.error(f"Error saving {output_path}: {e}")
                    input("Please close the file in Excel and press Enter to retry.")
                    try:
                        wb.save(output_path)
                    except Exception as e2:
                        self.logger.error(f"Failed again: {e2}. Skipping save for {file}.")
                self.logger.info(f"Students Checked: {file_checked}")
                self.logger.info(f"Students Matched: {file_matched}")
                self.logger.info(f"Students NOT Found: {file_not_found}")
            else:
                self.logger.error(f"Unsupported file format: {file}. Skipping.")
                files_skipped.append(os.path.basename(file))
                shutil.copy(file, os.path.join(skipped_folder, os.path.basename(file)))

        # Save not found log
        if not_found:
            log_df = pd.DataFrame(not_found)
            log_df.to_excel(os.path.join(pat_folder, "not_found_log.xlsx"), index=False)

        # Save report
        if not_found or files_checked or files_skipped:
            summary_data = [
                {'Metric': 'Total Files Processed', 'Value': len(files_checked)},
                {'Metric': 'Total Matched', 'Value': total_matched},
                {'Metric': 'Total NOT Matched', 'Value': len(not_found)},
                {'Metric': 'Note', 'Value': 'Numbers will be exaggerated, because students may be checked multiple times if they are in multiple files.'},
            ]
            summary_df = pd.DataFrame(summary_data)

            not_found_df = pd.DataFrame(not_found)

            with pd.ExcelWriter(os.path.join(pat_folder, "PAT_report.xlsx")) as writer:
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                not_found_df.to_excel(writer, sheet_name='Full List', index=False)

                sheet = writer.sheets['Summary']
                sheet.cell(row=7, column=1).value = "Files Checked"
                for i, file in enumerate(files_checked, start=8):
                    sheet.cell(row=i, column=1).value = file

                sheet.cell(row=7, column=2).value = "Files Skipped"
                for i, file in enumerate(files_skipped, start=8):
                    sheet.cell(row=i, column=2).value = file

        self.logger.info(f"Total Students Checked --> {total_checked}")
        self.logger.info(f"Total Students Matched --> {total_matched}")
        self.logger.info(f"Total NOT Found --> {len(not_found)}")
        self.logger.info(f"Processing complete. Files saved in {pat_folder} folder.")
        self.logger.finalize_report()


def main():
    print(r"""
===================================================================================================
______  ___ _____            ___________
| ___ \/ _ \_   _|          |_   _|  _  \
| |_/ / /_\ \| |    ______    | | | | | |_____      ____ _ _ __  _ __   ___ _ __
|  __/|  _  || |   |______|   | | | | | / __\ \ /\ / / _` | '_ \| '_ \ / _ \ '__|
| |   | | | || |             _| |_| |/ /\__ \\ V  V / (_| | |_) | |_) |  __/ |
\_|   \_| |_/\_/             \___/|___/ |___/ \_/\_/ \__,_| .__/| .__/ \___|_|
                                                          | |   | |
          OARS files ONLY                                 |_|   |_|
===================================================================================================
""")

    app = wx.App(False)
    swapper = PATSwapper()
    swapper.run()
    app.Destroy()


if __name__ == "__main__":
    main()
