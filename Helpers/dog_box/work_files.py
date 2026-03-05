"""
work_files.py
Helper for selecting working files to process.

Supports three selection modes via a single dialog:
  - Folder: user picks a folder, all matching files in it and its subfolders
    are collected.
  - Single/multi file: user picks one or more files directly.

The caller provides the acceptable file extensions (e.g. ['.xlsx', '.xls']).
"""

import os
import wx
from typing import List, Optional


def _ensure_app():
    """Return the existing wx.App or create one if none exists."""
    app = wx.GetApp()
    if app is None:
        app = wx.App(False)
    return app


def _collect_from_folder(folder, extensions):
    """Walk folder recursively and return files matching any of the extensions."""
    extensions = [ext.lower() for ext in extensions]
    found = []
    for root, _, filenames in os.walk(folder):
        for name in filenames:
            if os.path.splitext(name)[1].lower() in extensions:
                found.append(os.path.join(root, name))
    found.sort()
    return found


def _build_wildcard(extensions):
    """Build a wx wildcard string from a list of extensions.

    e.g. ['.xlsx', '.xls'] -> 'Excel files (*.xlsx;*.xls)|*.xlsx;*.xls|All files (*.*)|*.*'
    """
    patterns = ";".join(f"*{ext}" for ext in extensions)
    return f"Matching files ({patterns})|{patterns}|All files (*.*)|*.*"


def select_work_files(extensions: List[str]) -> Optional[List[str]]:
    """Prompt the user to select working files or a folder for processing.

    A dialog asks the user to choose between selecting files or a folder.
    - Files: a multi-select file dialog filtered by the given extensions.
    - Folder: a directory picker; all files matching the extensions in the
      folder and its subfolders are collected.

    Args:
        extensions: List of acceptable file extensions, e.g. ['.xlsx', '.xls'].
                    Include the dot.

    Returns:
        List of file paths, or None if the user cancelled.
        An empty list is returned if a folder was selected but contained
        no matching files (caller should handle this).
    """
    _ensure_app()

    # Ask: files or folder?
    dlg = wx.SingleChoiceDialog(
        None,
        "How would you like to select your working files?",
        "Working Files",
        ["Select file(s)", "Select a folder (includes subfolders)"],
    )
    dlg.CentreOnScreen()
    try:
        if dlg.ShowModal() != wx.ID_OK:
            return None
        choice = dlg.GetSelection()
    finally:
        dlg.Destroy()

    if choice == 0:
        # File selection
        wildcard = _build_wildcard(extensions)
        style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE
        fdlg = wx.FileDialog(None, message="Select working file(s)",
                             wildcard=wildcard, style=style)
        fdlg.CentreOnScreen()
        try:
            if fdlg.ShowModal() != wx.ID_OK:
                return None
            return list(fdlg.GetPaths())
        finally:
            fdlg.Destroy()
    else:
        # Folder selection
        ddlg = wx.DirDialog(None, message="Select folder to process",
                            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        ddlg.CentreOnScreen()
        try:
            if ddlg.ShowModal() != wx.ID_OK:
                return None
            folder = ddlg.GetPath()
        finally:
            ddlg.Destroy()

        files = _collect_from_folder(folder, extensions)
        if not files:
            wx.MessageBox(
                f"No files with extensions {extensions} found in:\n{folder}",
                "No Files Found",
                wx.OK | wx.ICON_INFORMATION,
            )
        return files
