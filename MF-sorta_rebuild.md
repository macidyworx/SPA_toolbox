# Mission File: File Sorter Rebuild

Rebuild the file sorting system from the old SPAhub repo into SPA_toolbox.
Reference docs: `sorta.md` (review), `sortaPHASE2.md` (future features).

---

## Phase 1 — Foundation

### Step 1: Create folder structure and empty modules -- DONE
- [x] Create `Finders/File_sorter/` directory
- [x] Create `Finders/File_sorter/__init__.py`
- [x] Create `Finders/File_sorter/file_identifier.py` (empty scaffold)
- [x] Create `Finders/File_sorter/file_sorter.py` (empty scaffold)
- [x] Create `Finders/File_sorter/test_configs/` directory
- [x] Create `Finders/File_sorter/test_configs/__init__.py`

### Step 2: Port and validate test_identifiers.yaml -- DONE
- [x] Copy `test_identifiers.yaml` from old repo into `Finders/File_sorter/test_configs/`
- [x] Review YAML structure — verify all 45+ test types are present and well-formed
- [x] Unify cell references: convert all xls `[row, col]` entries to `"A1"` notation
- [x] Unify cell references: convert all csv `row`/`col` entries to `cell` with `"A1"` notation
- [x] Convert SWAPPER_FILE backslash paths to forward slashes
- [x] Add `variant` and `sort_strategy` fields to each test type (default `sort_strategy: "{folder}"`)
- [x] Ensure YAML loads cleanly with `yaml.safe_load()`

### Step 3: YAML config loader with validation -- DONE
- [x] Create `Finders/File_sorter/config_loader.py`
- [x] Load YAML using `__file__`-relative path (not hard-coded)
- [x] Validate required fields per test type: `priority`, `folder`, at least one format key
- [x] Validate sort_strategy template variables are valid (`{type}`, `{group}`, `{variant}`, `{area}`, `{folder}`)
- [x] Return test types sorted by priority (lower = first)
- [x] Raise clear errors for malformed entries
- [x] Create `Finders/File_sorter/tests/test_config_loader.py` — list tests for user

---

## Phase 2 — File Identification Engine

### Step 4: Cell reference utilities -- DONE
- [x] Create `Finders/File_sorter/cell_utils.py`
- [x] `parse_cell_ref("B2")` -> `(row, col)` tuple (1-indexed)
- [x] Handle edge cases: multi-letter columns (AA1), case insensitive
- [x] Create `Finders/File_sorter/tests/test_cell_utils.py` — list tests for user

### Step 5: Format-specific readers -- DONE
- [x] Create `Finders/File_sorter/readers/` directory with `__init__.py`
- [x] Create `readers/base_reader.py` — abstract base with `_normalize()` using `field_cleaner()`
- [x] Create `readers/xlsx_reader.py` — read cell value and scan area (openpyxl)
- [x] Create `readers/xls_reader.py` — read cell value and scan area (xlrd)
- [x] Create `readers/csv_reader.py` — read cell value and scan area (csv stdlib)
- [x] Create `readers/xlsm_reader.py` — inherits from xlsx_reader (openpyxl handles both)
- [x] Each reader exposes: `read_cell(path, sheet, cell_ref)` and `scan_area(path, sheet, max_rows, max_cols)`
- [x] All text output normalized via `field_cleaner()`
- [x] READERS dict maps extensions to reader classes
- [x] Create `Finders/File_sorter/tests/test_readers.py` — list tests for user

### Step 6: File identifier core -- DONE
- [x] Create `Finders/File_sorter/file_identifier.py`
- [x] `identify_file(filepath, test_configs)` -> `(name, config)` or `(None, None)`
- [x] Route to correct reader based on file extension
- [x] Check KEYS first (specific cell matches: `startswith`, `contains`)
- [x] Check FIND_KEYS second (area scan within configurable rows x cols)
- [x] All comparisons use `field_cleaner()` — normalize both config values and cell values
- [x] Priority order: iterate test types by priority, first match wins
- [x] Configurable scan limits: `max_scan_rows` (default 20), `max_scan_cols` (default 30)
- [x] FIND_KEYS caches scan results per (filepath, sheet) to avoid re-scanning
- [x] Create `Finders/File_sorter/tests/test_file_identifier.py` — list tests for user

