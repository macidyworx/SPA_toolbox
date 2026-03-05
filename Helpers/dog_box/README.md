# dog_box Module Overview

wxPython-based file selection dialogs for opening Excel files. Two use cases:

1. **Single reference file** (`ssotsif.py`) — load a SIF or SSOT that will be accessed multiple times.
2. **Working files** (`work_files.py`) — select files or a folder to process in batch.

## Contents

- **ssotsif.py**: SIF and SSOT file selection with validation.
  - `select_sif()` — pick a SIF file, validates row 2 headers (CalendarYear, YearLevel, Surname, Firstname, StudentID in columns A-E)
  - `select_ssot()` — pick an SSOT file, prompts user for header row, old ID column, new ID column
  - `select_single_file(mode)` — convenience wrapper, mode is `'sif'`, `'ssot'`, or `'choose'`

- **work_files.py**: Working file/folder selection.
  - `select_work_files(extensions)` — user chooses files or a folder; folder selection walks subfolders recursively

## Usage

```python
from Helpers.dog_box import select_sif, select_ssot, select_work_files

# --- SIF ---
sif_path = select_sif()
# Returns: str path or None

# --- SSOT ---
ssot = select_ssot()
# Returns: {"path": str, "header_row": int, "old_id_col": str, "new_id_col": str} or None

# --- Let user choose SIF or SSOT ---
from Helpers.dog_box import select_single_file
result = select_single_file("choose")

# --- Working files ---
files = select_work_files([".xlsx", ".xls"])
# Returns: list of file paths, or None if cancelled
```

## SIF Validation

Row 2 of the selected file must contain these headers in order:

| Column | Header        |
|--------|---------------|
| A      | CalendarYear  |
| B      | YearLevel     |
| C      | Surname       |
| D      | Firstname     |
| E      | StudentID     |

Comparison is case-insensitive and strips whitespace. Data is expected from row 3 onward.

## SSOT Dialog

After file selection, the user is prompted for:
- **Header row number** (spinner, default 1)
- **Old ID column** (e.g. "A")
- **New ID column** (e.g. "B")

Both column inputs are validated as valid Excel column letters.

## Testing

```sh
pytest Helpers/dog_box/tests/
```
