# Last_row_finder Module Overview

Find the actual last row with data in an Excel column. Works around openpyxl's `max_row` reporting phantom rows from activated-but-empty cells.

## Contents

- **real_last_row.py**: Core utility.
  - `ws_last_row(ws, column)` — finds last data row on an already-open worksheet
  - `get_last_row(file_path, sheet, column)` — convenience wrapper that opens the file for you
- **test_last_row.py**: pytest suite.

## Usage

```python
from Helpers.Last_row_finder import get_last_row, ws_last_row

# Quick one-off lookup
last = get_last_row("data.xlsx", "Sheet1", "A")

# Multiple columns from the same file (avoids re-opening)
from openpyxl import load_workbook
wb = load_workbook("data.xlsx", data_only=True)
ws = wb["Sheet1"]
last_a = ws_last_row(ws, "A")
last_b = ws_last_row(ws, "B")
wb.close()
```

## Options

| Parameter   | Type       | Description                                          |
|-------------|------------|------------------------------------------------------|
| `file_path` | `str`      | Path to the Excel file (get_last_row only)           |
| `sheet`     | `str/int`  | Sheet name or 0-based index (get_last_row only)      |
| `ws`        | `Worksheet`| An openpyxl Worksheet object (ws_last_row only)      |
| `column`    | `str/int`  | Column letter (e.g. `'A'`) or number (e.g. `1`)     |

Both functions return the last row number with data (`int`), or `None` if the column is empty. Whitespace-only cells are treated as empty.

## Testing

```sh
pytest Helpers/Last_row_finder/test_last_row.py
```
