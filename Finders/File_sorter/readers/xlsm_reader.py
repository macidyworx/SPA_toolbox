"""
xlsm_reader.py - Reader for .xlsm files using openpyxl.

Identical to xlsx_reader — openpyxl handles both formats.
"""

from Finders.File_sorter.readers.xlsx_reader import XlsxReader


class XlsmReader(XlsxReader):
    """Reads .xlsm files. Same as XlsxReader (openpyxl handles both)."""
    pass
