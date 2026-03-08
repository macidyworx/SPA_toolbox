# MP-IDswappers_Tests — Mission Plan

## Objective

Create comprehensive test coverage for the IDswappers module (12 swapper classes) and Report_Merger functionality. Tests should cover data transformation logic, header detection, lookup matching, file I/O, error handling, and report generation.

## Scope

**Included:**
- Unit tests for all 12 IDswapper classes: Magic, ROL, RR, OBS, SSSR, DIBELS, EOI, MOI, Westwood, NAPLAN_OQ, PATdownloads, SMBtemplates
- Unit tests for Report_Merger class
- Fixtures for test Excel files (empty, valid headers, missing headers, mismatched data)
- Fixtures for SIF/SSOT lookup files
- Tests for header detection (`_find_headers`, `_find_headers_xlrd`)
- Tests for ID matching logic (SIF mode: name-based; SSOT mode: ID-based)
- Tests for report generation (not-found logs, summary reports, file movement)
- Tests for edge cases: malformed headers, missing sheets, empty data, corrupt files
- Integration tests verifying file processing workflows

**Excluded:**
- GUI/wxPython tests (UI dialogs, user interaction)
- Tests for THElogger (external logging library)
- Tests for dog_box file selector dialogs (external UI library)
- End-to-end tests with real user workflows (covered by integration tests only)
- Performance tests under large datasets (out of scope)

## Affected Areas

**Files/Modules:**
- `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/Magic.py`
- `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/ROL.py`
- `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/RR.py`
- `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/OBS.py`
- `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/SSSR.py`
- `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/DIBELS.py`
- `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/EOI.py`
- `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/MOI.py`
- `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/Westwood.py`
- `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/NAPLAN_OQ.py`
- `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/PATdownloads.py`
- `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/SMBtemplates.py`
- `/home/bigbox/Documents/Mworx/SPA_toolbox/IDswappers/Report_Merger.py`
- `/home/bigbox/Documents/Mworx/SPA_toolbox/tests/conftest.py` (enhance if needed)
- Test output: `/home/bigbox/Documents/Mworx/SPA_toolbox/tests/test_idswappers.py` and `/home/bigbox/Documents/Mworx/SPA_toolbox/tests/test_report_merger.py`

**Dependencies:**
- openpyxl (workbook I/O)
- xlrd, xlutils (legacy xls support)
- Helpers.Clean_fields.clean_field (field_cleaner for text normalization)
- water_logged.the_logger (logging)
- pytest (test framework)
- tempfile, Path (test file management)

## Implementation Steps

### Phase 1: Test Infrastructure Setup

1. **Enhance conftest.py with IDswappers fixtures**
   - Create reusable Excel file factory (`create_test_excel` helper)
   - Create SIF lookup file fixture (3 columns: Firstname, Surname, StudentID)
   - Create SSOT lookup file fixture (2 columns: Old_ID, New_ID)
   - Create XLS file fixture (for modules supporting legacy format: ROL, SSSR, DIBELS, RR)
   - Create CSV file fixture (for SSSR which processes CSVs)
   - Mark fixtures with appropriate pytest markers (`@pytest.mark.unit`, `@pytest.mark.needs_files`)

2. **Create shared test data constants**
   - Define test student data: names, IDs (both alphanumeric and numeric)
   - Define malformed headers, missing headers, extra whitespace in headers
   - Define lookup dictionaries for SIF and SSOT modes
   - Define expected transformation results for validation

### Phase 2: Core Header Detection Tests

3. **Test `_find_headers` for all swappers**
   - Test exact header match (case-insensitive, whitespace-tolerant)
   - Test headers in non-standard order (columns shuffled)
   - Test missing required headers (should return None)
   - Test extra headers beyond required (should still find required ones)
   - Test headers with extra whitespace/unicode (use field_cleaner patterns)
   - Test worksheet with no header row (data starts at row 1)
   - Test worksheet with header on row 2+ (offset headers)
   - Expected target sheets for each class (e.g., 'MagicWords', 'ROL Data', etc.)

