# Mission: PAT Username Format Checker

## 1. Objective

Build a dual-mode Python script that auto-detects the username column in PATonline Excel files, validates all usernames against a user-selected format (alphanumeric, long numeric, or short numeric), and organizes files into categorized output folders based on validation results.

## 2. Scope

**Included:**
- Auto-detect username column by searching for common header variants (e.g., "Username", "ID", "User ID", case-insensitive)
- Present user with three format choices via wxPython dialog:
  - `ABC0001` (alphanumeric: 2 uppercase letters, 1 letter or dash, 4 digits)
  - `182815548` (numeric: 4-12 digits, may be stored as string or number)
  - `5548` (numeric: 2-8 digits, may be stored as string or number)
- Validate all usernames in the detected column against the selected format (case-insensitive)
- Move files to organized output structure based on validation:
  - `{output_folder}/Expected_ID/{filename}` if all values match
  - `{output_folder}/Files_to_check/{filename}` if any values don't match
  - `{output_folder}/Empty_or_unreadable/{filename}` if column is empty or unreadable
- Handle user cancellation gracefully (exit with message, no state changes)
- Support both standalone execution and module import (dual-mode architecture per CLAUDE.md)

**Excluded:**
- Modifying the Excel file contents (read-only)
- Automatic column selection fallback if detection fails (will prompt user)
- Complex Excel data types beyond basic string/numeric values
- Recursive subdirectory scanning (process only files user selects)

## 3. Assumptions

- PATonline files are Excel (.xlsx or .xls format)
- Username column exists and has a recognizable header name (will auto-detect from common variants)
- Files are readable and not corrupted
- Output folder exists and is writable
- User can interact with wxPython dialogs on their system
- Numeric IDs may be stored as numbers (int) or strings in Excel cells
- Case-insensitive matching (e.g., "abc0001" matches ABC0001)
- Files are moved (not copied); the original files are no longer available after processing

## 4. Affected Areas

**Files/Modules:**
- `RandomTools/PAT/PAT_Username_Checker.py` (new, will be created and filled)
- Uses `Helpers/dog_box/work_files.py` (select_work_files, select_output_folder)
- Uses `Helpers/Clean_fields/clean_field.py` (field_cleaner for case-insensitive matching)
- Uses `Helpers/Last_row_finder/real_last_row.py` (to find actual last row with data in username column)

**Dependencies:**
- openpyxl (Excel file reading)
- wxPython (file selection and format dialogs)
- Standard library: os, shutil, pathlib, re

## 5. Risks

**Technical Risks:**
- **Numeric ID ambiguity**: Excel may auto-convert numeric strings to integers; mitigation: read with `data_only=True` and normalize both int and str representations before validation
- **Column detection failure**: If header is non-standard, auto-detection may miss it; mitigation: provide fallback prompt asking user to specify column letter or name
- **File locking during move**: If file is open elsewhere, move will fail; mitigation: catch exception, show error dialog, skip that file with logging
- **Path normalization across OS**: Windows/Linux path handling; mitigation: use pathlib.Path for cross-platform compatibility

**Regressions:**
- If output folder structure creation fails, files won't be moved; mitigation: validate output folder writability before processing any files
- If user cancels mid-process, partial state could exist (some files moved, some not); mitigation: ask for confirmation before moving files, or batch-process all validation first, then move in sequence

**Edge Cases:**
- Username column is empty (no data rows) → move to Empty_or_unreadable
- Username column contains mixed data types (some numbers, some strings) → normalize before comparison
- Filename collisions in output folder → append timestamp or counter to filename
- Very long file paths exceeding OS limits → use pathlib.Path and let OS handle errors gracefully

## 6. Implementation Strategy

1. **Create PAT_Username_Checker class** with dual-mode architecture:
   - `__init__(output_folder, selected_format)` constructor for module mode
   - `run(files)` method for processing file list
   - `main()` standalone entry point with full dialog flow

2. **Implement username column auto-detection** function:
   - Load first file's headers using openpyxl
   - Search for header containing "username", "id", "user_id", etc. (case-insensitive, whitespace-tolerant)
   - Use field_cleaner for robust matching
   - If not found, prompt user via dialog to select column letter or name
   - Return column letter (A, B, C, etc.)

3. **Build format validators** (three regex/logic functions):
   - `validate_alphanumeric(value)`: 2 letters + (1 letter OR dash) + 4 digits, case-insensitive
   - `validate_long_numeric(value)`: 4-12 digits, handles int or string
   - `validate_short_numeric(value)`: 2-8 digits, handles int or string
   - All validators normalize input (convert to string, lowercase, strip whitespace) using field_cleaner

4. **Implement format selection dialog**:
   - wxPython single-choice dialog presenting three options
   - Return selected format key or None if cancelled
   - Exit gracefully with message if user cancels

5. **Implement file validation loop** for each file:
   - Open with openpyxl (data_only=True to get values, not formulas)
   - Detect username column (call auto-detect function)
   - Find last row with data using ws_last_row helper
   - Iterate through all data rows in username column
   - Normalize each value and validate against selected format
   - Track: all_match (bool), file_status (str)
   - Return: status code (EXPECTED_ID, FILES_TO_CHECK, EMPTY_OR_UNREADABLE)

