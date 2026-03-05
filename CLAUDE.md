# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SPA_toolbox** is a collection of reusable Python helper modules for working with Excel files for client data processing. The toolbox provides text normalization, file selection dialogs, and utilities that address common pain points with openpyxl and messy real-world data.

## Project Structure

```
Helpers/
  Clean_fields/          # Text normalization for name/ID matching
    clean_field.py       # field_cleaner() — unicode, case, whitespace normalization
    test_clean_fields.py

  Last_row_finder/       # Find actual last data row (works around openpyxl max_row bug)
    real_last_row.py     # get_last_row(), ws_last_row()
    test_last_row.py

  dog_box/               # wxPython file selection dialogs
    ssotsif.py           # select_sif(), select_ssot(), select_single_file()
    work_files.py        # select_work_files()
    tests/
      test_ssotsif.py
      test_work_files.py
```

## Using the Helpers

### Clean_fields — Text normalization

```python
from Helpers.Clean_fields.clean_field import field_cleaner

# Default: lowercase, strip all spaces (ideal for name/ID matching)
field_cleaner("Van Owen")        # -> "vanowen"
field_cleaner("  ABC 0001  ")    # -> "abc0001"

# Preserve spaces when needed
field_cleaner("Hello World", strip_spaces=False)  # -> "hello world"
```

Options: `lowercase`, `collapse_whitespace`, `strip_spaces` (default True), `strip_bom`, `unicode_form`.

### Last_row_finder — Actual last data row

```python
from Helpers.Last_row_finder import get_last_row, ws_last_row

# One-off lookup
last = get_last_row("data.xlsx", "Sheet1", "A")

# Multiple columns from the same file (avoids re-opening)
from openpyxl import load_workbook
wb = load_workbook("data.xlsx", data_only=True)
ws = wb["Sheet1"]
last_a = ws_last_row(ws, "A")
last_b = ws_last_row(ws, "B")
wb.close()
```

### dog_box — File selection dialogs

```python
from Helpers.dog_box import select_sif, select_ssot, select_work_files

# SIF: validates row 2 headers (CalendarYear, YearLevel, Surname, Firstname, StudentID)
sif_path = select_sif()

# SSOT: prompts user for header row, old ID col, new ID col
ssot = select_ssot()  # returns dict with path, header_row, old_id_col, new_id_col

# Working files: user picks files or folder, caller specifies extensions
files = select_work_files([".xlsx", ".xls"])
```

## Commands

**Always activate the project virtual environment (`.venv`) before running commands.**

```bash
source .venv/bin/activate
```

## Testing

**Do not run tests during implementation.** Create tests and list them for user verification.

When tests need to be run, use these commands:

```bash
# All tests
.venv/bin/pytest

# Individual modules
.venv/bin/pytest Helpers/Clean_fields/test_clean_fields.py -v
.venv/bin/pytest Helpers/Last_row_finder/test_last_row.py -v
.venv/bin/pytest Helpers/dog_box/tests/ -v
```

## Coding Standards

### Naming

| Element            | Convention       |
|--------------------|------------------|
| Functions/variables | `snake_case`    |
| Classes            | `PascalCase`     |
| Constants          | `SCREAMING_SNAKE` |

### Helpers should be dependency-free

Helper modules should not depend on external project utilities (e.g. loggers). They should only use standard library, their own sibling helpers, and declared pip dependencies (openpyxl, wxPython).

### Commit Messages

```
feat: Brief description

- Change 1
- Change 2
```

## Application Architecture

### Dual-Mode Design

**All apps must be usable as both modules AND standalone scripts.**

```python
"""
my_app.py - Description of what this app does.
"""

# === IMPORTS ===
import sys

# === MAIN FUNCTIONS/CLASSES ===
class MyApp:
    def __init__(self, config):
        self.config = config

    def run(self):
        """Main application logic."""
        pass

def main():
    """Entry point for standalone execution."""
    app = MyApp(config={})
    app.run()

# === STANDALONE EXECUTION ===
if __name__ == "__main__":
    main()
```

This allows:

- `python my_app.py` - Run standalone
- `from my_app import MyApp` - Use as module

## Ignore

Do not read or reference anything in the `ZZHISTORY/` folder.

## Task Workflow

1. Read and understand existing code before modifying
2. **Do not run tests during implementation** — create/update tests and list them for the user
3. If uncertain about a requirement or approach, ask for clarification — do not assume