4. **Test `_find_headers_xlrd` for legacy XLS support (ROL, SSSR, DIBELS, RR)**
   - Same scenarios as above but using xlrd sheet objects
   - Verify column indices are 0-based
   - Test header detection in xlrd sheet vs openpyxl worksheet consistency

### Phase 3: Data Processing Tests (SIF Mode)

5. **Test SIF mode ID matching for all applicable swappers**
   - Create test data: 3+ students with first/last names
   - Build SIF lookup: (cleaned_fname, cleaned_lname) → StudentID
   - Process test data, verify IDs are updated correctly
   - Test with names in various cases/spacing: "JOHN SMITH", " john  smith ", "John Smith"
   - Test not-found tracking: students not in SIF should be logged
   - Test partial matches (one name matches, other doesn't) should be rejected
   - Test with numeric and alphanumeric student IDs from lookup
   - Test with missing name data (None or empty string) should be skipped

6. **Test multi-sheet processing (for modules with 2+ sheets)**
   - Create workbook with multiple relevant sheets
   - Verify only target sheet is processed (MAGIC: 'MagicWords', ROL: 'ROL Data', etc.)
   - Verify other sheets are left untouched
   - Test behavior when target sheet is missing (should skip file)

### Phase 4: Data Processing Tests (SSOT Mode)

7. **Test SSOT mode ID mapping for all applicable swappers**
   - Create test data with old IDs
   - Build SSOT lookup: old_id (cleaned) → new_id
   - Process test data, verify old IDs are replaced with new IDs
   - Test with numeric, alphanumeric, and string old IDs
   - Test not-found tracking: old IDs not in SSOT should be logged
   - Test with None/empty old IDs should be skipped
   - Test SSOT file parsing (identify old_id_col and new_id_col correctly)

### Phase 5: Special Processing Tests

8. **Test SSSR-specific name parsing**
   - Test `parse_student_name('JAMES ABBEY')` → ('JAMES', 'ABBEY')
   - Test with middle names: `parse_student_name('JAMES WILLIAM ABBEY')` → ('JAMES', 'ABBEY')
   - Test with single word: should return None
   - Test with empty/None input: should return None
   - Test CSV section detection: find header row with 'Local Student ID' and 'Student Name'
   - Test multi-section CSV: identify and process only student data section

9. **Test module-specific patterns**
   - **Magic**: Load workbook with `keep_vba=True` to preserve macros (verify in tests)
   - **ROL**: Support both .xls (xlrd) and .xlsx (openpyxl)
   - **SSSR**: Parse space-separated student names
   - **DIBELS**: Verify sheet handling for DIBELS data format
   - **OBS**: Verify sheet handling for OBS data format
   - **Others**: Document expected sheet/column patterns for each

### Phase 6: Report Generation Tests

10. **Test report generation for all swappers**
    - Verify not-found log is created with correct columns
    - Verify not-found log contains all unmatched records
    - Verify summary report is created with correct structure
    - Verify summary contains: metric names, values, files processed, matched counts
    - Verify file organization: files categorized by processing result
    - Verify files are moved to correct output subfolders

11. **Test Report_Merger class**
    - Test Summary sheet: multiple reports placed side-by-side with column gaps
    - Test Full List sheet: concatenated from all reports, header duplicates removed
    - Test with 1, 2, and 3+ input files
    - Test missing Summary sheet (should skip file gracefully)
    - Test missing Full List sheet (should create only Summary output)
    - Test output file creation and location
    - Test with empty input files
    - Test with corrupt/unreadable files (error handling)

### Phase 7: Edge Cases and Error Handling

12. **Test robust file handling**
    - Test with temp files (starting with ~$) should be filtered
    - Test with file locks/permissions errors (should log and continue)
    - Test with missing files in file list
    - Test with duplicate filenames across different directories
    - Test output folder collision (existing output subfolder)

13. **Test data edge cases**
    - Test empty workbook (no data rows)
    - Test with all None/empty cells
    - Test with duplicate student names in data
    - Test with numeric data stored as integers vs strings
    - Test with unicode/special characters in names
    - Test with very long names/IDs (boundary)

14. **Test error recovery**
    - Test file save failures (e.g., locked by Excel)
    - Test with corrupt Excel files
    - Test with missing required helper modules (should raise ImportError)
    - Test logging: verify all major operations are logged

### Phase 8: Integration Tests

15. **Test end-to-end workflows**
    - For each swapper: complete workflow with multiple input files
    - SIF mode: process 3+ files, verify all matched correctly, not-found logged
    - SSOT mode: process 3+ files, verify all IDs replaced, unmatched tracked
    - Verify output structure is correct
    - Verify no original files are lost
    - Verify files with errors are moved to SKIPPED folder (if implemented)

16. **Test module importability and instantiation**
    - Verify each class can be imported without errors
    - Verify each class instantiates with logger
    - Verify logger is configured correctly

## Risks

- **UI Dependency (wxPython)**: Tests should NOT mock UI dialogs; tests should only test the data processing logic (`_find_headers`, `_process_sheet`, etc.), not the `run()` method which requires user input.
  - **Mitigation**: Keep `run()` untested; focus on testable internal methods. Document this limitation.

- **File I/O Complexity**: Creating realistic test Excel files requires careful setup. Files may differ across .xlsx vs .xls formats.
  - **Mitigation**: Use conftest.py fixtures to centralize file creation. Test both openpyxl (xlsx) and xlrd (xls) paths separately.

- **Field Cleaner Dependency**: field_cleaner behavior must match production. If field_cleaner changes, all tests may fail.
  - **Mitigation**: Tests import field_cleaner directly, ensuring test behavior matches production exactly.

- **Logging Side Effects**: Tests will generate log files. If not cleaned up, logs can accumulate.
  - **Mitigation**: Mock or disable logging in unit tests; only enable in integration tests.

- **Marker Consistency**: Pytest markers should match those in pytest.ini.
  - **Mitigation**: Define test markers in pytest.ini upfront; reference them in tests.

## Validation

**Tests to create:**
- `test_idswappers.py`: ~35 test methods covering header detection, SIF/SSOT processing, reports, edge cases, and integration
- `test_report_merger.py`: ~15 test methods covering Summary/Full List merging, error handling, and edge cases
- Coverage target: >80% of IDswapper logic (excludes UI/dialogs)

**Manual checks:**
- Run `pytest tests/test_idswappers.py -v` to verify all tests pass
- Run `pytest tests/test_report_merger.py -v` to verify all tests pass
- Run `pytest tests/test_idswappers.py -m unit` to verify unit test isolation (no file I/O)
- Run `pytest tests/test_idswappers.py -m integration` to verify end-to-end workflows
- Check coverage report: `pytest --cov=IDswappers tests/test_idswappers.py`
- Manually inspect generated test Excel files in temp directories to ensure fixtures work correctly

## Rollback

If tests reveal issues with the actual IDswapper code:

1. Do NOT modify IDswapper code during test creation
2. Document failures in test comments and report them separately
3. If test fixtures are incorrect, fix the fixture, not the swapper
4. If tests are too strict, loosen them with proper documentation
5. If code is broken, create a separate bug-fix task for the Actioning Agent

If test infrastructure is misconfigured:

1. Revert changes to conftest.py: `git checkout tests/conftest.py`
2. Delete test files: `rm tests/test_idswappers.py tests/test_report_merger.py`
3. Re-run setup phase with corrected approach

## Test Strategy Summary

**Unit Tests** (fast, no I/O):
- Header detection functions (`_find_headers`, `_find_headers_xlrd`)
- Data processing logic (`_process_sheet`)
- Name parsing (SSSR)
- Field cleaning and matching

**Integration Tests** (file I/O):
- Complete workflows with real Excel files
- Report generation and file movement
- Report_Merger with multiple input files
- Error handling with corrupt files

**Fixtures**:
- Excel files with valid/invalid headers
- SIF/SSOT lookup files
- Test data with known transformations
- Temp directories with cleanup

**Markers**:
- `@pytest.mark.unit` — fast, no files
- `@pytest.mark.integration` — uses files, slower
- `@pytest.mark.needs_files` — creates temp Excel files
- Add to pytest.ini if not already present

---

**Total Estimated Test Methods**: ~50 across both files
**Est. Coverage**: 80%+ for data processing logic (excluding UI and external libraries)
