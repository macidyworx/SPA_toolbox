# Mission: Build PATUniqueID_Checker.py

## 1. Objective

Build PATUniqueID_Checker.py to validate Unique ID column values in Excel files against an expected format pattern (ABC0001, 182815548, or 5548). Files with invalid or empty Unique ID values are moved to an Invalid_UniqueID/ subfolder; valid files remain in place. Script runs standalone with progress dialogs or as an importable module with optional progress callback.

## 2. Scope

**Included:**
- Unique ID format validation for three predefined patterns (ABC0001 = alphanumeric, 182815548 = 9-digit numeric, 5548 = 4-digit numeric)
- Excel file scanning across both .xlsx and .xls formats
- Unique ID column header detection using field_cleaner normalization (handles case, unicode, whitespace)
- Per-file validation: if ANY Unique ID cell is empty or invalid format → move file to Invalid_UniqueID/
- File move workflow with user prompts on filename conflicts (overwrite/skip/rename options)
- Dual-mode architecture: standalone with progress dialog + importable module with progress_callback support
- Progress reporting: current_index (1-based), total_count, filename
- Output folder structure: valid files in root, invalid files in Invalid_UniqueID/ subfolder

**Excluded:**
- Modifying file contents or Excel data
- Validating other columns (Family name, Given name, Username)
- Support for non-Excel formats
- Recursive directory scanning (user selects folder, script processes files at that level only)
- Multi-sheet processing (process active/first sheet only)

## 3. Assumptions

- User selects working files folder containing .xlsx/.xls files to validate
- User selects output folder where categorized files will be moved
- User explicitly chooses one of three Unique ID formats via dialog
- Unique ID column header appears in first 20 rows and columns A-M (consistent with PATonline_FINDER pattern)
- Empty cells (None or empty string) in Unique ID column are treated as validation failures
- Files already at destination are handled via user prompt, not silent overwrite
- Project structure: PATUniqueID_Checker.py will be placed in Finders/ directory (alongside PATonline_FINDER.py)
- logging.ini config available in Finders/ or parent IDswappers/ directory
- Field_cleaner helper available for robust text normalization

## 4. Affected Areas

**Files/Modules:**
- New file: `/Finders/PATUniqueID_Checker.py` (main script)
- New test file: `/Finders/test_patuniqueID_checker.py` (test suite)
- Modified/referenced: `Helpers/Clean_fields/clean_field.py` (field_cleaner function - no changes)
- Referenced: `Helpers/dog_box/ssotsif.py` (select_work_files, select_output_folder)
- Referenced: `water_logged/the_logger.py` (THElogger for logging)

**Dependencies:**
- Internal: field_cleaner (text normalization), select_work_files, select_output_folder, THElogger
- External: openpyxl (read .xlsx), xlrd (read .xls), wxPython (dialogs), shutil (file operations)

## 5. Risks

**Technical Risks:**
- **Risk**: Files moved to Invalid_UniqueID/ cannot be easily recovered if user aborts or makes mistakes
  - **Mitigation**: Implement clear logging of all moves, provide rollback instructions in log messages, use "rename" conflict option instead of overwrite-by-default
- **Risk**: Large file counts (100+) may require long processing time, user might cancel mid-operation
  - **Mitigation**: Progress callback with cancellation support, log files processed before abort so user knows which files were moved

**Regressions:**
- None expected; new script does not modify existing modules or PATonline_FINDER logic

**Edge Cases:**
- Unique ID column header appears in multiple locations → first match (top-left scan order) is used
- File is corrupted or unreadable → caught by try-except, logged as warning, file left in place
- Output folder is same as source folder → files moved to Invalid_UniqueID/ subfolder within source
- Filename conflict in Invalid_UniqueID/ → user prompt with overwrite/skip/rename options
- User selects zero files → graceful exit with log message
- Unique ID header present but column contains all empty cells → all values fail validation, file moves to Invalid_UniqueID/

## 6. Implementation Strategy

