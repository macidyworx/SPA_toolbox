# Helper module for file/folder selection dialog

import wx
from typing import Optional


def choose_files_or_folders() -> Optional[str]:
    """Show a simple dialog asking the user to pick Files or Folders.

    Returns:
        "files" if the user clicked the Files button,
        "folders" if the user clicked the Folders button,
        None if the dialog was closed without choosing.
    """
    app = wx.App(False)
    choice: Optional[str] = None

    dlg = wx.Dialog(None, title="Working items")
    # position in center of screen so the user notices it
    dlg.CentreOnScreen()
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(
        wx.StaticText(dlg, label="Would you like to process Files or Folders?"),
        0,
        wx.ALL,
        10,
    )
    btnsizer = wx.BoxSizer(wx.HORIZONTAL)
    btn_files = wx.Button(dlg, label="Files")
    btn_folders = wx.Button(dlg, label="Folders")
    btnsizer.Add(btn_files, 0, wx.ALL, 5)
    btnsizer.Add(btn_folders, 0, wx.ALL, 5)
    sizer.Add(btnsizer, 0, wx.ALIGN_CENTER)
    dlg.SetSizer(sizer)
    dlg.Fit()

    def on_files(evt):
        nonlocal choice
        choice = "files"
        dlg.EndModal(wx.ID_OK)

    def on_folders(evt):
        nonlocal choice
        choice = "folders"
        dlg.EndModal(wx.ID_CANCEL)

    btn_files.Bind(wx.EVT_BUTTON, on_files)
    btn_folders.Bind(wx.EVT_BUTTON, on_folders)

    dlg.ShowModal()
    dlg.Destroy()
    return choice
