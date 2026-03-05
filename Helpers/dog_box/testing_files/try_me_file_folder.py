# === CODE OVERVIEW DOCSTRING STARTS HERE ===
"""
Interactive demo script that prompts the user to select either files or a folder
and then logs every file path that was chosen or discovered.

This is intended as a simple example of using the `tool_box.Helpers.dog_box.file_folder` dialog
helper together with SPAhub logging conventions.
"""
# === CODE OVERVIEW DOCSTRING STOPS HERE ===

# === IMPORTS STARTS HERE ===
import os
import sys
from typing import List, Optional

# add project root to Python path for tool_box imports
# the script lives in a subfolder (dog_box), so walk up one level
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import wx
from tool_box.Helpers.water_logged.the_logger import THElogger
from tool_box.Helpers.dog_box.file_folder import choose_files_or_folders
# note: wx import is kept here because some environments require WX to be
# initialized before creating dialogs; nothing uses it prior to main().
# === IMPORTS STOPS HERE ===

# === GLOBAL CONSTANTS STARTS HERE ===
LOG_FOLDER = "./logs"
TO_CONSOLE = True
TO_LOGFILE = True
DEBUG_ON = False
# === GLOBAL CONSTANTS STOPS HERE ===

# === HELPER FUNCTIONS STARTS HERE ===
def _gather_files_from_folder(folder_path: str) -> List[str]:
    """Return a list of all file paths under ``folder_path`` recursively.

    Args:
        folder_path: Root directory to scan.

    Returns:
        List of file paths found under the folder.
    """
    files: List[str] = []
    for root, _, filenames in os.walk(folder_path):
        for name in filenames:
            files.append(os.path.join(root, name))
    return files


# === HELPER FUNCTIONS STOPS HERE ===

# === MAIN FUNCTIONS/CLASSES STARTS HERE ===

def main() -> None:
    """Standalone entry point for the demo script."""
    logger = THElogger(
        script_name="try_me",
        log_folder=LOG_FOLDER,
        to_console=TO_CONSOLE,
        to_logfile=TO_LOGFILE,
        debug_on=DEBUG_ON,
    )

    choice: Optional[str] = choose_files_or_folders()
    if choice is None:
        logger.info("No selection was made; exiting.")
        logger.finalize_report()
        return

    app = wx.App(False)
    if choice == "folders":
        dlg = wx.DirDialog(None, message="Select a folder to scan for files:")
        dlg.CentreOnScreen()
        if dlg.ShowModal() == wx.ID_OK:
            folder = dlg.GetPath()
            logger.info(f"User selected folder: {folder}")
            all_files = _gather_files_from_folder(folder)
            for f in all_files:
                logger.info(f"Found file: {f}")
        dlg.Destroy()
    else:  # files
        style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE
        dlg = wx.FileDialog(None, message="Select one or more files:", style=style)
        dlg.CentreOnScreen()
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            logger.info(f"User selected {len(paths)} file(s)")
            for p in paths:
                logger.info(f"Selected file: {p}")
        dlg.Destroy()

    logger.finalize_report()


# === MAIN FUNCTIONS/CLASSES STOPS HERE ===

# === STANDALONE EXECUTION STARTS HERE ===
if __name__ == "__main__":
    main()
# === STANDALONE EXECUTION STOPS HERE ===