1. **Define PATUniqueIDChecker class** with format validators and file processing methods
   - `__init__()`: Initialize logger (same pattern as PATonline_FINDER)
   - `validate_unique_id_format(value, format_type)`: Return True if value matches format, False otherwise
   - `find_unique_id_column(worksheet)`: Scan A1-M20 for "Unique ID" header using field_cleaner normalization, return column letter or None
   - `validate_file(file_path, format_type)`: Open file, locate Unique ID column, check all values against format, return (is_valid, reason) tuple
   - `process_file(file_path, output_dir, format_type)`: Validate file, move to Invalid_UniqueID/ if invalid, handle conflicts with user prompt, return success boolean
   - `run(format_type, progress_callback=None)`: Main workflow — select files, output folder, process each file, handle progress/cancellation

2. **Implement format validators** as static methods or class methods
   - ABC0001 format: regex `^[A-Za-z]{3}[0-9]{4}$` (3 letters + 4 digits, case-insensitive in code but case preserved in input)
   - 182815548 format: regex `^[0-9]{9}$` (exactly 9 digits)
   - 5548 format: regex `^[0-9]{4}$` (exactly 4 digits)
   - Strip whitespace from cell value before validation (field_cleaner with strip_spaces=True for consistency)

3. **Implement Unique ID column detection**
   - Reuse PATonline_FINDER pattern: scan rows 1-20, columns A-M
   - Use field_cleaner(str(cell.value), strip_spaces=True) to normalize cell text
   - Create normalized lookup dict: {field_cleaner("Unique ID", strip_spaces=True): "unique_id"}
   - Return column letter when header match found; return None if not found

4. **Implement file validation logic**
   - Open file with openpyxl (try) then xlrd fallback (catch)
   - Detect Unique ID column; if not found → return (False, "Unique ID column not found")
   - Iterate all populated rows in Unique ID column (from row after header to last_row)
   - For each cell: if empty → return (False, "Empty Unique ID found")
   - If non-empty: strip whitespace and validate against format using format validator
   - If any cell invalid → return (False, f"Invalid format in {column}{row}: {value}")
   - If all cells valid → return (True, "All Unique ID values match format")

5. **Implement file move workflow**
   - If validation passes (is_valid=True) → file stays in place, return True
   - If validation fails (is_valid=False) → prepare move to Invalid_UniqueID/ subfolder
   - Create Invalid_UniqueID/ subfolder in output_dir if not exists
   - Build target_path = output_dir/Invalid_UniqueID/filename
   - Check if target_path exists:
     - If yes → call `_handle_file_conflict(source_path, target_path)` → returns action ("overwrite", "skip", "rename")
     - If action="overwrite" → remove existing file, move source
     - If action="skip" → log and return False
     - If action="rename" → append _dup, _dup2, etc. suffix before extension, move with new name
   - If no conflict → move file with shutil.move
   - Log result and return True on success

6. **Implement conflict dialog handler**
   - `_handle_file_conflict(source_path, target_path)`: Show wxPython dialog with three buttons
   - Dialog message: "filename.xlsx already exists in Invalid_UniqueID/. Overwrite, skip, or rename?"
   - Return "overwrite" | "skip" | "rename" based on user click
   - If rename: generate new name with _dup suffix (e.g., file_dup.xlsx, file_dup2.xlsx if _dup exists)

7. **Implement dual-mode architecture**
   - `run(format_type, progress_callback=None)`: Main method
   - Validate progress_callback is None or callable (raise TypeError otherwise, matching PATonline_FINDER)
   - If progress_callback is None and running standalone → create internal progress dialog via helper function
   - Call select_work_files([".xlsx", ".xls"]) for file selection
   - Call select_output_folder("Select output folder for validated Unique ID files") for output folder
   - Process files in loop:
     - For each file (index, total_count, filename):
       - Call progress_callback(index, total_count, filename) if provided
       - Check return value: False → cancel, log message, return early
       - Call process_file(file_path, output_dir, format_type)
   - Log completion summary (X files processed, Y moved to Invalid_UniqueID/, Z left in place)
   - Call logger.finalize_report()

8. **Implement standalone execution**
   - `main()` function: display ASCII art banner (similar to PATonline_FINDER)
   - Create wx.App instance
   - Prompt user for format selection via wxPython dialog:
     - Show dialog: "Select expected Unique ID format"
     - Buttons: "ABC0001 (3 letters + 4 digits)", "182815548 (9 digits)", "5548 (4 digits)", "Cancel"
     - Store user choice in format_type variable
   - If user cancels → exit gracefully
   - Create PATUniqueIDChecker instance
   - Call run(format_type, progress_callback=_create_progress_callback())
   - Clean up: app.Destroy()

