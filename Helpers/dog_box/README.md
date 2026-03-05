# dog_box/file_folder.py

Utility functions for simple file/folder selection dialogs used by the
`dog_box` collection of helper scripts. This module encapsulates a minimal
wxPython dialog that asks the user whether they want to work with files or a
folder and returns the choice.

## Functionality

* `choose_files_or_folders()` – displays a two‑button dialog with the
  question “Would you like to process Files or Folders?”.
  * Returns the string `'files'` or `'folders'` depending on which button the
    user clicked.
  * Returns `None` if the dialog was closed without making a selection.
  * Dialog is centered on the screen to ensure visibility.

The module has no external dependencies beyond `wx` and the standard library,
and is intentionally lightweight so it can be imported by other scripts without
bringing in a full application framework.

## Example usage

```python
from tool_box.Helpers.dog_box.file_folder import choose_files_or_folders

choice = choose_files_or_folders()
if choice == "files":
    # open a FileDialog
elif choice == "folders":
    # open a DirDialog
else:
    # user cancelled
```

The companion script originally at `dog_box/try_me.py` has been moved to
`dog_box/testing_files/try_me_file_folder.py` and continues to provide a
simple demonstration with logging.

## Notes

* This module is part of the SPAhub repository and follows its coding
  conventions. It does not add `tool_box` to `sys.path`; callers are
  responsible for ensuring their environment is configured correctly.
* If additional functionality is required (e.g. multiple file selection within
  this dialog), it should be added here and corresponding tests created.

---

## dog_box/load_SSOT.py

Helper for selecting a single SSOT (single source of truth) workbook.  The
caller passes a list of headers and may also specify which row contains those
headers (defaults to row 2 to allow a title row on line 1).  The function
validates the chosen `.xlsx` file before returning its path.  See the
module docstring for usage details.

### Demo scripts

* `testing_files/try_me_file_folder.py` – simple file/folder picker with logging.
* `testing_files/try_me_load_SSOT.py` – demo for the SSOT helper; headers and
  header_row can be edited in the script, and rows are logged to show
  behavior.

### Tests

Unit tests live in `dog_box/tests/`:

* `test_load_SSOT.py` – covers header validation logic.
* `test_try_me_load_SSOT.py` – exercises the demo helper for logging.
