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

Finders/
  File_sorter/             # Automatic file sorting by test type
    file_sorter.py         # FileSorter class — main sorting engine
    file_identifier.py     # identify_file() — YAML-driven file type matching
    config_loader.py       # load_test_configs() — YAML loader with validation
    path_resolver.py       # resolve_sort_path() — sort strategy templates
    unique_path.py         # get_unique_path() — duplicate filename handling
    file_cache.py          # FileCache — hash+mtime identification cache
    cell_utils.py          # parse_cell_ref() — A1 notation parser
    readers/               # Format-specific file readers
      xlsx_reader.py       # XlsxReader (openpyxl)
      xlsm_reader.py       # XlsmReader (openpyxl)
      xls_reader.py        # XlsReader (xlrd)
      csv_reader.py        # CsvReader (stdlib csv)
    test_configs/
      test_identifiers.yaml  # 45 test type definitions
    tests/
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

### File_sorter — Automatic file sorting by test type

```python
from Finders.File_sorter import FileSorter, identify_file, load_test_configs

# Sort all files in a folder (uses bundled YAML config)
sorter = FileSorter()
summary = sorter.sort_files("input_folder/", "SORTED/")
# summary["sorted"]       -> {"PAT R 5th OL": 3, "SSSR": 1, ...}
# summary["unidentified"] -> ["unknown_file.xlsx", ...]

# With callbacks (for GUI integration)
sorter = FileSorter(
    message_callback=my_log_func,
    progress_callback=lambda current, total, name: True,  # return False to cancel
)

# Identify a single file
configs = load_test_configs()
name, config = identify_file("student_data.xlsx", configs)

# Standalone
# python -m Finders.File_sorter.file_sorter <input_folder> <output_folder>
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
.venv/bin/pytest Finders/File_sorter/tests/ -v
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

### Using clean_field for text matching

**Always use `field_cleaner()` for any text comparison/matching operations.** This ensures robust handling of real-world data with unicode variations, extra whitespace, and mixed case.

**Critical pattern: Normalize both sides of the comparison while keeping source data readable:**

```python
from Helpers.Clean_fields.clean_field import field_cleaner

# ✓ CORRECT: Keep lookup table readable, normalize both sides
TARGET_HEADERS = {
    "Family name": "family_name",
    "Given name": "given_name",
    "Unique ID": "unique_id",
}

# When matching, normalize both lookup keys and incoming value
normalized_headers = {field_cleaner(k, strip_spaces=True): v for k, v in TARGET_HEADERS.items()}
incoming = field_cleaner(str(cell.value), strip_spaces=True)

if incoming in normalized_headers:
    result = normalized_headers[incoming]
```

**Benefits:**
- Better debuggability: Source code shows readable headers; if matching fails, you can trace exactly what `field_cleaner` produced
- Handles edge cases: unicode, extra whitespace, case variations all normalized consistently
- Single source of truth: Only one place to see what headers/values are expected

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

Do not read or reference anything in the `ZZHISTORY/` or `zzNOTES/` folder.

## Task Workflow

1. Read and understand existing code before modifying
2. **Do not run tests during implementation** — create/update tests and list them for the user
3. If uncertain about a requirement or approach, ask for clarification — do not assume