6. **Implement file organization workflow**:
   - Validate output folder exists and is writable
   - Create subdirectory structure if missing: Expected_ID, Files_to_check, Empty_or_unreadable
   - For each file, determine destination folder based on validation result
   - Handle filename collisions: if destination file exists, append _(1), _(2), etc.
   - Move file using shutil.move
   - Log each operation (source → destination or error)
   - Return summary: [N files processed, N to Expected_ID, N to Files_to_check, N to Empty_or_unreadable, N errors]

7. **Implement error handling**:
   - Catch openpyxl exceptions (corrupt files, unreadable sheets) → move to Empty_or_unreadable
   - Catch file move exceptions (permission denied, disk full) → log error, skip file, continue
   - Catch dialog cancellation → exit with message, no files moved
   - Wrap all file operations in try-except with informative logging

8. **Standalone execution flow** (main function):
   - Call select_work_files(['.xlsx', '.xls']) to prompt user for files
   - Exit if user cancels (return None)
   - Call format selection dialog → get format choice
   - Exit if user cancels format selection
   - Call select_output_folder() → get output path
   - Exit if user cancels output folder selection
   - Instantiate PAT_Username_Checker with output_folder and format
   - Call run(files) to process
   - Print summary results to console

## 7. Validation Strategy

**Tests to Create:**

Create `/RandomTools/PAT/test_PAT_Username_Checker.py` with these test classes and methods:

**Test File**: `test_PAT_Username_Checker.py`

- **TestFormatValidation**:
  - Test: Alphanumeric format accepts valid ABC0001 (ABC0001, abc0001, AbC0001 all match)
  - Test: Alphanumeric format accepts valid ABC-0001 (with dash)
  - Test: Alphanumeric format rejects invalid patterns (ABC00012, AB0001, ABCD0001, ABC-001, etc.)
  - Test: Long numeric format accepts 4-12 digits (1234, 123456789, 999999999999)
  - Test: Long numeric format rejects 1-3 or 13+ digits
  - Test: Short numeric format accepts 2-8 digits (12, 12345, 99999999)
  - Test: Short numeric format rejects 1-digit or 9+ digit numbers
  - Test: All validators handle string and integer inputs uniformly
  - Test: All validators are case-insensitive (via field_cleaner normalization)

- **TestColumnDetection**:
  - Test: Auto-detect finds "Username" header (exact match)
  - Test: Auto-detect finds "User ID" header (case-insensitive, whitespace-tolerant)
  - Test: Auto-detect finds "ID" header when unambiguous
  - Test: Auto-detect returns None if no match found (fallback to prompt)
  - Test: field_cleaner normalization works on header names (spaces, case)

- **TestFileValidation**:
  - Test: File with all matching usernames returns EXPECTED_ID status
  - Test: File with one non-matching username returns FILES_TO_CHECK status
  - Test: File with empty username column returns EMPTY_OR_UNREADABLE status
  - Test: Unreadable/corrupt Excel file returns EMPTY_OR_UNREADABLE status
  - Test: File with mixed string/numeric usernames validates correctly

- **TestFileOrganization**:
  - Test: Output folder structure is created (Expected_ID, Files_to_check, Empty_or_unreadable)
  - Test: File is moved to correct subfolder based on validation result
  - Test: Filename collision is handled (appends _(1), _(2), etc.)
  - Test: Original file no longer exists after move
  - Test: Output folder selection cancellation exits gracefully

- **TestIntegration**:
  - Test: Module can be imported and instantiated
  - Test: Standalone script can be executed with mocked dialogs
  - Test: Summary report is accurate (counts for each category)

**User Verification:**

Run tests with:
```bash
cd /home/bigbox/Documents/Mworx/SPA_toolbox
source .venv/bin/activate
pytest RandomTools/PAT/test_PAT_Username_Checker.py -v
```

**Manual Checks:**
- Test with actual PATonline files (if available) to verify column detection on real data
- Verify that file moves are correct and no files are duplicated or lost
- Test dialog cancellation at each step (file selection, format, output folder)
- Verify output folder structure is created with correct permissions
- Check that error handling is graceful (no crashes on corrupt files)

## 8. Rollback Plan

**If something goes wrong during implementation:**
- All file moves are reversible if source files are backed up before running the script
- Recommend user backup the original files before first use
- If move fails mid-process, files remaining in source location can be re-processed
- To undo moves, user can manually move files back from output folder to original location

**If a file is moved to the wrong folder:**
- User can manually inspect output subfolders and move files back
- Re-run the script on the misplaced file to re-validate and move to correct folder

**Safe reversal process:**
1. Check source directory for any remaining files
2. For files in output folders, use the script again with corrected parameters
3. If script has bugs, revert `PAT_Username_Checker.py` to previous git commit and rebuild

**Development safeguards:**
- Never run file move operations in testing (use dry-run or copy-only for test suite)
- Use git commits after each major implementation step to allow revert if needed
- Test all dialog cancellation paths before enabling file moves
- Log all file operations with source, destination, and timestamp for audit trail
