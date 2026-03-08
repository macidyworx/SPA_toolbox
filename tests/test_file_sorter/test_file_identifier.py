"""
Tests for file_identifier.py
"""

import csv
import pytest

from openpyxl import Workbook

from Finders.File_sorter.file_identifier import (
    identify_file,
    _check_keys,
    _check_find_keys,
    _match_entry,
)
from Finders.File_sorter.readers.xlsx_reader import XlsxReader
from Finders.File_sorter.readers.csv_reader import CsvReader


# === HELPERS ===

def _make_xlsx(tmp_path, filename, cell_values):
    """Create a .xlsx file with given cell values.

    cell_values: dict of {"A1": "value", "B2": "value", ...}
    """
    path = tmp_path / filename
    wb = Workbook()
    ws = wb.active
    for ref, val in cell_values.items():
        ws[ref] = val
    wb.save(str(path))
    wb.close()
    return str(path)


def _make_csv(tmp_path, filename, rows):
    """Create a .csv file with given rows (list of lists)."""
    path = tmp_path / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)
    return str(path)


def _config(keys=None, find_keys=None, fmt="xlsx", **kwargs):
    """Build a minimal test config."""
    cfg = {
        "priority": 1,
        "folder": "TestFolder",
        "group": "",
        "area": "",
        "variant": "",
        "sort_strategy": "{folder}",
    }
    fmt_section = {}
    if keys is not None:
        fmt_section["KEYS"] = keys
    if find_keys is not None:
        fmt_section["FIND_KEYS"] = find_keys
    cfg[fmt] = fmt_section
    cfg.update(kwargs)
    return cfg


# === TESTS: identify_file ===

class TestIdentifyFile:
    """Tests for the main identify_file function."""

    def test_match_startswith(self, tmp_path):
        """Matches a file by startswith on A1."""
        path = _make_xlsx(tmp_path, "pat.xlsx", {"A1": "PAT Reading 5th Edition"})
        configs = [
            ("PAT R 5th", _config(keys=[
                {"sheet": 0, "cell": "A1", "startswith": "pat reading 5th edition"}
            ])),
        ]
        name, cfg = identify_file(path, configs)
        assert name == "PAT R 5th"

    def test_match_contains(self, tmp_path):
        """Matches a file by contains on B2."""
        path = _make_xlsx(tmp_path, "swst.xlsx", {
            "B2": "Single Word Spelling Test Scoring Templates"
        })
        configs = [
            ("SWST", _config(keys=[
                {"sheet": 0, "cell": "B2", "contains": [
                    "single word spelling test", "scoring templates"
                ]}
            ])),
        ]
        name, cfg = identify_file(path, configs)
        assert name == "SWST"

    def test_contains_partial_miss(self, tmp_path):
        """Does not match when only some contains fragments are present."""
        path = _make_xlsx(tmp_path, "partial.xlsx", {
            "B2": "Single Word Spelling Test"
        })
        configs = [
            ("SWST", _config(keys=[
                {"sheet": 0, "cell": "B2", "contains": [
                    "single word spelling test", "scoring templates"
                ]}
            ])),
        ]
        name, cfg = identify_file(path, configs)
        assert name is None

    def test_match_multi_cell_keys(self, tmp_path):
        """Matches when ALL KEYS entries match."""
        path = _make_xlsx(tmp_path, "naplan.xlsx", {
            "A1": "APS Year 2024",
            "B1": "Reporting Test Results",
        })
        configs = [
            ("NAPLAN", _config(keys=[
                {"sheet": 0, "cell": "A1", "startswith": "aps year"},
                {"sheet": 0, "cell": "B1", "startswith": "reporting test"},
            ])),
        ]
        name, cfg = identify_file(path, configs)
        assert name == "NAPLAN"

    def test_multi_cell_partial_fail(self, tmp_path):
        """Does not match when only some KEYS entries match."""
        path = _make_xlsx(tmp_path, "partial.xlsx", {
            "A1": "APS Year 2024",
            "B1": "Something Else",
        })
        configs = [
            ("NAPLAN", _config(keys=[
                {"sheet": 0, "cell": "A1", "startswith": "aps year"},
                {"sheet": 0, "cell": "B1", "startswith": "reporting test"},
            ])),
        ]
        name, cfg = identify_file(path, configs)
        assert name is None

    def test_match_find_keys(self, tmp_path):
        """Matches a file by FIND_KEYS area search."""
        path = _make_xlsx(tmp_path, "adapt.xlsx", {
            "C5": "Test Something",
            "D8": "Date of Test",
            "B12": "PAT Reading Adaptive Result",
        })
        configs = [
            ("PAT-R Adapt", _config(find_keys=[
                {"sheet": 0, "startswith": "Test"},
                {"sheet": 0, "startswith": "Date"},
                {"sheet": 0, "startswith": "PAT Reading Adaptive"},
            ])),
        ]
        name, cfg = identify_file(path, configs, max_scan_rows=20, max_scan_cols=10)
        assert name == "PAT-R Adapt"

    def test_find_keys_partial_miss(self, tmp_path):
        """Does not match when only some FIND_KEYS entries are found."""
        path = _make_xlsx(tmp_path, "partial.xlsx", {
            "C5": "Test Something",
            "D8": "Date of Test",
        })
        configs = [
            ("PAT-R Adapt", _config(find_keys=[
                {"sheet": 0, "startswith": "Test"},
                {"sheet": 0, "startswith": "Date"},
                {"sheet": 0, "startswith": "PAT Reading Adaptive"},
            ])),
        ]
        name, cfg = identify_file(path, configs)
        assert name is None

    def test_priority_order(self, tmp_path):
        """First matching config by priority wins."""
        path = _make_xlsx(tmp_path, "multi.xlsx", {"A1": "PAT Test Data"})
        configs = [
            ("HighPri", _config(
                keys=[{"sheet": 0, "cell": "A1", "startswith": "pat"}],
                priority=1,
            )),
            ("LowPri", _config(
                keys=[{"sheet": 0, "cell": "A1", "startswith": "pat"}],
                priority=2,
            )),
        ]
        name, cfg = identify_file(path, configs)
        assert name == "HighPri"

    def test_keys_checked_before_find_keys(self, tmp_path):
        """KEYS match takes precedence over FIND_KEYS within same config."""
        path = _make_xlsx(tmp_path, "both.xlsx", {"A1": "Specific Value"})
        configs = [
            ("ByKeys", _config(keys=[
                {"sheet": 0, "cell": "A1", "startswith": "specific value"}
            ])),
            ("ByFind", _config(find_keys=[
                {"sheet": 0, "startswith": "Specific"},
            ])),
        ]
        name, cfg = identify_file(path, configs)
        assert name == "ByKeys"

    def test_no_match_returns_none(self, tmp_path):
        """Returns (None, None) when no config matches."""
        path = _make_xlsx(tmp_path, "unknown.xlsx", {"A1": "Random Data"})
        configs = [
            ("PAT", _config(keys=[
                {"sheet": 0, "cell": "A1", "startswith": "pat reading"}
            ])),
        ]
        name, cfg = identify_file(path, configs)
        assert name is None
        assert cfg is None

    def test_unsupported_extension(self, tmp_path):
        """Returns (None, None) for unsupported file types."""
        path = tmp_path / "file.txt"
        path.write_text("hello")
        name, cfg = identify_file(str(path), [])
        assert name is None

    def test_csv_match(self, tmp_path):
        """Identifies a CSV file correctly."""
        path = _make_csv(tmp_path, "data.csv", [
            ["FirstName", "Surname", "StudentNumber"],
            ["Jane", "Doe", "123"],
        ])
        configs = [
            ("EA", _config(
                keys=[
                    {"sheet": 0, "cell": "A1", "startswith": "firstname"},
                    {"sheet": 0, "cell": "B1", "startswith": "surname"},
                    {"sheet": 0, "cell": "C1", "startswith": "studentnumber"},
                ],
                fmt="csv",
            )),
        ]
        name, cfg = identify_file(path, configs)
        assert name == "EA"

    def test_format_mismatch_skipped(self, tmp_path):
        """Config for xlsx doesn't match a csv file."""
        path = _make_csv(tmp_path, "data.csv", [["Test"]])
        configs = [
            ("OnlyXlsx", _config(keys=[
                {"sheet": 0, "cell": "A1", "startswith": "test"}
            ], fmt="xlsx")),
        ]
        name, cfg = identify_file(path, configs)
        assert name is None

    def test_case_insensitive_matching(self, tmp_path):
        """Matching is case insensitive via field_cleaner normalization."""
        path = _make_xlsx(tmp_path, "case.xlsx", {"A1": "PAT READING 5TH EDITION"})
        configs = [
            ("PAT", _config(keys=[
                {"sheet": 0, "cell": "A1", "startswith": "pat reading 5th edition"}
            ])),
        ]
        name, cfg = identify_file(path, configs)
        assert name == "PAT"

    def test_whitespace_insensitive_matching(self, tmp_path):
        """Matching ignores extra whitespace via field_cleaner."""
        path = _make_xlsx(tmp_path, "space.xlsx", {"A1": "  PAT  Reading  5th "})
        configs = [
            ("PAT", _config(keys=[
                {"sheet": 0, "cell": "A1", "startswith": "pat reading 5th"}
            ])),
        ]
        name, cfg = identify_file(path, configs)
        assert name == "PAT"


