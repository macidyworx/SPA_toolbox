# Mission: Implement PATonline-FINDER Script

## 1. Objective

Create PATonline-FINDER.py to locate and categorize PATonline Excel files based on the presence of family name, given name, unique ID, and username fields, organizing them into corresponding output folder structures.

## 2. Scope

**Included:**
- File selection UI (user picks files or folder to process via dog_box helper)
- Output folder selection UI
- PATonline file detection: scan columns A-M, rows 1-20 for headers "Family name", "Given name", "Unique ID", "Username"
- File categorization into three categories:
  - `[output_folder]/No_UniqueID/` — contains Family name + Given name + Username (no Unique ID)
  - `[output_folder]/Only_UniqueID/` — contains Family name + Given name + Unique ID (no Username)
  - `[output_folder]/` — contains all four fields: Family name + Given name + Unique ID + Username
- File movement/copying to categorized subdirectories
- Logging: INFO level for identified PATonline files only (unidentified files are not logged)
- Standalone execution via `python PATonline-FINDER.py`
- Usable as module: `from Finders.PATonline_FINDER import PATonlineFinder`

**Excluded:**
- Validation of cell content (only header presence matters, not data integrity)
- Filtering by data row count or data quality
- Moving of non-Excel files
- Integration with external logging systems beyond water_logged

## 3. Assumptions

- All input files are .xlsx or .xls format (caller provides via dog_box)
- Headers are case-insensitive (e.g., "family name", "Family Name", "FAMILY NAME" all match)
- Exact header names: "Family name", "Given name", "Unique ID", "Username" (whitespace-trimmed)
- Headers can appear in any column A-M and any row 1-20
- If multiple instances of a header exist, first occurrence is used for detection
- User has permission to read input files and write to output directory
- Output directory structure is created on demand (no pre-existing constraints)
- Files are moved (not copied) to output directories; duplicates handled by overwrite/skip decision via wx.MessageBox
- water_logged.THElogger is available in the virtual environment

## 4. Affected Areas

**Files/Modules:**
- `Finders/PATonline-FINDER.py` (new file)
- `Helpers/dog_box/__init__.py` (dependency: no changes required)
- `Helpers/dog_box/ssotsif.py` (dependency: no changes required)
- `Helpers/dog_box/work_files.py` (dependency: no changes required)
- `Helpers/Clean_fields/clean_field.py` (optional: for header name normalization)
- `IDswappers/logging.ini` (can be referenced or copied to Finders/)

**Dependencies:**
- openpyxl (load_workbook, data_only mode)
- xlrd (for .xls format support)
- wx (file/folder dialogs, message boxes)
- water_logged.THElogger (logging)
- Helpers.dog_box (file/folder selection)

## 5. Risks

**Technical Risks:**
- **Large file handling**: openpyxl may consume memory for large .xlsx files; use `read_only=True, data_only=True` to mitigate.
- **File locking**: If a file is open in Excel during processing, move operation may fail on Windows; add try/except and notify user.
- **Header detection edge cases**: Headers with leading/trailing whitespace; use `.strip()` on all cell values.
- **Column scanning limit (A-M)**: Assumes PATonline always uses columns ≤ M; verify with user if files use columns beyond M.

**Regressions:**
- None expected; this is a new script with no impact on existing modules.

**Edge Cases:**
- Empty files (no cells in A1-M20): treat as unidentified, do not log.
- Files with headers but no data: still process as PATonline if headers are present.
- Duplicate filenames in different output subdirectories: move may silently overwrite; prompt user before overwrite.
- Files without extension or non-Excel files: skip gracefully with debug log (not INFO).
- Unicode in filenames or header values: clean_field() handles Unicode normalization; apply to header comparison.

## 6. Implementation Strategy

1. **Set up project structure and imports**
   - Create PATonline-FINDER.py with section markers (IMPORTS, GLOBAL CONSTANTS, MAIN CLASS, etc.)
   - Import openpyxl, xlrd, wx, water_logged, os, sys, shutil
   - Import dog_box helpers: `select_work_files`, `select_output_folder`
   - Import field_cleaner from Helpers.Clean_fields (for header normalization)
   - Set up sys.path to allow relative imports from Helpers

2. **Define header detection logic**
   - Create `find_headers(workbook, worksheet)` function to scan cells A1-M20
   - Normalize each cell value: `.strip().lower()` for case-insensitive matching
   - Return dict with boolean flags: `has_family_name`, `has_given_name`, `has_unique_id`, `has_username`
   - Use set membership to track which headers were found (avoid duplicates)