---

## Phase 3 — File Sorter Module

### Step 7: Sort strategy / path resolver -- DONE
- [x] Create `Finders/File_sorter/path_resolver.py`
- [x] `resolve_sort_path(test_name, test_config, base_output_dir)` -> full output directory path
- [x] Read `sort_strategy` template from test config (default: `"{folder}"`)
- [x] Substitute template variables: `{type}`, `{group}`, `{variant}`, `{area}`, `{folder}`
- [x] Sanitize path components (no `..`, no absolute paths in templates)
- [x] Empty segments filtered out (e.g. empty variant doesn't create empty dirs)
- [x] Create `Finders/File_sorter/tests/test_path_resolver.py` — list tests for user

### Step 8: Duplicate file handler -- DONE
- [x] Create `Finders/File_sorter/unique_path.py`
- [x] `get_unique_path(filepath)` -> path with `_1`, `_2` suffix if name exists
- [x] Matches pattern used elsewhere in SPA_toolbox
- [x] Create `Finders/File_sorter/tests/test_unique_path.py` — list tests for user

### Step 9: Hash + mtime cache -- DONE
- [x] Create `Finders/File_sorter/file_cache.py`
- [x] Cache keyed on `(filepath, md5_hash, mtime)`
- [x] `get_cached_type(filepath)` -> test type name or `None`
- [x] `set_cached_type(filepath, test_type)` -> stores result
- [x] Bounded LRU cache (configurable, default 1000)
- [x] Create `Finders/File_sorter/tests/test_file_cache.py` — list tests for user

### Step 10: Main file_sorter module -- DONE
- [x] Create `Finders/File_sorter/file_sorter.py`
- [x] Dual-mode design (standalone + module) per CLAUDE.md — FileSorter class + main()
- [x] `FileSorter.sort_files(input_folder, output_folder)` main entry point
- [x] Walk input folder recursively, filter by supported extensions
- [x] For each file: check cache -> identify -> resolve sort path -> copy with `shutil.copy2()`
- [x] Use `get_unique_path()` for duplicate filenames
- [x] Callback system: `progress_callback(current, total, filename) -> bool` (False = cancel)
- [x] `message_callback` for status messages (default: `print`)
- [x] Track and report summary: counts per test type, unidentified files list
- [x] Bounded timing list (top N slowest files, default 5) via heapq
- [x] File size cap (configurable, default 10MB, skip with warning)
- [x] Create `Finders/File_sorter/tests/test_file_sorter.py` — list tests for user

---

## Phase 4 — Integration and Polish

### Step 11: Package wiring -- DONE
- [x] Update `Finders/File_sorter/__init__.py` with public API exports
- [x] Exports: `FileSorter`, `identify_file`, `load_test_configs`
- [x] Verify standalone: `python -m Finders.File_sorter.file_sorter`

### Step 12: Update project docs -- DONE
- [x] Update `CLAUDE.md` project structure section to include `Finders/File_sorter/`
- [x] Add usage examples for FileSorter, identify_file, load_test_configs
- [x] Add File_sorter tests to testing commands section

### Step 13: Final review -- DONE
- [x] Run full test suite — 156 passed in 1.78s
- [x] Added missing `Finders/__init__.py` for package resolution
- [x] Check all field_cleaner() usage normalizes both sides
- [x] Check no hard-coded paths remain
- [x] Check dual-mode works (module import + standalone)
- [x] Verify sort_strategy default (`{folder}`) produces same output as old system

---

## Out of Scope (Phase 2 — see sortaPHASE2.md)
- YAML validation helper tool
- Configurable sort strategies per test type (variant/group templates)
- test_manager wxPython GUI (add/edit/delete test types)
- Dry-run mode
- Cancel support mid-sort
- XML format support