9. **Implement progress callback factory**
   - `_create_progress_callback()`: Return closure that creates and manages progress dialog
   - Dialog class: ProgressDialog (reuse from PATonline_FINDER or create similar)
   - On first call: create ProgressDialog(total_count), call Show()
   - On each call: update counter, filename, progress bar
   - Check is_cancelled() on each call, return False if cancelled (which signals run() to stop)
   - On final call or cancel: Destroy dialog

## 7. Validation Strategy

**Tests to Create:**

- **Test: Format Validators** - Verify each format validator correctly accepts valid values and rejects invalid values
  - ABC0001: accept "ABC0001", "xyz1234", reject "ab1234", "ABC00001", "ABCD0001", empty string, None
  - 182815548: accept "123456789", reject "12345678", "1234567890", "12345678a", empty string, None
  - 5548: accept "1234", "9999", reject "123", "12345", "123a", empty string, None

- **Test: Column Detection** - Verify Unique ID column detection works with various header placements
  - Header in A1, B1, C1, etc. → correctly identified
  - Header with whitespace variations ("  Unique ID  ") → found and normalized correctly
  - Header with case variations ("unique id", "UNIQUE ID") → found via field_cleaner
  - Header missing → returns None

- **Test: File Validation - Valid Files** - Files with all valid Unique ID values pass validation
  - File with ABC0001 format values → returns (True, ...)
  - File with 9-digit values → returns (True, ...)
  - File with 4-digit values → returns (True, ...)

- **Test: File Validation - Invalid Files** - Files with any invalid/empty Unique ID values fail
  - File with empty cells in Unique ID column → returns (False, "Empty Unique ID found")
  - File with format mismatch (e.g., "ABC00001" for ABC0001 pattern) → returns (False, "Invalid format...")
  - File without Unique ID column → returns (False, "Unique ID column not found")
  - File with whitespace in values ("  ABC0001  ") → values stripped and validated correctly

- **Test: File Move Workflow** - Validate files moved correctly with conflict handling
  - Valid file stays in source folder
  - Invalid file moved to Invalid_UniqueID/ subfolder
  - Conflict dialog called when file exists at destination
  - Overwrite action removes old file and moves new one
  - Skip action leaves both files in place
  - Rename action appends _dup suffix and moves

- **Test: Progress Callback** - Verify callback called correctly during batch processing
  - Callback called with (1, total, filename), (2, total, filename), ..., (total, total, filename)
  - Returning False cancels processing
  - Exceptions in callback logged as warnings, processing continues

- **Test: Edge Cases**
  - Zero files selected → graceful exit, no error
  - Corrupted/unreadable file → caught, logged as warning, left in place
  - Output folder same as source → Invalid_UniqueID/ subfolder created within source
  - Large filenames → truncated properly in progress dialog if needed

**User Verification:**

Run tests with: `pytest Finders/test_patuniqueID_checker.py -v`

**Manual Checks:**

- Run standalone with format selection dialog — user sees ASCII art banner, format dialog, file selection, output folder selection
- Verify progress dialog updates correctly during processing (counter, filename, progress bar)
- Verify cancel button in progress dialog stops processing gracefully
- Test file conflict scenarios: move file twice to same output folder, trigger dialog, test all three options
- Verify log file contains all processed files and final summary
- Verify Invalid_UniqueID/ folder created only when needed
- Verify valid files remain in source folder (not moved)

## 8. Rollback Plan

All file moves are destructive (shutil.move). Rollback requires:

1. **If processing aborted mid-operation**: Check logger output to identify which files were moved to Invalid_UniqueID/
2. **Restore files**: Move files from Invalid_UniqueID/ back to source folder
3. **Prevent future moves**: Delete Invalid_UniqueID/ folder if empty after restore
4. **Alternative**: If output folder is different from source, copy files back from output folder

**Prevention measures:**
- Comprehensive logging of every file move with source/destination paths
- Conflict handling dialog allows skip option to prevent unintended overwrites
- User can review log output before running again

