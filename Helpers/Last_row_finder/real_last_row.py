# This module provides functions to find the last row with data in Excel columns.

import openpyxl
from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string, get_column_letter

def get_last_row(file_path, sheet, column):
    """
    Finds the last row with data in a specific column.
    
    Args:
        file_path (str): Path to the Excel file.
        sheet (str or int): Name of the sheet (str) or index of the sheet (int, 0-based).
        column (str or int): Column letter (e.g., 'A') or number (e.g., 1).
    
    Returns:
        int or None: The last row number with data, or None if no data found in the column.
    """
    wb = load_workbook(file_path, data_only=True)
    
    if isinstance(sheet, int):
        if sheet < 0 or sheet >= len(wb.worksheets):
            raise ValueError(f"Sheet index {sheet} is out of range. Valid indices: 0 to {len(wb.worksheets)-1}")
        ws = wb.worksheets[sheet]
        actual_sheet = ws.title
    else:
        if sheet not in wb.sheetnames:
            raise ValueError(f"Sheet '{sheet}' not found in the workbook.")
        ws = wb[sheet]
        actual_sheet = sheet
    
    if isinstance(column, str):
        col_num = column_index_from_string(column)
    else:
        col_num = column
    
    # Find the last row with data in this column
    for row in range(ws.max_row, 0, -1):
        cell = ws.cell(row=row, column=col_num)
        if cell.value is not None and str(cell.value).strip() != "":
            return row
    
    return None  # No data found in the column

