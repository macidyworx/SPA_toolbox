"""
manager.py - Main launcher for the Test Identifier Editor.
"""

# === PATH SETUP (must be before other imports) ===
import os
import sys
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# === IMPORTS ===
import wx

from Finders.File_sorter.test_manager.add_test import AddTestDialog
from Finders.File_sorter.test_manager.edit_test import EditTestListDialog, EditTestDetailDialog
from Finders.File_sorter.test_manager.config_utils import YAML_PATH


# === MAIN FRAME ===
class TestManagerFrame(wx.Frame):
    """Main launcher window with Add and Edit buttons."""

    def __init__(self, yaml_path=None):
        super().__init__(None, title="Test Identifier Editor", size=(400, 200))
        self.yaml_path = yaml_path or YAML_PATH
        self._build_ui()
        self.Centre()

    def _build_ui(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Test Identifier Editor")
        title.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(title, 0, wx.ALL | wx.ALIGN_CENTER, 15)

        add_btn = wx.Button(panel, label="Add Test", size=(200, 35))
        add_btn.Bind(wx.EVT_BUTTON, self._on_add)
        sizer.Add(add_btn, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        edit_btn = wx.Button(panel, label="Edit Tests", size=(200, 35))
        edit_btn.Bind(wx.EVT_BUTTON, self._on_edit)
        sizer.Add(edit_btn, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        panel.SetSizer(sizer)

    def _on_add(self, event):
        dlg = AddTestDialog(self, yaml_path=self.yaml_path)
        dlg.ShowModal()
        dlg.Destroy()

    def _on_edit(self, event):
        dlg = EditTestListDialog(self, yaml_path=self.yaml_path)
        dlg.ShowModal()
        dlg.Destroy()


# === STANDALONE ENTRY POINT ===
def main():
    """Entry point for standalone execution."""
    app = wx.App(False)
    frame = TestManagerFrame()
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
