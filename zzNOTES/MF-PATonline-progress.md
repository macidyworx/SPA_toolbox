# Mission: Add Progress Tracking to PATonline-FINDER

## 1. Objective

Add progress tracking with a cancellable progress window to PATonline_FINDER.py. For standalone execution, display a progress bar showing file count and current filename. For module usage, enable progress callbacks via a function parameter.

## 2. Scope

**Included:**
- New wxPython progress dialog window with progress bar and file/counter display
- Cancel button on progress window to stop processing mid-way
- Callback function parameter in `PATonlineFinder.run()` for module usage
- Counter tracking: total files to process, current file index
- Filename display: show which file is currently being processed
- Progress window appears after file selection dialogs complete (before processing loop starts)
- Graceful handling of user cancel: log cancellation, finalize report, exit cleanly
- Backwards compatibility: `run()` method works with or without callback parameter

**Excluded:**
- Multi-threading (processing remains single-threaded; UI updates during file iteration)
- Progress percentage estimation based on file size (counter only)
- Retry logic on cancelled files
- Progress persistence across runs

## 3. Assumptions

- wxPython is available (already a dependency per CLAUDE.md)
- Progress window can be modal/blocking during file processing
- User will have opportunity to review and optionally cancel before processing reaches problematic files
- Caller provides callback function that matches expected signature when used as module
- All files are processed sequentially (no async/threading complexity)
- Cancel event flag is simple boolean; no need for thread-safe synchronization

## 4. Affected Areas

**Files/Modules:**
- `Finders/PATonline_FINDER.py` (modify: add ProgressDialog class, update run() signature, integrate cancel handling)

**Dependencies:**
- `wx` (wxPython dialogs, ProgressDialog)
- Existing: openpyxl, xlrd, field_cleaner, select_work_files, select_output_folder, THElogger

**No changes required:**
- `Helpers/dog_box/` (file selection)
- `Helpers/Clean_fields/` (text normalization)
- `water_logged.THElogger` (logging)

## 5. Risks

**Technical Risks:**
- **Modal dialog blocking**: If progress window is modal and user interacts with file system during processing, file locks may cause move operations to fail; mitigate by warning user in dialog ("Do not move files while processing")
- **Fast processing**: If file processing completes very quickly (< 1 second), progress window may flash briefly; acceptable for UX
- **Cancel timing**: If user cancels during file move operation, file may be half-moved; mitigate by wrapping move in try/except and not updating progress until move completes successfully

**Regressions:**
- If callback parameter is provided but is not callable, script will crash; add type checking in run() to validate callback is callable or None
- Module users who don't expect run() signature change may pass positional args and break; update docstring clearly

**Edge Cases:**
- Zero files selected: progress window still appears briefly; acceptable (immediate completion)
- Very large file count (1000+): progress bar may not update visually fast enough; acceptable (counter still accurate)
- Callback exception: if user-provided callback raises exception, catch and log, don't crash main processing loop

## 6. Implementation Strategy

1. **Create ProgressDialog wxPython class**
   - Subclass wx.Dialog with progress bar, counter label, filename label, cancel button
   - Constructor: takes total_file_count, parent window
   - Methods: `update(current_index, filename)` to update progress display, `is_cancelled()` to check cancel flag
   - Cancel button sets internal `_cancelled` flag to True
   - Size/layout: modal dialog centered on parent, minimal size 400x150 pixels

2. **Update PATonlineFinder.run() method signature**
   - Add parameter: `progress_callback=None` (optional callable)
   - Add validation: if callback provided, verify it's callable, otherwise raise TypeError
   - Callback signature: `def progress_callback(current_index: int, total_count: int, filename: str) -> bool:`
     - Params: current_index (0-based or 1-based?), total_count (total files), filename (basename only)
     - Returns: True to continue processing, False to cancel (or raise custom exception)

3. **Integrate cancel handling into run() processing loop**
   - Before processing loop: calculate total_file_count = len(files)
   - If callback provided, create progress dialog or call callback with initial counts
   - For each file in processing loop:
     - Call callback with (index, total, filename) or check progress window cancel flag
     - If callback returns False or cancel flag is set, break processing loop
     - Log cancellation at INFO level: "Processing cancelled by user after N files"
   - Ensure finalize_report() is called even if processing is cancelled

4. **Create standalone progress window factory**
   - In standalone mode (main()), create ProgressDialog and pass to run() via lambda callback
   - Lambda maps progress dialog update calls to run() callback signature
   - Let dialog be destroyed after run() completes (main() cleans up)

5. **Modify run() method flow**
   - After selecting files and output folder, log: "Processing {len(files)} file(s) to {output_dir}"
   - Create/initialize progress tracking (either callback or progress window)
   - Iterate files with try/except block to catch exceptions during individual file processing
   - Call progress update before each process_file() call
   - After process_file() completes (success or fail), increment progress counter
   - Check cancel flag between each file
   - After loop (or if cancelled), finalize_report()

