"""
Tests for unique_path.py
"""

import os
import pytest

from Finders.File_sorter.unique_path import get_unique_path


class TestGetUniquePath:
    """Tests for get_unique_path function."""

    def test_no_conflict(self, tmp_path):
        """Returns original path when no file exists."""
        path = str(tmp_path / "file.xlsx")
        assert get_unique_path(path) == path

    def test_one_conflict(self, tmp_path):
        """Appends _1 when original exists."""
        path = str(tmp_path / "file.xlsx")
        open(path, "w").close()
        result = get_unique_path(path)
        assert result == str(tmp_path / "file_1.xlsx")

    def test_two_conflicts(self, tmp_path):
        """Appends _2 when original and _1 both exist."""
        path = str(tmp_path / "file.xlsx")
        open(path, "w").close()
        open(str(tmp_path / "file_1.xlsx"), "w").close()
        result = get_unique_path(path)
        assert result == str(tmp_path / "file_2.xlsx")

    def test_many_conflicts(self, tmp_path):
        """Handles many sequential conflicts."""
        path = str(tmp_path / "data.csv")
        open(path, "w").close()
        for i in range(1, 10):
            open(str(tmp_path / f"data_{i}.csv"), "w").close()
        result = get_unique_path(path)
        assert result == str(tmp_path / "data_10.csv")

    def test_preserves_extension(self, tmp_path):
        """Extension is preserved after the suffix."""
        path = str(tmp_path / "report.xlsx")
        open(path, "w").close()
        result = get_unique_path(path)
        assert result.endswith(".xlsx")
        assert "_1.xlsx" in result

    def test_no_extension(self, tmp_path):
        """Works with files that have no extension."""
        path = str(tmp_path / "README")
        open(path, "w").close()
        result = get_unique_path(path)
        assert result == str(tmp_path / "README_1")

    def test_result_does_not_exist(self, tmp_path):
        """Returned path does not already exist."""
        path = str(tmp_path / "file.xlsx")
        open(path, "w").close()
        result = get_unique_path(path)
        assert not os.path.exists(result)
