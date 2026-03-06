"""
add_test.py - wxPython dialog for adding a new test type to test_identifiers.yaml.
"""

import copy
import wx

from Helpers.Clean_fields.clean_field import field_cleaner
from Finders.File_sorter.test_manager.config_utils import (
    load_raw_configs, save_configs, get_next_priority, get_all_folders,
    build_test_entry, FILETYPES, YAML_PATH,
)


class AddTestDialog(wx.Dialog):
    """Dialog for adding a new test type configuration."""

    def __init__(self, parent=None, yaml_path=None):
        super().__init__(parent, title="Add New Test Type",
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.yaml_path = yaml_path or YAML_PATH
        self.configs = load_raw_configs(self.yaml_path)
        self.keys_dict = {ft: [] for ft in FILETYPES}
        self.find_keys_dict = {ft: [] for ft in FILETYPES}

        self._build_ui()
        self.SetSize(550, 700)
        self.Centre()

    def _build_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- Basic fields ---
        fields_sizer = wx.FlexGridSizer(rows=7, cols=2, vgap=6, hgap=10)
        fields_sizer.AddGrowableCol(1, 1)

        fields_sizer.Add(wx.StaticText(panel, label="Test Name:"), 0, wx.ALIGN_CV)
        self.name_ctrl = wx.TextCtrl(panel)
        fields_sizer.Add(self.name_ctrl, 1, wx.EXPAND)

        fields_sizer.Add(wx.StaticText(panel, label="Folder:"), 0, wx.ALIGN_CV)
        folders = get_all_folders(self.configs) + ["(new...)"]
        self.folder_combo = wx.ComboBox(panel, choices=folders, style=wx.CB_DROPDOWN)
        if folders and folders[0] != "(new...)":
            self.folder_combo.SetSelection(0)
        fields_sizer.Add(self.folder_combo, 1, wx.EXPAND)

        fields_sizer.Add(wx.StaticText(panel, label="Group:"), 0, wx.ALIGN_CV)
        self.group_ctrl = wx.TextCtrl(panel)
        fields_sizer.Add(self.group_ctrl, 1, wx.EXPAND)

        fields_sizer.Add(wx.StaticText(panel, label="Area:"), 0, wx.ALIGN_CV)
        self.area_ctrl = wx.TextCtrl(panel)
        fields_sizer.Add(self.area_ctrl, 1, wx.EXPAND)

        fields_sizer.Add(wx.StaticText(panel, label="Variant:"), 0, wx.ALIGN_CV)
        self.variant_ctrl = wx.TextCtrl(panel)
        fields_sizer.Add(self.variant_ctrl, 1, wx.EXPAND)

        fields_sizer.Add(wx.StaticText(panel, label="Sort Strategy:"), 0, wx.ALIGN_CV)
        self.strategy_ctrl = wx.TextCtrl(panel, value="{folder}")
        fields_sizer.Add(self.strategy_ctrl, 1, wx.EXPAND)

        main_sizer.Add(fields_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # --- File type checkboxes ---
        ft_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ft_sizer.Add(wx.StaticText(panel, label="File types:"), 0, wx.ALIGN_CV | wx.RIGHT, 8)
        self.ft_checks = {}
        for ft in ["xlsx/xls", "csv", "xlsm"]:
            cb = wx.CheckBox(panel, label=ft)
            cb.SetValue(True)
            self.ft_checks[ft] = cb
            ft_sizer.Add(cb, 0, wx.RIGHT, 10)
        main_sizer.Add(ft_sizer, 0, wx.LEFT | wx.RIGHT, 10)

        # --- Add KEY section ---
        key_box = wx.StaticBox(panel, label="Add KEY (exact cell match)")
        key_sizer = wx.StaticBoxSizer(key_box, wx.HORIZONTAL)
        key_sizer.Add(wx.StaticText(panel, label="Sheet:"), 0, wx.ALIGN_CV | wx.RIGHT, 4)
        self.key_sheet = wx.TextCtrl(panel, value="0", size=(50, -1))
        key_sizer.Add(self.key_sheet, 0, wx.RIGHT, 8)
        key_sizer.Add(wx.StaticText(panel, label="Cell:"), 0, wx.ALIGN_CV | wx.RIGHT, 4)
        self.key_cell = wx.TextCtrl(panel, size=(50, -1))
        key_sizer.Add(self.key_cell, 0, wx.RIGHT, 8)
        key_sizer.Add(wx.StaticText(panel, label="Startswith:"), 0, wx.ALIGN_CV | wx.RIGHT, 4)
        self.key_startswith = wx.TextCtrl(panel, size=(150, -1))
        key_sizer.Add(self.key_startswith, 1, wx.RIGHT, 8)
        add_key_btn = wx.Button(panel, label="Add Key")
        add_key_btn.Bind(wx.EVT_BUTTON, self._on_add_key)
        key_sizer.Add(add_key_btn, 0)
        main_sizer.Add(key_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # --- Add FIND_KEY section ---
        fk_box = wx.StaticBox(panel, label="Add FIND_KEY (area search)")
        fk_sizer = wx.StaticBoxSizer(fk_box, wx.HORIZONTAL)
        fk_sizer.Add(wx.StaticText(panel, label="Sheet:"), 0, wx.ALIGN_CV | wx.RIGHT, 4)
        self.fk_sheet = wx.TextCtrl(panel, value="0", size=(50, -1))
        fk_sizer.Add(self.fk_sheet, 0, wx.RIGHT, 8)
        fk_sizer.Add(wx.StaticText(panel, label="Startswith:"), 0, wx.ALIGN_CV | wx.RIGHT, 4)
        self.fk_startswith = wx.TextCtrl(panel, size=(150, -1))
        fk_sizer.Add(self.fk_startswith, 1, wx.RIGHT, 8)
        add_fk_btn = wx.Button(panel, label="Add Find Key")
        add_fk_btn.Bind(wx.EVT_BUTTON, self._on_add_find_key)
        fk_sizer.Add(add_fk_btn, 0)
        main_sizer.Add(fk_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # --- Keys display ---
        self.keys_display = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY,
                                        size=(-1, 150))
        main_sizer.Add(self.keys_display, 1, wx.ALL | wx.EXPAND, 10)

        # --- Feedback ---
        self.feedback = wx.StaticText(panel, label="")
        main_sizer.Add(self.feedback, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # --- Buttons ---
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        save_btn = wx.Button(panel, label="Save to YAML")
        save_btn.Bind(wx.EVT_BUTTON, self._on_save)
        btn_sizer.Add(save_btn, 0, wx.RIGHT, 10)
        close_btn = wx.Button(panel, wx.ID_CANCEL, "Close")
        btn_sizer.Add(close_btn, 0)
        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        panel.SetSizer(main_sizer)

    def _get_selected_filetypes(self):
        """Return list of selected file type strings."""
        types = []
        if self.ft_checks["xlsx/xls"].GetValue():
            types.extend(["xlsx", "xls"])
        if self.ft_checks["csv"].GetValue():
            types.append("csv")
        if self.ft_checks["xlsm"].GetValue():
            types.append("xlsm")
        return types

    def _parse_sheet(self, text):
        """Parse sheet value — int if numeric, else string."""
        text = text.strip()
        try:
            return int(text)
        except ValueError:
            return text

    def _on_add_key(self, event):
        sheet = self._parse_sheet(self.key_sheet.GetValue())
        cell = self.key_cell.GetValue().strip()
        startswith = field_cleaner(self.key_startswith.GetValue().strip())

        if not cell or not startswith:
            self.feedback.SetLabel("Cell and Startswith are required for KEY.")
            self.feedback.SetForegroundColour(wx.RED)
            return

        selected = self._get_selected_filetypes()
        if not selected:
            self.feedback.SetLabel("Select at least one file type.")
            self.feedback.SetForegroundColour(wx.RED)
            return

        key = {"sheet": sheet, "cell": cell, "startswith": startswith}
        for ft in selected:
            self.keys_dict[ft].append(copy.deepcopy(key))

        self.key_cell.SetValue("")
        self.key_startswith.SetValue("")
        self._update_display()
        self.feedback.SetLabel(f"Key added to: {', '.join(selected)}")
        self.feedback.SetForegroundColour(wx.Colour(0, 128, 0))

    def _on_add_find_key(self, event):
        sheet = self._parse_sheet(self.fk_sheet.GetValue())
        startswith = field_cleaner(self.fk_startswith.GetValue().strip())

        if not startswith:
            self.feedback.SetLabel("Startswith is required for FIND_KEY.")
            self.feedback.SetForegroundColour(wx.RED)
            return

        selected = self._get_selected_filetypes()
        if not selected:
            self.feedback.SetLabel("Select at least one file type.")
            self.feedback.SetForegroundColour(wx.RED)
            return

        key = {"sheet": sheet, "startswith": startswith}
        for ft in selected:
            self.find_keys_dict[ft].append(copy.deepcopy(key))

        self.fk_startswith.SetValue("")
        self._update_display()
        self.feedback.SetLabel(f"Find Key added to: {', '.join(selected)}")
        self.feedback.SetForegroundColour(wx.Colour(0, 128, 0))

    def _update_display(self):
        """Refresh the keys display text."""
        lines = []
        for ft in FILETYPES:
            if self.keys_dict[ft]:
                lines.append(f"{ft} KEYS:")
                for k in self.keys_dict[ft]:
                    lines.append(f"  {k}")
            if self.find_keys_dict[ft]:
                lines.append(f"{ft} FIND_KEYS:")
                for k in self.find_keys_dict[ft]:
                    lines.append(f"  {k}")
        self.keys_display.SetValue("\n".join(lines))

    def _on_save(self, event):
        name = self.name_ctrl.GetValue().strip()
        if not name:
            self.feedback.SetLabel("Test name is required.")
            self.feedback.SetForegroundColour(wx.RED)
            return

        if name in self.configs:
            self.feedback.SetLabel("Test name already exists in YAML.")
            self.feedback.SetForegroundColour(wx.RED)
            return

        folder = self.folder_combo.GetValue().strip()
        if folder == "(new...)" or not folder:
            self.feedback.SetLabel("Enter or select a folder name.")
            self.feedback.SetForegroundColour(wx.RED)
            return

        has_keys = any(self.keys_dict[ft] for ft in FILETYPES)
        has_find = any(self.find_keys_dict[ft] for ft in FILETYPES)
        if not has_keys and not has_find:
            self.feedback.SetLabel("Add at least one KEY or FIND_KEY.")
            self.feedback.SetForegroundColour(wx.RED)
            return

        entry = build_test_entry(
            folder=folder,
            group=self.group_ctrl.GetValue().strip(),
            area=self.area_ctrl.GetValue().strip(),
            variant=self.variant_ctrl.GetValue().strip(),
            sort_strategy=self.strategy_ctrl.GetValue().strip() or "{folder}",
            keys_dict=self.keys_dict,
            find_keys_dict=self.find_keys_dict,
            priority=get_next_priority(self.configs),
        )

        self.configs[name] = entry
        save_configs(self.configs, self.yaml_path)

        self.feedback.SetLabel("Saved to YAML!")
        self.feedback.SetForegroundColour(wx.Colour(0, 128, 0))
        wx.CallLater(1000, self.EndModal, wx.ID_OK)
