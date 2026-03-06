"""
csv_reader.py - Reader for .csv files using stdlib csv.
"""

import csv

from Finders.File_sorter.cell_utils import parse_cell_ref
from Finders.File_sorter.readers.base_reader import BaseReader


class CsvReader(BaseReader):
    """Reads .csv files using the standard library csv module."""

    def read_cell(self, filepath, sheet, cell_ref):
        row, col = parse_cell_ref(cell_ref)
        rows = self._load_rows(filepath, max_rows=row)
        # Convert from 1-indexed to 0-indexed
        if row - 1 >= len(rows):
            return ""
        target_row = rows[row - 1]
        if col - 1 >= len(target_row):
            return ""
        return self._normalize(target_row[col - 1])

    def scan_area(self, filepath, sheet, max_rows=20, max_cols=30):
        rows = self._load_rows(filepath, max_rows=max_rows)
        results = []
        for row in rows:
            for value in row[:max_cols]:
                normalized = self._normalize(value)
                if normalized:
                    results.append(normalized)
        return results

    @staticmethod
    def _load_rows(filepath, max_rows):
        """Load up to max_rows from a CSV file."""
        rows = []
        with open(filepath, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                rows.append(row)
        return rows
