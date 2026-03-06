# Mission: Implement PATonline Unique ID Validator

## 1. Objective

Create a script (`PATonline_UID_Validator.py`) that validates the Unique ID column format in PATonline Excel files, moves files with invalid IDs to a dedicated subfolder, and provides progress feedback via both UI dialogs (standalone) and callbacks (module mode).

## 2. Scope

**Included:**
- User selects working files (folder or individual .xlsx/.xls files)
- User selects output folder
- User selects expected ID format from: `ABC0001` (letters+digits), `182815548` (all digits, 9 chars), `5548` (all digits, 4 chars)
- Scan worksheet for "Unique ID" header (case/whitespace-insensitive using `field_cleaner`)
- Validate ALL non-empty values in Unique ID column against selected format
- If ANY cell is empty OR doesn't match format → move file to `output_dir/Invalid_UniqueID/`
- If ALL values match format (and no empty cells) → leave file in original location
- If "Unique ID" column not found → leave file in original location (don't move)
- Handle file move conflicts: prompt user for each duplicate (overwrite/skip/rename)
- Support progress callbacks for integration into other workflows
- Standalone execution with wxPython progress dialog
- Dual-mode design: usable as module (`import PATonline_UID_Validator`) or script (`python PATonline_UID_Validator.py`)

**Excluded:**
- Modifying file contents
- Validating other columns
- Creating output subfolders beyond `Invalid_UniqueID/`
- Auto-resolving file conflicts (always prompt user)

## 3. Assumptions

- Files are .xlsx or .xls format (handled by `select_work_files`)
- "Unique ID" header is in rows 1-20, columns A-M (scanned like PATonline-FINDER)
- Data rows start after header row (caller responsible for locating header)
- All data to validate is in column containing "Unique ID" header
- User can run with `.venv/bin/pytest` for test execution
- Water_logged logger available (same as PATonline-FINDER pattern)
- Field normalization via `field_cleaner(str(value), strip_spaces=True)` for header matching

## 4. Affected Areas

**Files/Modules:**
- `Finders/PATonline_UID_Validator.py` (new file)
- `Finders/test_patonline_uid_validator.py` (new test file)
- `Helpers/dog_box/__init__.py` (no changes needed; already exports `select_work_files`, `select_output_folder`)
- `Helpers/Clean_fields/clean_field.py` (existing; used for header matching)

**Dependencies:**
- Internal: `Helpers.Clean_fields.clean_field::field_cleaner`
- Internal: `Helpers.dog_box::select_work_files, select_output_folder`
- External: `openpyxl`, `xlrd` (Excel reading)
- External: `wx` (wxPython for dialogs)
- External: `water_logged.the_logger::THElogger` (logging)

## 5. Risks

**Technical Risks:**
- **Risk**: Determining data row range when header row is not row 1
  - **Mitigation**: After locating header, scan all rows from (header_row + 1) to worksheet max_row, allowing script to work with files that have preamble rows or metadata above headers
- **Risk**: Handling very large Excel files (performance)
  - **Mitigation**: Use `read_only=True` when loading workbooks; progress callbacks allow UI to remain responsive
- **Risk**: xlrd limitations (.xls parsing differences vs .xlsx)
  - **Mitigation**: Test both file formats; xlrd fallback pattern from PATonline-FINDER already proven

**Regressions:**
- Ensure PATonline-FINDER tests still pass (no changes to shared modules)
- Ensure existing dog_box and Clean_fields tests unaffected (read-only usage)

**Edge Cases:**
- File has no Unique ID column: leave in place (no move, no error) ✓
- File with empty Unique ID column (header found, but all values empty): move to Invalid_UniqueID ✓
- File with mixed empty/non-empty values: move if ANY empty ✓
- File with values partially matching format: move if ANY non-match ✓
- Format `ABC0001`: Validate exactly 3 uppercase letters + 4 digits; case-sensitive for letters
- Format `182815548`: Validate exactly 9 digits
- Format `5548`: Validate exactly 4 digits
- File already exists in Invalid_UniqueID: prompt user (overwrite/skip/rename)

## 6. Implementation Strategy

### 6.1 File Structure

```
PATonline_UID_Validator.py
├── IMPORTS
├── GLOBAL CONSTANTS
│   ├── TARGET_HEADERS (map "Unique ID" → key, reuse PATonline-FINDER pattern)
│   ├── SCAN_COLUMNS, SCAN_ROWS (same as PATonline-FINDER)
│   └── ID_FORMATS (dict: format name → regex/validator function)
├── ProgressDialog (class: wxPython dialog with counter, filename, progress bar, cancel)
├── UID_FORMAT_VALIDATOR (class: encapsulate format validation logic)
├── Helper Functions
│   ├── find_uid_header(worksheet) → column_letter or None
│   ├── get_uid_column_data(worksheet, column_letter) → list of (row_num, value) tuples
│   └── validate_uid_format(values, format_name) → (is_valid: bool, invalid_rows: list)
├── PATonlineUIDValidator (main class)
│   ├── __init__() → setup logger
│   ├── validate_file(file_path) → (has_uid_col: bool, is_valid: bool, invalid_rows: list)
│   ├── process_file(file_path, output_dir) → (moved: bool, reason: str)
│   └── run(progress_callback=None)
├── main() → entry point for standalone execution
└── _create_progress_callback() → closure for dialog lifecycle
```

### 6.2 ID Format Validation

Create `UID_FORMAT_VALIDATOR` class with methods for each format:

```python
class UID_FORMAT_VALIDATOR:
    """Validates Unique ID values against expected format."""

    FORMATS = {
        'ABC0001': 'ABC0001 (3 letters + 4 digits)',
        '182815548': '182815548 (9 digits)',
        '5548': '5548 (4 digits)',
    }

    @staticmethod
    def is_valid_ABC0001(value: str) -> bool:
        """Check: exactly 3 uppercase letters + 4 digits."""
        # Pattern: ^[A-Z]{3}\d{4}$

    @staticmethod
    def is_valid_182815548(value: str) -> bool:
        """Check: exactly 9 digits."""
        # Pattern: ^\d{9}$

    @staticmethod
    def is_valid_5548(value: str) -> bool:
        """Check: exactly 4 digits."""
        # Pattern: ^\d{4}$

    @classmethod
    def validate(cls, format_name: str, value: str) -> bool:
        """Route to appropriate validator; return True if valid."""
        if format_name == 'ABC0001':
            return cls.is_valid_ABC0001(value)
        elif format_name == '182815548':
            return cls.is_valid_182815548(value)
        elif format_name == '5548':
            return cls.is_valid_5548(value)
        return False
```

### 6.3 Header Detection & Column Data Extraction

Reuse PATonline-FINDER pattern:

```python
def find_uid_header(worksheet):
    """
    Scan worksheet cells A1-M20 for "Unique ID" header.
    Uses field_cleaner for robust text normalization.

    Returns:
        str: Column letter (e.g., 'C') if found, None otherwise
    """
    normalized_target = field_cleaner("Unique ID", strip_spaces=True)

    for row in SCAN_ROWS:
        for col in SCAN_COLUMNS:
            cell = worksheet[f'{col}{row}']
            if cell.value is not None:
                cell_text = field_cleaner(str(cell.value), strip_spaces=True)
                if cell_text == normalized_target:
                    return col
    return None
```

```python
def get_uid_column_data(worksheet, column_letter):
    """
    Extract all values from Unique ID column, starting after header row.

    Returns:
        list of (row_number, value) tuples
        Includes empty cells (value=None or '')
    """
    data = []
    # Find header row first
    header_row = None
    for row in SCAN_ROWS:
        cell_value = worksheet[f'{column_letter}{row}'].value
        if cell_value is not None and field_cleaner(str(cell_value), strip_spaces=True) == field_cleaner("Unique ID", strip_spaces=True):
            header_row = row
            break

    if header_row is None:
        return []

    # Scan from header_row+1 to max_row
    for row in range(header_row + 1, worksheet.max_row + 1):
        cell = worksheet[f'{column_letter}{row}']
        data.append((row, cell.value))

    return data
```

### 6.4 Validation Logic

```python
def validate_uid_format(column_data, format_name):
    """
    Validate all values in UID column against format.

    Args:
        column_data: list of (row_num, value) tuples
        format_name: 'ABC0001', '182815548', or '5548'

    Returns:
        tuple: (is_valid: bool, invalid_rows: list of row_num)

    Logic:
        - If ANY value is empty → is_valid = False
        - If ANY value doesn't match format regex → is_valid = False
        - Otherwise → is_valid = True
    """
    invalid_rows = []

    for row_num, value in column_data:
        # Empty cell check
        if value is None or str(value).strip() == '':
            invalid_rows.append((row_num, "Empty"))
            continue

        # Format check
        if not UID_FORMAT_VALIDATOR.validate(format_name, str(value).strip()):
            invalid_rows.append((row_num, str(value)))

    is_valid = len(invalid_rows) == 0
    return (is_valid, invalid_rows)
```

### 6.5 Main PATonlineUIDValidator Class

```python
class PATonlineUIDValidator:
    """Validates Unique ID column in PATonline Excel files."""

    def __init__(self):
        """Initialize logger."""
        # Setup THElogger same as PATonline-FINDER

    def validate_file(self, file_path):
        """
        Check if file's Unique ID column is valid.

        Returns:
            dict: {
                'has_uid_column': bool,
                'is_valid': bool,
                'invalid_rows': list,  # [(row_num, reason), ...]
                'error': str or None
            }
        """
        # Try openpyxl, fallback to xlrd
        # Call find_uid_header() → if None, return has_uid_column=False, is_valid=N/A
        # Call get_uid_column_data() → get all values
        # Call validate_uid_format() → check all values
        # Return results

    def prompt_file_conflict(self, target_path):
        """
        Prompt user when file already exists in output folder.

        Returns:
            'overwrite', 'skip', 'rename', or None if user cancels
        """
        # wxPython dialog with three buttons

    def process_file(self, file_path, output_dir, format_name):
        """
        Validate file and move if invalid (to Invalid_UniqueID/).

        Args:
            file_path: path to file
            output_dir: root output directory
            format_name: expected ID format

        Returns:
            dict: {
                'moved': bool,
                'reason': str,
                'error': str or None
            }

        Logic:
            1. Call validate_file(file_path)
            2. If has_uid_column=False → skip (don't move, log at DEBUG)
            3. If is_valid=True → skip (don't move, log at INFO)
            4. If is_valid=False → move to Invalid_UniqueID/
               - Create Invalid_UniqueID/ subfolder
               - Check if target file exists
               - If exists, call prompt_file_conflict()
               - Move file, log result
        """

    def run(self, progress_callback=None):
        """
        Main workflow.

        Args:
            progress_callback (callable, optional):
                Signature: callback(current_index, total_count, filename) -> bool
                Returns: True to continue, False to cancel

        Flow:
            1. Prompt user for input files
            2. Prompt user for output folder
            3. Prompt user for expected ID format (dialog with radio buttons)
            4. For each file:
               - Check progress_callback
               - Call process_file()
               - Log result
            5. Finalize logger report
        """
```

### 6.6 Standalone Execution

```python
def main():
    """Entry point for standalone execution."""
    # Print banner (like PATonline-FINDER)
    # Create wx.App(False)
    # Create PATonlineUIDValidator()
    # Call validator.run(progress_callback=_create_progress_callback())
    # app.Destroy()

def _create_progress_callback():
    """
    Create progress callback closure that manages ProgressDialog lifecycle.

    Returns:
        Callable with signature (current_index, total_count, filename) -> bool
    """
    # Same pattern as PATonline-FINDER: nonlocal dialog, create on first call
```

### 6.7 ProgressDialog Class

```python
class ProgressDialog(wx.Dialog):
    """Modal progress dialog with file counter, filename, progress bar, cancel."""

    def __init__(self, total_files, parent=None):
        # Counter label: "File X of Y"
        # Filename label: "Processing: filename.xlsx"
        # Progress gauge: 0 to total_files
        # Cancel button

    def update(self, current_index, filename):
        # Update counter and filename labels
        # Update progress gauge
        # Call wx.SafeYield() to keep UI responsive

    def is_cancelled(self):
        # Return _cancelled flag

    def on_cancel(self, event):
        # Set _cancelled = True
        # EndModal(wx.ID_CANCEL)
```

### 6.8 ID Format Selection Dialog

Create helper function to prompt user for ID format:

```python
def prompt_id_format():
    """
    Prompt user to select expected ID format via wxPython dialog.

    Returns:
        str: 'ABC0001', '182815548', '5548', or None if cancelled
    """
    dlg = wx.SingleChoiceDialog(
        None,
        "Select expected Unique ID format:",
        "Unique ID Format",
        [
            "ABC0001 (3 letters + 4 digits)",
            "182815548 (9 digits)",
            "5548 (4 digits)",
        ]
    )
    dlg.Centre()
    try:
        if dlg.ShowModal() == wx.ID_OK:
            selection = dlg.GetStringSelection()
            # Map back to format name
            return ['ABC0001', '182815548', '5548'][dlg.GetSelection()]
        return None
    finally:
        dlg.Destroy()
```

## 7. Validation Strategy

**Tests to Create:**

### Unit Tests: UID_FORMAT_VALIDATOR

- Test: `test_abc0001_valid` — Validate correct ABC0001 format (e.g., "ABC0001", "XYZ9999")
- Test: `test_abc0001_invalid_letters` — Reject lowercase letters (e.g., "abc0001")
- Test: `test_abc0001_invalid_length` — Reject wrong length (e.g., "AB01", "ABCD0001")
- Test: `test_abc0001_invalid_no_digits` — Reject no digits (e.g., "ABCDEFG")
- Test: `test_182815548_valid` — Validate correct 9-digit format (e.g., "182815548", "000000001")
- Test: `test_182815548_invalid_length` — Reject 8 or 10 digits
- Test: `test_182815548_invalid_letters` — Reject non-digits (e.g., "18281554A")
- Test: `test_5548_valid` — Validate correct 4-digit format (e.g., "5548", "0001")
- Test: `test_5548_invalid_length` — Reject 3 or 5 digits
- Test: `test_5548_invalid_letters` — Reject non-digits (e.g., "554A")

### Unit Tests: find_uid_header()

- Test: `test_find_uid_header_basic` — Find "Unique ID" in standard position (e.g., C1)
- Test: `test_find_uid_header_case_insensitive` — Find "unique id" (lowercase)
- Test: `test_find_uid_header_extra_spaces` — Find "Unique  ID" (extra whitespace)
- Test: `test_find_uid_header_not_found` — Return None when header absent
- Test: `test_find_uid_header_unicode` — Find with unicode variations (if applicable)

### Unit Tests: get_uid_column_data()

- Test: `test_get_uid_column_data_basic` — Extract values from column C, rows 2-5 (standard case)
- Test: `test_get_uid_column_data_with_empty` — Include empty cells in results
- Test: `test_get_uid_column_data_mixed` — Mix of populated and empty rows
- Test: `test_get_uid_column_data_no_header` — Return empty list if header not found

### Unit Tests: validate_uid_format()

- Test: `test_validate_uid_all_valid` — All values match format → is_valid=True, invalid_rows=[]
- Test: `test_validate_uid_with_empty` — Any empty value → is_valid=False, invalid_rows includes empty row
- Test: `test_validate_uid_with_mismatch` — Any non-matching value → is_valid=False, invalid_rows includes mismatched row
- Test: `test_validate_uid_mixed` — Mix of valid, empty, and mismatched → is_valid=False

### Integration Tests: PATonlineUIDValidator.validate_file()

- Test: `test_validate_file_xlsx_no_uid_column` — .xlsx file without UID column → has_uid_column=False
- Test: `test_validate_file_xlsx_valid_abc0001` — .xlsx file with all valid ABC0001 → is_valid=True
- Test: `test_validate_file_xlsx_invalid_abc0001` — .xlsx file with invalid values → is_valid=False, invalid_rows populated
- Test: `test_validate_file_xls_valid_9digit` — .xls file with valid 9-digit → is_valid=True
- Test: `test_validate_file_corrupted` — Corrupted file → error field populated

### Integration Tests: PATonlineUIDValidator.process_file()

- Test: `test_process_file_no_uid_column` — File without UID column → moved=False, reason="UID column not found"
- Test: `test_process_file_valid` — File with valid UIDs → moved=False, reason="All UIDs valid"
- Test: `test_process_file_invalid_moved` — File with invalid UIDs → moved=True to Invalid_UniqueID/
- Test: `test_process_file_conflict_overwrite` — Existing file in Invalid_UniqueID, user chooses overwrite → file moved and replaced
- Test: `test_process_file_conflict_skip` — Existing file in Invalid_UniqueID, user chooses skip → file NOT moved
- Test: `test_process_file_conflict_rename` — Existing file in Invalid_UniqueID, user chooses rename → file moved with new name

**User Verification:**

Run tests with: `pytest Finders/test_patonline_uid_validator.py -v`

All tests must pass before marking task complete.

**Manual Checks:**

- Standalone execution: `python Finders/PATonline_UID_Validator.py`
  - Verify banner displays correctly
  - Verify file selection dialog opens
  - Verify output folder selection dialog opens
  - Verify ID format dialog shows three options
  - Verify progress dialog updates during processing
  - Verify files moved to `output_dir/Invalid_UniqueID/`
  - Verify conflict prompt works (overwrite/skip/rename)
  - Verify logger produces report after completion

- Module usage: Verify callable from another script
  ```python
  from Finders.PATonline_UID_Validator import PATonlineUIDValidator
  validator = PATonlineUIDValidator()
  # Call with custom progress_callback
  ```

## 8. Rollback Plan

1. **If file move fails**: Script logs warning and continues to next file (no partial moves)
2. **If invalid file is moved**: User can manually move from `Invalid_UniqueID/` back to source folder or recover from backup
3. **If progress_callback causes issues**: Script catches callback exceptions and continues processing (logged as warning)
4. **If wxPython dialog unavailable**: Module mode allows headless usage with `progress_callback` parameter
5. **Complete rollback**: Delete `Invalid_UniqueID/` subfolder and move files back to original location manually

## 9. Code Location & Dependencies

**Primary file**: `/home/bigbox/Documents/Mworx/SPA_toolbox/Finders/PATonline_UID_Validator.py`

**Test file**: `/home/bigbox/Documents/Mworx/SPA_toolbox/Finders/test_patonline_uid_validator.py`

**Dependencies (already in project)**:
- `Helpers.Clean_fields.clean_field.field_cleaner` ← for header matching
- `Helpers.dog_box.select_work_files` ← for file selection
- `Helpers.dog_box.select_output_folder` ← for output folder selection
- `openpyxl.load_workbook` ← for .xlsx files
- `xlrd.open_workbook` ← for .xls files
- `water_logged.the_logger.THElogger` ← for logging
- `wx` ← for dialogs (already used by PATonline-FINDER)

**Code style**: Follow PATonline-FINDER conventions:
- Use section markers (IMPORTS, GLOBAL CONSTANTS, PROGRESS DIALOG, etc.)
- Dual-mode design with `if __name__ == "__main__": main()`
- Logger initialization with fallback config path lookup
- Progress callback parameter with type checking in `run()`
- Reuse `field_cleaner` for all text matching
- All file operations logged at appropriate levels (DEBUG/INFO/WARNING)
