"""
Tests for file_sorter.py
"""

import csv
import os
import pytest

from openpyxl import Workbook

from Finders.File_sorter.file_sorter import FileSorter


# === HELPERS ===

def _make_xlsx(path, cell_values):
    """Create a .xlsx file with given cell values."""
    wb = Workbook()
    ws = wb.active
    for ref, val in cell_values.items():
        ws[ref] = val
    wb.save(str(path))
    wb.close()


def _make_csv(path, rows):
    """Create a .csv file with given rows."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)


def _make_large_file(path, size_bytes):
    """Create a file of given size."""
    with open(path, "wb") as f:
        f.write(b"x" * size_bytes)


@pytest.fixture
def input_dir(tmp_path):
    """Create an input directory with test files."""
    d = tmp_path / "input"
    d.mkdir()
    return d


@pytest.fixture
def output_dir(tmp_path):
    """Create an output directory."""
    d = tmp_path / "output"
    d.mkdir()
    return d


@pytest.fixture
def yaml_path(tmp_path):
    """Create a minimal test YAML config."""
    import yaml
    config = {
        "TestTypeA": {
            "priority": 1,
            "folder": "FolderA",
            "group": "GroupA",
            "area": "AreaA",
            "variant": "",
            "sort_strategy": "{folder}",
            "xlsx": {
                "KEYS": [{"sheet": 0, "cell": "A1", "startswith": "typea"}]
            },
        },
        "TestTypeB": {
            "priority": 2,
            "folder": "FolderB",
            "group": "GroupB",
            "area": "AreaB",
            "variant": "online",
            "sort_strategy": "{group}/{variant}",
            "xlsx": {
                "KEYS": [{"sheet": 0, "cell": "A1", "startswith": "typeb"}]
            },
            "csv": {
                "KEYS": [{"sheet": 0, "cell": "A1", "startswith": "typeb"}]
            },
        },
    }
    path = tmp_path / "test_config.yaml"
    with open(path, "w") as f:
        yaml.dump(config, f)
    return str(path)


# === TESTS: FileSorter ===

class TestFileSorter:
    """Tests for the FileSorter class."""

    def test_sorts_matching_file(self, input_dir, output_dir, yaml_path):
        """Matching file is copied to the correct folder."""
        _make_xlsx(input_dir / "file1.xlsx", {"A1": "TypeA Data"})
        sorter = FileSorter(yaml_path=yaml_path)
        summary = sorter.sort_files(str(input_dir), str(output_dir))

        assert summary["sorted"] == {"TestTypeA": 1}
        assert os.path.exists(os.path.join(str(output_dir), "FolderA", "file1.xlsx"))

    def test_sorts_to_strategy_path(self, input_dir, output_dir, yaml_path):
        """File is sorted using the sort_strategy template."""
        _make_xlsx(input_dir / "file2.xlsx", {"A1": "TypeB Online Report"})
        sorter = FileSorter(yaml_path=yaml_path)
        summary = sorter.sort_files(str(input_dir), str(output_dir))

        assert summary["sorted"] == {"TestTypeB": 1}
        expected = os.path.join(str(output_dir), "GroupB", "online", "file2.xlsx")
        assert os.path.exists(expected)

    def test_unidentified_file(self, input_dir, output_dir, yaml_path):
        """Unmatched file is recorded in unidentified list."""
        _make_xlsx(input_dir / "unknown.xlsx", {"A1": "No Match Here"})
        sorter = FileSorter(yaml_path=yaml_path)
        summary = sorter.sort_files(str(input_dir), str(output_dir))

        assert len(summary["unidentified"]) == 1
        assert "unknown.xlsx" in summary["unidentified"][0]

    def test_multiple_files(self, input_dir, output_dir, yaml_path):
        """Sorts multiple files correctly."""
        _make_xlsx(input_dir / "a.xlsx", {"A1": "TypeA"})
        _make_xlsx(input_dir / "b.xlsx", {"A1": "TypeB"})
        _make_xlsx(input_dir / "c.xlsx", {"A1": "Unknown"})

        sorter = FileSorter(yaml_path=yaml_path)
        summary = sorter.sort_files(str(input_dir), str(output_dir))

        assert summary["sorted"]["TestTypeA"] == 1
        assert summary["sorted"]["TestTypeB"] == 1
        assert len(summary["unidentified"]) == 1
        assert summary["total"] == 3

    def test_recursive_scan(self, input_dir, output_dir, yaml_path):
        """Finds files in subdirectories."""
        sub = input_dir / "subdir"
        sub.mkdir()
        _make_xlsx(sub / "nested.xlsx", {"A1": "TypeA Nested"})

        sorter = FileSorter(yaml_path=yaml_path)
        summary = sorter.sort_files(str(input_dir), str(output_dir))

        assert summary["sorted"] == {"TestTypeA": 1}

    def test_duplicate_filenames(self, input_dir, output_dir, yaml_path):
        """Duplicate filenames get _1 suffix."""
        sub1 = input_dir / "dir1"
        sub2 = input_dir / "dir2"
        sub1.mkdir()
        sub2.mkdir()
        _make_xlsx(sub1 / "same.xlsx", {"A1": "TypeA File 1"})
        _make_xlsx(sub2 / "same.xlsx", {"A1": "TypeA File 2"})

        sorter = FileSorter(yaml_path=yaml_path)
        summary = sorter.sort_files(str(input_dir), str(output_dir))

        assert summary["sorted"]["TestTypeA"] == 2
        folder = os.path.join(str(output_dir), "FolderA")
        files = os.listdir(folder)
        assert len(files) == 2
        assert "same.xlsx" in files
        assert "same_1.xlsx" in files

    def test_skips_large_files(self, input_dir, output_dir, yaml_path):
        """Files exceeding max_file_size are skipped."""
        _make_large_file(str(input_dir / "big.xlsx"), 500)
        sorter = FileSorter(yaml_path=yaml_path, max_file_size=100)
        summary = sorter.sort_files(str(input_dir), str(output_dir))

        assert len(summary["skipped"]) == 1

    def test_skips_unsupported_extensions(self, input_dir, output_dir, yaml_path):
        """Non-supported file types are ignored."""
        (input_dir / "notes.txt").write_text("hello")
        (input_dir / "image.png").write_bytes(b"\x89PNG")
        _make_xlsx(input_dir / "real.xlsx", {"A1": "TypeA"})

        sorter = FileSorter(yaml_path=yaml_path)
        summary = sorter.sort_files(str(input_dir), str(output_dir))

        assert summary["total"] == 1
        assert summary["sorted"] == {"TestTypeA": 1}

    def test_empty_input(self, input_dir, output_dir, yaml_path):
        """Empty input folder returns zero totals."""
        sorter = FileSorter(yaml_path=yaml_path)
        summary = sorter.sort_files(str(input_dir), str(output_dir))

        assert summary["total"] == 0
        assert summary["sorted"] == {}

    def test_preserves_file_content(self, input_dir, output_dir, yaml_path):
        """Copied file has same content as original (shutil.copy2)."""
        src = input_dir / "orig.xlsx"
        _make_xlsx(src, {"A1": "TypeA Content"})

        sorter = FileSorter(yaml_path=yaml_path)
        sorter.sort_files(str(input_dir), str(output_dir))

        dest = os.path.join(str(output_dir), "FolderA", "orig.xlsx")
        with open(str(src), "rb") as f1, open(dest, "rb") as f2:
            assert f1.read() == f2.read()

    def test_csv_identification(self, input_dir, output_dir, yaml_path):
        """CSV files are identified and sorted."""
        _make_csv(str(input_dir / "data.csv"), [["TypeB Online Data"]])

        sorter = FileSorter(yaml_path=yaml_path)
        summary = sorter.sort_files(str(input_dir), str(output_dir))

        assert summary["sorted"] == {"TestTypeB": 1}

    def test_cancel_via_progress_callback(self, input_dir, output_dir, yaml_path):
        """Progress callback returning False cancels the sort."""
        _make_xlsx(input_dir / "a.xlsx", {"A1": "TypeA"})
        _make_xlsx(input_dir / "b.xlsx", {"A1": "TypeA"})

        cancel_after = 1
        call_count = [0]

        def progress(current, total, filename):
            call_count[0] += 1
            return call_count[0] <= cancel_after

        messages = []
        sorter = FileSorter(
            yaml_path=yaml_path,
            progress_callback=progress,
            message_callback=messages.append,
        )
        summary = sorter.sort_files(str(input_dir), str(output_dir))

        assert any("cancelled" in m.lower() for m in messages)

    def test_message_callback(self, input_dir, output_dir, yaml_path):
        """Messages are sent via the callback."""
        _make_xlsx(input_dir / "a.xlsx", {"A1": "TypeA"})
        messages = []
        sorter = FileSorter(
            yaml_path=yaml_path,
            message_callback=messages.append,
        )
        sorter.sort_files(str(input_dir), str(output_dir))

        assert len(messages) > 0
        assert any("Sort Summary" in m for m in messages)

    def test_slowest_tracking(self, input_dir, output_dir, yaml_path):
        """Slowest files are tracked in summary."""
        _make_xlsx(input_dir / "a.xlsx", {"A1": "TypeA"})
        sorter = FileSorter(yaml_path=yaml_path)
        summary = sorter.sort_files(str(input_dir), str(output_dir))

        assert len(summary["slowest"]) <= 5
        for elapsed, path in summary["slowest"]:
            assert elapsed >= 0
            assert os.path.basename(path).endswith(".xlsx")
