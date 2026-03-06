"""
xls_reader.py - Reader for .xls files using xlrd.
"""

import xlrd

from Finders.File_sorter.cell_utils import parse_cell_ref
from Finders.File_sorter.readers.base_reader import BaseReader


class XlsReader(BaseReader):
    """Reads .xls files using xlrd."""

    def read_cell(self, filepath, sheet, cell_ref):
        row, col = parse_cell_ref(cell_ref)
        wb = xlrd.open_workbook(filepath)
        try:
            ws = self._get_sheet(wb, sheet)
            # Convert from 1-indexed (A1 style) to 0-indexed (xlrd)
            if row - 1 >= ws.nrows or col - 1 >= ws.ncols:
                return ""
            value = ws.cell_value(row - 1, col - 1)
            return self._normalize(value)
        finally:
            wb.release_resources()

    def scan_area(self, filepath, sheet, max_rows=20, max_cols=30):
        wb = xlrd.open_workbook(filepath)
        try:
            ws = self._get_sheet(wb, sheet)
            results = []
            scan_rows = min(max_rows, ws.nrows)
            scan_cols = min(max_cols, ws.ncols)
            for r in range(scan_rows):
                for c in range(scan_cols):
                    value = ws.cell_value(r, c)
                    normalized = self._normalize(value)
                    if normalized:
                        results.append(normalized)
            return results
        finally:
            wb.release_resources()

    @staticmethod
    def _get_sheet(wb, sheet):
        if isinstance(sheet, int):
            return wb.sheet_by_index(sheet)
        return wb.sheet_by_name(sheet)
