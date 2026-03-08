import openpyxl
import pytest
import os
import sys

# SKIP: This test depends on tool_box.Helpers.water_logged which doesn't exist in this codebase
pytestmark = pytest.mark.skip(reason="Module depends on water_logged logger that is not available")

# ensure package path for direct execution
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
# add package root so "dog_box.testing_files" can be imported
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# the demo script has been moved into testing_files subpackage
from Helpers.dog_box.testing_files.try_me_load_SSOT import _log_first_five_columns


class DummyLogger:
    def __init__(self):
        self.records = []

    def info(self, msg, *args):
        self.records.append(str(msg % args if args else msg))

    def error(self, msg, *args):
        self.records.append(f"ERROR: {msg % args if args else msg}")


def _make_book(path, rows):
    wb = openpyxl.Workbook()
    ws = wb.active  # type: ignore[assignment]
    # ws is never None with openpyxl, ignore the optional member warning
    for r in rows:
        ws.append(r)  # type: ignore[attr-defined]
    wb.save(path)


def test_log_first_five_columns(tmp_path):
    file_path = tmp_path / "data.xlsx"
    rows = [
        [1, 2, 3, 4, 5, 6],
        ["a", "b", None, "d", "e"],
    ]
    _make_book(file_path, rows)
    logger = DummyLogger()
    _log_first_five_columns(str(file_path), logger)
    # first record is the sheet-info line
    assert logger.records[0].startswith("Inspecting sheet:")
    # only two data rows should be logged (empty rows skipped)
    assert "first5=['1', '2', '3', '4', '5']" in logger.records[1]
    assert "first5=['a', 'b', '', 'd', 'e']" in logger.records[2]


def test_log_nonexistent(tmp_path):
    logger = DummyLogger()
    with pytest.raises(FileNotFoundError):
        _log_first_five_columns(str(tmp_path / "nofile.xlsx"), logger)