3. **Create PATonlineFinder class**
   - `__init__`: initialize logger with logging.ini config
   - `categorize_file(file_path)`: return category string ("all_fields", "no_unique_id", "only_unique_id", "unidentified")
   - `process_file(file_path, output_dir)`: open file, detect headers, move to appropriate subdirectory
   - `run()`: main workflow
     - Prompt user for input files/folder via `select_work_files([".xlsx", ".xls"])`
     - Prompt user for output folder via `select_output_folder()`
     - Create output subdirectories on demand
     - Iterate over files, call process_file() for each
     - Log INFO for identified PATonline files only
     - Handle file move errors gracefully (log warnings, continue)

4. **Implement file movement logic**
   - Determine target directory based on categorization
   - Check if target file already exists; if yes, show wx.MessageBox asking user to overwrite/skip
   - Use `shutil.move()` to move file to target directory
   - Log file movements with source and destination paths

5. **Add logging and user feedback**
   - Log script start/end times
   - Log user selections (input file count, output directory)
   - Log each identified PATonline file at INFO level with category
   - Log file move operations at DEBUG level
   - Finalize report via `logger.finalize_report()` at script end

6. **Implement standalone execution**
   - Add `main()` function that creates PATonlineFinder() instance and calls run()
   - Add `if __name__ == "__main__":` block to call main()
   - Handle exceptions gracefully, logging errors before exit

7. **Add dual-mode module support**
   - Ensure class can be imported: `from Finders.PATonline_FINDER import PATonlineFinder`
   - Document public interface in module docstring

## 7. Validation Strategy

**Tests to Create:**

- Test: Header detection with headers in different columns (A, B, M)
- Test: Header detection with headers in different rows (1, 10, 20)
- Test: Case-insensitive header matching (lowercase, uppercase, mixed case)
- Test: Whitespace handling in headers (leading/trailing spaces)
- Test: Categorization logic for all four scenarios (all_fields, no_unique_id, only_unique_id, unidentified)
- Test: File with partial headers (missing one or more fields)
- Test: Empty file (no headers in A1-M20)
- Test: Multiple input files with mixed categories
- Test: Output directory creation and file movement
- Test: Logging output (INFO for identified files, no log for unidentified)

**User Verification:**

1. Create test Excel files:
   - `test_all_fields.xlsx`: contains all four headers in various columns/rows
   - `test_no_unique_id.xlsx`: contains Family name, Given name, Username only
   - `test_only_unique_id.xlsx`: contains Family name, Given name, Unique ID only
   - `test_unidentified.xlsx`: has some headers but missing critical ones

2. Run the script with test files:
   ```
   python Finders/PATonline-FINDER.py
   ```

3. Verify output:
   - Files are categorized correctly into subdirectories
   - Logs show INFO entries for identified PATonline files only
   - Log report is generated in the logs/ directory
   - No errors or exceptions during file movement

4. Run tests with:
   ```
   .venv/bin/pytest Finders/test_patonline_finder.py -v
   ```

**Manual Checks:**

- Verify logging output: open logs/PATonline-FINDER_*.log and confirm INFO entries match moved files
- Verify file integrity: check that moved files are complete and readable after movement
- Test with Unicode filenames and headers (e.g., accented characters)
- Test with large files (> 10 MB) to ensure memory handling is acceptable
- Test cancellation at each dialog (file selection, output folder, overwrite prompt)

## 8. Rollback Plan

If implementation encounters issues:

1. **If file movement fails during processing**:
   - Files are moved one at a time; if an error occurs, stop processing, log the error, and notify user via wx.MessageBox
   - User can re-run script to retry with different settings or manually move remaining files
   - No data loss occurs because files are not deleted until successfully moved

2. **If logging fails**:
   - Catch exception in logger initialization; fall back to basic print() statements
   - Notify user that detailed logging is unavailable but script continues

3. **If header detection is incorrect**:
   - Verify header detection logic against sample files; if edge case found, add specific handling
   - Create new test case and re-run validation

4. **Complete rollback**:
   - Delete PATonline-FINDER.py
   - Files moved to output directories can be manually moved back to source location if needed
   - No changes to existing codebase required; only addition of new script

---

**File Locations:**

- Script: `/home/bigbox/Documents/Mworx/SPA_toolbox/Finders/PATonline-FINDER.py`
- Mission file: `/home/bigbox/Documents/Mworx/SPA_toolbox/Finders/MF-PATonline-FINDER.md`
- Requirements doc: `/home/bigbox/Documents/Mworx/SPA_toolbox/PAT_FINDER.md`
- Helpers: `/home/bigbox/Documents/Mworx/SPA_toolbox/Helpers/dog_box/`
- Logging config template: `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/logging.ini`
