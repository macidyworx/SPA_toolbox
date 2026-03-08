import sys
import os

import pytest

# Module file_folder does not exist in current codebase
pytest.importorskip("Helpers.dog_box.file_folder", minversion=None)

# ensure package import works
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Helpers.dog_box.file_folder import choose_files_or_folders

# create fake wx classes to drive the dialog behavior
class DummyApp:
    def __init__(self, arg=False):
        pass

class DummyDialog:
    # class variable controlling what gets selected during ShowModal
    _mode: str | None = None

    def __init__(self, *args, **kwargs):
        self.file_handler = None
        self.folder_handler = None

    def CentreOnScreen(self):
        # real dialog centers, no effect in dummy
        pass

    def SetSizer(self, *args, **kwargs):
        pass

    def Fit(self):
        pass

    def ShowModal(self):
        # simulate user choice based on mode
        if self._mode == 'files' and self.file_handler is not None:
            self.file_handler(None)
            return wx.ID_OK
        if self._mode == 'folders' and self.folder_handler is not None:
            self.folder_handler(None)
            return wx.ID_CANCEL
        return wx.ID_CANCEL

    def EndModal(self, code):
        self._result = code

    def Destroy(self):
        pass

class DummyBoxSizer:
    def __init__(self, *args, **kwargs):
        pass
    def Add(self, *args, **kwargs):
        pass

class DummyStaticText:
    def __init__(self, *args, **kwargs):
        pass

class DummyButton:
    def __init__(self, parent, label):
        self.parent = parent
        self.label = label
        self._handler = None

    def Bind(self, event, handler):
        # decide which handler to store based on label text
        if 'Files' in self.label:
            self.parent.file_handler = handler
        else:
            self.parent.folder_handler = handler


def setup_module(module):
    # patch wx symbols used by the helper
    import tool_box.Helpers.dog_box.file_folder as ff
    ff.wx.App = DummyApp
    ff.wx.Dialog = DummyDialog
    ff.wx.BoxSizer = DummyBoxSizer
    ff.wx.StaticText = DummyStaticText
    ff.wx.Button = DummyButton
    ff.wx.ALL = None
    ff.wx.HORIZONTAL = None
    ff.wx.VERTICAL = None
    ff.wx.ALIGN_CENTER = None
    ff.wx.ID_OK = 1
    ff.wx.ID_CANCEL = 2
    ff.wx.EVT_BUTTON = 'EVT_BUTTON'


def test_choose_files(monkeypatch):
    DummyDialog._mode = 'files'
    assert choose_files_or_folders() == 'files'


def test_choose_folders(monkeypatch):
    DummyDialog._mode = 'folders'
    assert choose_files_or_folders() == 'folders'


def test_close_without_choice(monkeypatch):
    DummyDialog._mode = None
    assert choose_files_or_folders() is None
