"""
base_reader.py - Abstract base for format-specific file readers.
"""

from abc import ABC, abstractmethod

from Helpers.Clean_fields.clean_field import field_cleaner


class BaseReader(ABC):
    """Base class for file readers used by the file identifier."""

    @abstractmethod
    def read_cell(self, filepath, sheet, cell_ref):
        """Read and normalize a single cell value.

        Args:
            filepath: Path to the file.
            sheet: Sheet index (int, 0-based) or sheet name (str).
            cell_ref: Cell reference in A1 notation (e.g. "B2").

        Returns:
            Normalized string value, or empty string if cell is empty/error.
        """

    @abstractmethod
    def scan_area(self, filepath, sheet, max_rows=20, max_cols=30):
        """Scan an area and return all normalized cell values.

        Args:
            filepath: Path to the file.
            sheet: Sheet index (int, 0-based) or sheet name (str).
            max_rows: Maximum rows to scan.
            max_cols: Maximum columns to scan.

        Returns:
            List of normalized non-empty string values found in the area.
        """

    @staticmethod
    def _normalize(value):
        """Normalize a cell value to a cleaned string."""
        if value is None:
            return ""
        return field_cleaner(str(value), strip_spaces=True)