6. **Add cancel checking points**
   - Check for cancel before calling process_file() (avoid starting file ops if cancel pending)
   - Option: check cancel after processing completes to allow current file to finish
   - Log cancellation decision clearly

7. **Update standalone main() entry point**
   - After file/folder selection, initialize wx.App if not already done
   - Create ProgressDialog(total_count, parent=None)
   - Define lambda callback that calls progress_dialog.update()
   - Pass lambda to finder.run(progress_callback=lambda idx, tot, fname: update_dialog(...) and continue_processing())
   - Handle dialog close/destruction cleanup

8. **Documentation**
   - Add module docstring clarification: "Supports progress callbacks for integration into other workflows"
   - Update run() docstring with callback parameter description
   - Add example in module docstring showing module usage with callback

## 7. Validation Strategy

**Tests to Create:**

- Test: `run()` method works without callback (backwards compatibility, existing behavior)
- Test: `run()` method accepts callable callback parameter
- Test: Callback is invoked with correct signature (current_index, total_count, filename)
- Test: Callback is invoked for each file in correct sequence
- Test: Cancel via callback (callback returns False) stops processing loop
- Test: Cancelled processing logs cancellation message at INFO level
- Test: Finalize_report() is called even when processing is cancelled
- Test: Invalid callback (not callable) raises TypeError with helpful message
- Test: Large file count (100+ files) progress updates complete without error
- Test: Progress callback exception is caught and logged, processing continues

**Standalone Verification:**

Run PATonline_FINDER.py with test files:

```bash
python Finders/PATonline_FINDER.py
```

Manual checks:
- Progress window appears after file selection
- Progress window displays "File X of Y" counter
- Progress window displays current filename being processed
- Progress bar fills as files are processed
- Cancel button stops processing (verify with log showing cancelled message)
- Progress window closes after processing completes or is cancelled
- Log contains INFO entry showing final count: "Processing cancelled by user after N files" (if cancelled) or "Processing complete. N file(s) categorized and moved." (if completed)

**User Verification:**

Run tests with:
```bash
.venv/bin/pytest Finders/test_patonline_finder.py -v -k "progress"
```

Create test files with various sizes and manually verify:
1. Small batch (2-3 files): progress window appears, counter increments visibly
2. Cancel mid-processing: verify files processed before cancel are moved, remaining files untouched
3. Module usage: import and call with custom callback, verify callback receives correct args

## 8. Rollback Plan

If implementation encounters issues:

1. **If progress window doesn't render correctly**:
   - Verify wxPython is properly installed: `python -c "import wx; print(wx.version())"`
   - Simplify ProgressDialog layout (remove optional elements like progress bar if it causes issues)
   - Fall back to console-only progress (print to stdout) without GUI

2. **If callback integration breaks existing behavior**:
   - Ensure `progress_callback=None` is default and run() works without it
   - Add feature flag or environment variable to disable progress window: `SKIP_PROGRESS=1 python PATonline_FINDER.py`

3. **If cancel doesn't work properly**:
   - Add manual timeout: if processing takes > 60 seconds, auto-cancel (configurable)
   - Log which file caused hang/stall for debugging

4. **Complete rollback**:
   - Revert PATonline_FINDER.py to previous version (before progress changes)
   - Remove ProgressDialog class entirely
   - Remove progress_callback parameter from run()
   - Script returns to previous behavior (no progress visibility)

---

## Implementation Notes

### Callback Signature Details

```python
def progress_callback(current_index: int, total_count: int, filename: str) -> bool:
    """
    Called during file processing to report progress.

    Args:
        current_index: 1-based index of current file being processed (1 to total_count)
        total_count: Total number of files to process
        filename: Basename of file currently being processed

    Returns:
        True to continue processing, False to cancel

    Raises:
        Any exception raised by callback is caught and logged; processing continues
    """
    pass
```

### Standalone Mode Flow

```
main()
  → select_work_files() → get file list
  → select_output_folder() → get output dir
  → create ProgressDialog(len(files), parent=None)
  → define lambda callback: lambda idx, tot, fname: progress_dialog.update(idx, fname)
  → finder.run(progress_callback=lambda_callback)
  → progress_dialog.Destroy()
  → app.Destroy()
```

### Module Mode Flow

```python
from Finders.PATonline_FINDER import PATonlineFinder

def my_progress_handler(idx, total, filename):
    print(f"Processing: {idx}/{total} - {filename}")
    return True  # continue

finder = PATonlineFinder()
finder.run(
    progress_callback=my_progress_handler,
    # or use different file selection logic:
    # files=[...], output_dir="..."
)
```

---

**File Locations:**

- Script: `/home/bigbox/Documents/Mworx/SPA_toolbox/Finders/PATonline_FINDER.py`
- Mission file: `/home/bigbox/Documents/Mworx/SPA_toolbox/Finders/MF-PATonline-progress.md`
- Tests: `/home/bigbox/Documents/Mworx/SPA_toolbox/Finders/test_patonline_finder.py` (update/extend)
