import os
import pytest
from Helpers.dog_box.work_files import _collect_from_folder, _build_wildcard


# --- _collect_from_folder tests (no wx needed) ---

def _make_tree(tmp_path):
    """Create a folder structure with mixed file types."""
    # root files
    (tmp_path / "report.xlsx").write_text("")
    (tmp_path / "notes.txt").write_text("")
    (tmp_path / "data.xls").write_text("")

    # subfolder
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "more.xlsx").write_text("")
    (sub / "image.png").write_text("")

    # nested subfolder
    deep = sub / "deep"
    deep.mkdir()
    (deep / "final.xlsx").write_text("")
    (deep / "readme.md").write_text("")

    return tmp_path


def test_collect_xlsx_only(tmp_path):
    root = _make_tree(tmp_path)
    result = _collect_from_folder(str(root), [".xlsx"])
    filenames = [os.path.basename(p) for p in result]
    assert sorted(filenames) == ["final.xlsx", "more.xlsx", "report.xlsx"]


def test_collect_multiple_extensions(tmp_path):
    root = _make_tree(tmp_path)
    result = _collect_from_folder(str(root), [".xlsx", ".xls"])
    filenames = [os.path.basename(p) for p in result]
    assert sorted(filenames) == ["data.xls", "final.xlsx", "more.xlsx", "report.xlsx"]


def test_collect_no_matches(tmp_path):
    root = _make_tree(tmp_path)
    result = _collect_from_folder(str(root), [".csv"])
    assert result == []


def test_collect_case_insensitive(tmp_path):
    (tmp_path / "upper.XLSX").write_text("")
    (tmp_path / "lower.xlsx").write_text("")
    result = _collect_from_folder(str(tmp_path), [".xlsx"])
    filenames = [os.path.basename(p) for p in result]
    assert sorted(filenames) == ["lower.xlsx", "upper.XLSX"]


def test_collect_empty_folder(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    result = _collect_from_folder(str(empty), [".xlsx"])
    assert result == []


# --- _build_wildcard tests ---

def test_wildcard_single():
    wc = _build_wildcard([".xlsx"])
    assert "*.xlsx" in wc
    assert "All files" in wc


def test_wildcard_multiple():
    wc = _build_wildcard([".xlsx", ".xls"])
    assert "*.xlsx;*.xls" in wc
