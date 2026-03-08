"""
edit_test.py - wxPython dialog for editing/deleting test types in test_identifiers.yaml.
"""

import copy
import wx

from Helpers.Clean_fields.clean_field import field_cleaner
from Finders.File_sorter.test_manager.config_utils import (
    load_raw_configs, save_configs, get_all_folders,
    build_test_entry, FILETYPES, META_FIELDS, YAML_PATH,
)


class EditTestListDialog(wx.Dialog):
    """Dialog showing a list of test types to select for editing."""

    def __init__(self, parent=None, yaml_path=None):
        super().__init__(parent, title="Edit Test Types",
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.yaml_path = yaml_path or YAML_PATH
        self.configs = load_raw_configs(self.yaml_path)

        self._build_ui()
        self.SetSize(450, 500)
        self.Centre()

    def _build_ui(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(wx.StaticText(panel, label="Select a test type to edit:"),
                  0, wx.ALL, 10)

        self.test_list = wx.ListBox(panel, style=wx.LB_SINGLE)
        self._refresh_list()
        sizer.Add(self.test_list, 1, wx.ALL | wx.EXPAND, 10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        edit_btn = wx.Button(panel, label="Edit Selected")
        edit_btn.Bind(wx.EVT_BUTTON, self._on_edit)
        btn_sizer.Add(edit_btn, 0, wx.RIGHT, 10)

        close_btn = wx.Button(panel, wx.ID_CANCEL, "Close")
        btn_sizer.Add(close_btn, 0)
        sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        panel.SetSizer(sizer)
        self.test_list.Bind(wx.EVT_LISTBOX_DCLICK, self._on_edit)

    def _refresh_list(self):
        """Reload configs and refresh the list."""
        self.configs = load_raw_configs(self.yaml_path)
        self.sorted_names = sorted(self.configs.keys(), key=str.lower)
        self.test_list.Clear()
        for name in self.sorted_names:
            self.test_list.Append(name)

    def _on_edit(self, event):
        idx = self.test_list.GetSelection()
        if idx == wx.NOT_FOUND:
            wx.MessageBox("Please select a test to edit.", "No Selection",
                          wx.OK | wx.ICON_INFORMATION)
            return

        name = self.sorted_names[idx]
        configs = self.configs

        # Loop handles rebuild — detail dialog returns ID_RETRY when UI needs refresh
        while True:
            dlg = EditTestDetailDialog(self, name, configs, self.yaml_path)
            result = dlg.ShowModal()
            configs = dlg.configs
            test_data = dlg.test_data
            dlg.Destroy()

            if result == wx.ID_RETRY:
                # Rebuild: reopen with updated test_data
                configs[name] = test_data
                continue
            break

        if result == wx.ID_OK:
            self._refresh_list()


class EditTestDetailDialog(wx.Dialog):
    """Dialog for editing a single test type's configuration."""

    def __init__(self, parent, test_name, configs, yaml_path):
        super().__init__(parent, title=f"Edit: {test_name}",
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.test_name = test_name
        self.configs = configs
        self.yaml_path = yaml_path
        self.test_data = copy.deepcopy(configs[test_name])

        self._build_ui()
        self.SetSize(600, 750)
        self.Centre()

    def _build_ui(self):
        panel = wx.ScrolledWindow(self)
        panel.SetScrollRate(0, 10)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- Basic fields ---
        fields_sizer = wx.FlexGridSizer(cols=2, vgap=6, hgap=10)
        fields_sizer.AddGrowableCol(1, 1)

        fields_sizer.Add(wx.StaticText(panel, label="Test Name:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.name_ctrl = wx.TextCtrl(panel, value=self.test_name)
        fields_sizer.Add(self.name_ctrl, 1, wx.EXPAND)

        self.field_ctrls = {}
        basic_fields = [
            ("folder", "Folder:"),
            ("group", "Group:"),
            ("area", "Area:"),
            ("variant", "Variant:"),
            ("sort_strategy", "Sort Strategy:"),
            ("SWAPPER_FILE", "Swapper File:"),
            ("SURNAME_HEADER", "Surname Header:"),
            ("FIRSTNAME_HEADER", "Firstname Header:"),
            ("ID_HEADER", "ID Header:"),
        ]
        for field, label in basic_fields:
            fields_sizer.Add(wx.StaticText(panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
            ctrl = wx.TextCtrl(panel, value=str(self.test_data.get(field, "")))
            self.field_ctrls[field] = ctrl
            fields_sizer.Add(ctrl, 1, wx.EXPAND)

        main_sizer.Add(fields_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # --- KEYS / FIND_KEYS display and editing ---
        for ft in FILETYPES:
            ft_data = self.test_data.get(ft, {})
            if not isinstance(ft_data, dict):
                continue

            for key_type in ("KEYS", "FIND_KEYS"):
                entries = ft_data.get(key_type, [])
                if not entries:
                    continue

                box = wx.StaticBox(panel, label=f"{ft} {key_type}")
                box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

                for i, entry in enumerate(entries):
                    row_sizer = wx.BoxSizer(wx.HORIZONTAL)
                    for k, v in entry.items():
                        row_sizer.Add(wx.StaticText(panel, label=f"{k}:"),
                                      0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 2)
                        ctrl = wx.TextCtrl(panel, value=str(v), size=(100, -1),
                                           name=f"{ft}|{key_type}|{i}|{k}")
                        row_sizer.Add(ctrl, 0, wx.RIGHT, 8)

                    remove_btn = wx.Button(panel, label="Remove", size=(60, -1))
                    remove_btn.entry_ref = (ft, key_type, i)
                    remove_btn.Bind(wx.EVT_BUTTON, self._on_remove_entry)
                    row_sizer.Add(remove_btn, 0)

                    box_sizer.Add(row_sizer, 0, wx.ALL, 4)

                main_sizer.Add(box_sizer, 0, wx.ALL | wx.EXPAND, 5)

        # --- Add KEY/FIND_KEY section ---
        add_box = wx.StaticBox(panel, label="Add New Entry")
        add_sizer = wx.StaticBoxSizer(add_box, wx.VERTICAL)

        # File type checkboxes
        ft_row = wx.BoxSizer(wx.HORIZONTAL)
        ft_row.Add(wx.StaticText(panel, label="To file types:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.ft_checks = {}
        for ft in FILETYPES:
            cb = wx.CheckBox(panel, label=ft)
            self.ft_checks[ft] = cb
            ft_row.Add(cb, 0, wx.RIGHT, 8)
        add_sizer.Add(ft_row, 0, wx.ALL, 4)

        # Add KEY row
        key_row = wx.BoxSizer(wx.HORIZONTAL)
        key_row.Add(wx.StaticText(panel, label="Sheet:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self.add_key_sheet = wx.TextCtrl(panel, value="0", size=(40, -1))
        key_row.Add(self.add_key_sheet, 0, wx.RIGHT, 8)
        key_row.Add(wx.StaticText(panel, label="Cell:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self.add_key_cell = wx.TextCtrl(panel, size=(50, -1))
        key_row.Add(self.add_key_cell, 0, wx.RIGHT, 8)
        key_row.Add(wx.StaticText(panel, label="Startswith:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self.add_key_sw = wx.TextCtrl(panel, size=(120, -1))
        key_row.Add(self.add_key_sw, 1, wx.RIGHT, 8)
        add_key_btn = wx.Button(panel, label="Add Key")
        add_key_btn.Bind(wx.EVT_BUTTON, self._on_add_key)
        key_row.Add(add_key_btn, 0)
        add_sizer.Add(key_row, 0, wx.ALL | wx.EXPAND, 4)

        # Add FIND_KEY row
        fk_row = wx.BoxSizer(wx.HORIZONTAL)
        fk_row.Add(wx.StaticText(panel, label="Sheet:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self.add_fk_sheet = wx.TextCtrl(panel, value="0", size=(40, -1))
        fk_row.Add(self.add_fk_sheet, 0, wx.RIGHT, 8)
        fk_row.Add(wx.StaticText(panel, label="Startswith:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self.add_fk_sw = wx.TextCtrl(panel, size=(120, -1))
        fk_row.Add(self.add_fk_sw, 1, wx.RIGHT, 8)
        add_fk_btn = wx.Button(panel, label="Add Find Key")
        add_fk_btn.Bind(wx.EVT_BUTTON, self._on_add_find_key)
        fk_row.Add(add_fk_btn, 0)
        add_sizer.Add(fk_row, 0, wx.ALL | wx.EXPAND, 4)

        main_sizer.Add(add_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # --- Feedback ---
        self.feedback = wx.StaticText(panel, label="")
        main_sizer.Add(self.feedback, 0, wx.LEFT | wx.RIGHT, 10)

        # --- Action buttons ---
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        save_btn = wx.Button(panel, label="Save Changes")
        save_btn.Bind(wx.EVT_BUTTON, self._on_save)
        btn_sizer.Add(save_btn, 0, wx.RIGHT, 10)

        delete_btn = wx.Button(panel, label="Delete Test")
        delete_btn.SetForegroundColour(wx.RED)
        delete_btn.Bind(wx.EVT_BUTTON, self._on_delete)
        btn_sizer.Add(delete_btn, 0, wx.RIGHT, 10)

        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(cancel_btn, 0)
        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        panel.SetSizer(main_sizer)

    def _parse_sheet(self, text):
        text = text.strip()
        try:
            return int(text)
        except ValueError:
            return text

    def _get_checked_filetypes(self):
        return [ft for ft, cb in self.ft_checks.items() if cb.GetValue()]

    def _on_remove_entry(self, event):
        btn = event.GetEventObject()
        ft, key_type, idx = btn.entry_ref
        ft_data = self.test_data.get(ft, {})
        entries = ft_data.get(key_type, [])
        if 0 <= idx < len(entries):
            entries.pop(idx)
            if not entries:
                del ft_data[key_type]
            if not ft_data:
                del self.test_data[ft]
        # Rebuild UI
        self._rebuild()

    def _on_add_key(self, event):
        sheet = self._parse_sheet(self.add_key_sheet.GetValue())
        cell = self.add_key_cell.GetValue().strip()
        sw = field_cleaner(self.add_key_sw.GetValue().strip())
        if not cell or not sw:
            self.feedback.SetLabel("Cell and Startswith are required.")
            self.feedback.SetForegroundColour(wx.RED)
            return
        selected = self._get_checked_filetypes()
        if not selected:
            self.feedback.SetLabel("Select at least one file type.")
            self.feedback.SetForegroundColour(wx.RED)
            return
        key = {"sheet": sheet, "cell": cell, "startswith": sw}
        for ft in selected:
            self.test_data.setdefault(ft, {}).setdefault("KEYS", []).append(
                copy.deepcopy(key)
            )
        self._rebuild()

    def _on_add_find_key(self, event):
        sheet = self._parse_sheet(self.add_fk_sheet.GetValue())
        sw = field_cleaner(self.add_fk_sw.GetValue().strip())
        if not sw:
            self.feedback.SetLabel("Startswith is required.")
            self.feedback.SetForegroundColour(wx.RED)
            return
        selected = self._get_checked_filetypes()
        if not selected:
            self.feedback.SetLabel("Select at least one file type.")
            self.feedback.SetForegroundColour(wx.RED)
            return
        key = {"sheet": sheet, "startswith": sw}
        for ft in selected:
            self.test_data.setdefault(ft, {}).setdefault("FIND_KEYS", []).append(
                copy.deepcopy(key)
            )
        self._rebuild()

    def _rebuild(self):
        """Close and reopen with updated test_data."""
        # Store current test_data back into configs temporarily
        self.configs[self.test_name] = self.test_data
        parent = self.GetParent()
        self.EndModal(wx.ID_RETRY)

    def _collect_edited_values(self):
        """Read all editable fields back from the UI controls."""
        # Read basic field controls
        for field, ctrl in self.field_ctrls.items():
            val = ctrl.GetValue().strip()
            if val:
                self.test_data[field] = val
            elif field in self.test_data and field not in ("folder",):
                self.test_data[field] = ""

        # Read edited KEYS/FIND_KEYS values from named text controls
        for child in self._get_all_children(self):
            if isinstance(child, wx.TextCtrl) and child.GetName().count("|") == 3:
                parts = child.GetName().split("|")
                ft, key_type, idx_str, k = parts
                idx = int(idx_str)
                ft_data = self.test_data.get(ft, {})
                entries = ft_data.get(key_type, [])
                if idx < len(entries):
                    val = child.GetValue().strip()
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                    entries[idx][k] = val

    def _get_all_children(self, widget):
        """Recursively get all child widgets."""
        children = []
        for child in widget.GetChildren():
            children.append(child)
            children.extend(self._get_all_children(child))
        return children

    def _on_save(self, event):
        self._collect_edited_values()

        new_name = self.name_ctrl.GetValue().strip()
        if not new_name:
            self.feedback.SetLabel("Test name is required.")
            self.feedback.SetForegroundColour(wx.RED)
            return

        folder = self.field_ctrls["folder"].GetValue().strip()
        if not folder:
            self.feedback.SetLabel("Folder is required.")
            self.feedback.SetForegroundColour(wx.RED)
            return

        # Handle rename
        if new_name != self.test_name:
            if new_name in self.configs:
                self.feedback.SetLabel("A test with this name already exists.")
                self.feedback.SetForegroundColour(wx.RED)
                return
            del self.configs[self.test_name]

        self.configs[new_name] = self.test_data
        save_configs(self.configs, self.yaml_path)

        wx.MessageBox("Test updated successfully!", "Saved",
                       wx.OK | wx.ICON_INFORMATION)
        self.EndModal(wx.ID_OK)

    def _on_delete(self, event):
        result = wx.MessageBox(
            f'Are you sure you want to delete "{self.test_name}"?\n\nThis cannot be undone.',
            "Confirm Delete", wx.YES_NO | wx.ICON_WARNING
        )
        if result != wx.YES:
            return

        if self.test_name in self.configs:
            del self.configs[self.test_name]
            save_configs(self.configs, self.yaml_path)
            wx.MessageBox(f'Test "{self.test_name}" deleted.', "Deleted",
                           wx.OK | wx.ICON_INFORMATION)
        self.EndModal(wx.ID_OK)