# === TESTS: identify_file with bundled YAML ===

class TestIdentifyWithBundledConfig:
    """Test identification using the actual bundled test_identifiers.yaml."""

    @pytest.fixture
    def configs(self):
        from Finders.File_sorter.config_loader import load_test_configs
        return load_test_configs()

    def test_pat_r_5th_ol(self, tmp_path, configs):
        path = _make_xlsx(tmp_path, "pat.xlsx", {
            "A1": "PAT Reading 5th Edition Online Results"
        })
        name, cfg = identify_file(path, configs)
        assert name == "PAT R 5th OL"

    def test_running_records(self, tmp_path, configs):
        path = _make_xlsx(tmp_path, "rr.xlsx", {
            "B2": "Running Record Scoring Sheet"
        })
        name, cfg = identify_file(path, configs)
        assert name == "RUNNING RECORDS"

    def test_sssr(self, tmp_path, configs):
        path = _make_xlsx(tmp_path, "sssr.xlsx", {"A1": "SSSR Report 2024"})
        name, cfg = identify_file(path, configs)
        assert name == "NAPLAN SSSR"

    def test_unidentified(self, tmp_path, configs):
        path = _make_xlsx(tmp_path, "random.xlsx", {"A1": "Nothing matches"})
        name, cfg = identify_file(path, configs)
        assert name is None


# === TESTS: _match_entry ===

class TestMatchEntry:
    """Tests for the _match_entry helper."""

    def test_startswith_match(self):
        assert _match_entry("patreading5th", {"startswith": "pat reading"})

    def test_startswith_no_match(self):
        assert not _match_entry("something", {"startswith": "pat"})

    def test_contains_all_match(self):
        assert _match_entry(
            "singlewordspellingtestscoringtemplates",
            {"contains": ["single word spelling test", "scoring templates"]},
        )

    def test_contains_partial_miss(self):
        assert not _match_entry(
            "singlewordspellingtest",
            {"contains": ["single word spelling test", "scoring templates"]},
        )

    def test_no_match_type(self):
        assert not _match_entry("anything", {"cell": "A1"})
