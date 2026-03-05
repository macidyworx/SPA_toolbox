# === CODE OVERVIEW DOCSTRING STARTS HERE ===
"""
Demonstration script for the ``tool_box.Helpers.dog_box.load_SSOT`` helper.

Users may edit the ``REQUIRED_HEADERS`` list defined below to control which
column names must appear in the selected workbook.  When the script is run it:

1. Prompts the user to choose a single .xlsx file.
2. Validates that the file contains all of the required headers.
3. If validation succeeds, logs every row of the workbook, showing only the
   values from the first five columns.

The purpose is to provide a simple interactive test harness that exercises the
header‑checking logic and illustrates how a calling application might process
an SSOT workbook after selection.
"""
# === CODE OVERVIEW DOCSTRING STOPS HERE ===

# === IMPORTS STARTS HERE ===
import os
import sys
from typing import List, Optional

# add project root to Python path for tool_box imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import wx
import openpyxl

from tool_box.Helpers.water_logged.the_logger import THElogger
from tool_box.Helpers.dog_box.load_SSOT import select_ssot_file
# === IMPORTS STOPS HERE ===

# === GLOBAL CONSTANTS STARTS HERE ===
# modify these values before running to specify which headers are mandatory
REQUIRED_HEADERS: List[str] = ["Surname", "Firstname", "StudentID"]
# optional row where the column headers appear.  If you leave this variable
# out or set it to None, the helper defaults to row 2.  Set to 1 if your file
# puts headers on the first line instead of the second.
HEADER_ROW: Optional[int] = 2

LOG_FOLDER = "./logs"
TO_CONSOLE = True
TO_LOGFILE = True
DEBUG_ON = False
# === GLOBAL CONSTANTS STOPS HERE ===

# === HELPER FUNCTIONS STARTS HERE ===
def _log_first_five_columns(file_path: str, logger) -> None:
    """Open the workbook and log the first five columns for every row.

    This helper is intentionally verbose for debugging; it reports the active
    sheet name, row index, and the number of non-empty cells in the row.  It
    also logs the actual values from the first five columns so we can see if
    data is simply located further to the right.

    Args:
        file_path: Path to a validated `.xlsx` file.
        logger: Initialized THElogger instance.
    """
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.active
    logger.info(f"Inspecting sheet: {ws.title}")  # type: ignore[attr-defined]
    # pylance sometimes warns that ``ws`` could be None; ignore that
    for idx, row in enumerate(ws.iter_rows(values_only=True)):  # type: ignore[attr-defined]
        # count non-empty cells overall
        non_empty = sum(1 for cell in row if cell not in (None, ""))
        if non_empty == 0:
            # skip entirely blank rows
            continue
        # convert first five cells to strings
        values = [str(cell) if cell is not None else "" for cell in row[:5]]
        logger.info(f"Row {idx}: non_empty={non_empty} first5={values}")


# === HELPER FUNCTIONS STOPS HERE ===

# === MAIN FUNCTIONS/CLASSES STARTS HERE ===

def main() -> None:
    """Entry point when running the script directly."""
    logger = THElogger(
        script_name="try_me_load_SSOT",
        log_folder=LOG_FOLDER,
        to_console=TO_CONSOLE,
        to_logfile=TO_LOGFILE,
        debug_on=DEBUG_ON,
    )

    # selection dialog - only pass HEADER_ROW when it is not None so that
    # the helper can rely on its own default of 2 otherwise.
    if HEADER_ROW is None:
        selected = select_ssot_file(REQUIRED_HEADERS)
    else:
        selected = select_ssot_file(REQUIRED_HEADERS, HEADER_ROW)
    if selected is None:
        logger.info("No valid SSOT file was selected; exiting.")
        logger.finalize_report()
        return

    logger.info(f"Processing workbook: {selected}")
    try:
        _log_first_five_columns(selected, logger)
    except Exception as e:
        logger.error(f"Failed to read rows from {selected}: {e}")
    finally:
        logger.finalize_report()


# === MAIN FUNCTIONS/CLASSES STOPS HERE ===

# === STANDALONE EXECUTION STARTS HERE ===
if __name__ == "__main__":
    main()
# === STANDALONE EXECUTION STOPS HERE ===
