# File_sorter Review — Old SPAhub Implementation

## What It Does

Automatically sorts educational assessment files (Excel, CSV, XML) into folders by test type. Uses a YAML-driven configuration system with two matching strategies: exact cell checks (KEYS) and area searches (FIND_KEYS).

## Architecture

```
File_sorter.sort_files()
  → load test_identifiers.yaml (45+ test types)
  → walk input folder recursively
  → for each file:
      → get extension
      → identify_file_type() via File_IDer2
        → check cache (MD5 hash + mtime)
        → for each test type (priority order):
            → check KEYS (specific cell values)
            → check FIND_KEYS (search first 20 rows × 30 cols)
            → normalize all text with field_cleaner()
      → copy file to SORTED/{TestType}/
  → print summary (counts + top 5 slowest files)
```

## Key Files in Old Repo

| File | Lines | Purpose |
|------|-------|---------|
| `File_sorter/File_sorter.py` | 140 | Main sorting module |
| `File_IDer2/File_Identifier.py` | 621 | File type identification engine |
| `File_IDer2/test_Manager/test_identifiers.yaml` | 1228 | 45+ test type configurations |
| `File_IDer2/test_Manager/test_Manager.py` | 41 | GUI for managing test configs |
| `File_IDer2/test_Manager/add_test.py` | 324 | GUI: add new test types |
| `File_IDer2/test_Manager/edit_test.py` | 440 | GUI: edit/delete test types |
| `File_IDer2/test_Manager/config_utils.py` | 226 | YAML validation and utilities |
| `Helpers/Clean_fields/clean_field.py` | 57 | Text normalization |

## YAML Config Structure (per test type)

```yaml
TestType:
  priority: 1          # lower = checked first
  folder: "FolderName"
  group: "GroupName"
  area: "AreaName"
  SWAPPER_FILE: "path/to/swapper.py"
  SURNAME_HEADER: "Surname"
  FIRSTNAME_HEADER: "First Name"
  ID_HEADER: "Student ID"
  xlsx:
    KEYS:
      - sheet: 0
        cell: A1
        startswith: "text"
      - sheet: 0
        cell: B2
        contains: ["frag1", "frag2"]
    FIND_KEYS:
      - sheet: 0
        startswith: "text to find anywhere"
  xls: ...
  csv: ...
  xlsm: ...
```

## Matching Logic

1. **KEYS** — exact cell checks: open file, read specific cell, match with `startswith` or `contains` (all fragments must be present)
2. **FIND_KEYS** — area search: scan first 20 rows × 30 columns for any cell matching `startswith`
3. All comparisons normalized via `field_cleaner()` (unicode, whitespace, case)
4. Test types checked in priority order (1-45), first match wins

## Callback System

```python
sort_files(
    input_folder,
    prompt_callback=None,    # user input (default: input())
    message_callback=None,   # output messages (default: print())
    progress_callback=None,  # progress tracking (default: no-op)
)
```

## Strengths to Keep

1. **YAML-driven config** — add test types without code changes
2. **Priority system** — faster matching, most common types first
3. **Dual matching** (KEYS + FIND_KEYS) — handles both structured and messy files
4. **field_cleaner normalization** — already in our new repo
5. **Multi-format** — xlsx, xls, csv, xml, xlsm all handled
6. **Hash+mtime caching** — avoids re-identifying same file
7. **shutil.copy2()** — preserves file metadata
8. **Callback pattern** — decoupled from GUI/CLI

## Issues to Fix in New Version

### Critical

- **No duplicate file handling**: Same-name files overwrite silently. Need `_get_unique_path()` pattern from our other scripts.
- **YAML path is fragile**: Hard-coded relative path, breaks if structure changes. Should use `__file__`-relative path.
- **No schema validation**: Malformed YAML entries cause cryptic errors.

### Performance

- **Hard-coded limits**: 20 rows × 30 cols for FIND_KEYS, 10MB file size cap. Should be configurable.
- **Tracks ALL timings in memory**: Only shows top 5 but stores all. Use a bounded list.

### Architecture

- **XLS cell reference inconsistency**: xlsx uses "A1" strings, xls uses [row, col] lists. Confusing config format, should unify.
- **CSV FIND_KEYS limited**: No `contains` support, `sheet` value used as row index (misleading).
- **DEBUG_MODE is a global flag**: No way to enable without editing code. Should use logger levels.
- **test_Manager GUI uses Tkinter**: Rest of our project uses wxPython. Should be consistent.
- **File_Identifier is monolithic**: 621 lines, could be split into per-format handlers.

### Missing Features

- **No progress tracking integration**: Has callback stub but no actual progress dialog
- **No logging**: Uses print/callbacks only, not water_logged
- **No cancel support**: Can't abort mid-sort
- **SWAPPER_FILE not validated**: Config references swapper scripts but never checks they exist
- **No dry-run mode**: Can't preview what would be sorted without actually copying
- **XML support minimal**: Only basic pattern, rarely used

## Recommendations for New Version

### Structure

```
Finders/
  File_sorter/
    file_sorter.py           # Main sorting module
    file_identifier.py       # Identification engine (uses field_cleaner)
    test_configs/
      test_identifiers.yaml  # Test type definitions
    test_manager/             # wxPython GUI for config management
      manager.py
      add_test.py
      edit_test.py
      config_utils.py
```

### Key Changes

1. **Use water_logged.THElogger** instead of print/callbacks
2. **Use our progress_callback pattern** (current_index, total_count, filename) → bool
3. **Add cancel support** via callback return value
4. **Use `_get_unique_path()`** for duplicate filenames
5. **Unify cell references** — always use "A1" notation, convert internally
6. **Add YAML schema validation** on load
7. **wxPython for test_manager GUI** (match project convention)
8. **Use field_cleaner from Helpers/** (already exists in new repo)
9. **Dual-mode** (standalone + module) per CLAUDE.md convention
10. **Configurable limits** — scan range, file size cap as parameters

### What to Port As-Is

- `test_identifiers.yaml` — copy and validate
- Matching logic (KEYS + FIND_KEYS with priority) — proven and solid
- Hash+mtime caching — good performance optimization
- field_cleaner integration — already in new repo
