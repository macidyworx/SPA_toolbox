# Testing Guide

SPA_toolbox uses pytest for automated testing. Tests are organized by module in the `tests/` directory.

## Quick Start: Using `run_tests.py`

The **`run_tests.py`** wrapper script is the recommended way to run tests. It provides convenient test selection and **automatically filters JSON reports to show only failures** (keeping file sizes small).

### Common Commands

```bash
# All tests
python run_tests.py

# Specific test
python run_tests.py -t tests/test_dog_box/test_ssotsif.py::test_valid_sif

# Multiple tests
python run_tests.py -t tests/test_dog_box/test_ssotsif.py::test_valid_sif tests/test_clean_fields.py

# By path
python run_tests.py -t tests/test_dog_box/

# By keyword pattern
python run_tests.py -k "sif"
python run_tests.py -k "sif or work_files"

# Show all tests in JSON (including passed)
python run_tests.py -v

# Don't generate JSON report
python run_tests.py --no-json

# Get help
python run_tests.py --help
```

### Benefits of `run_tests.py`

✅ **Failure-only JSON reports** — Small file size (no passing test noise)
✅ **Flexible test selection** — By path, specific tests, or keyword
✅ **Automatic venv detection** — Uses `.venv/bin/pytest` if available
✅ **Clean summary output** — Shows passed/failed/skipped at a glance

---

## Direct pytest Commands (Advanced)

If you prefer to use pytest directly, here are the equivalent commands:

### Full Test Suite
```bash
pytest
```

### Run Tests by Feature (requires `@pytest.mark` decorators)
```bash
pytest -m dog_box
pytest -m clean_fields
pytest -m last_row
pytest -m file_sorter
pytest -m helpers
```

### Run Tests by Path
```bash
pytest tests/test_dog_box/
pytest tests/test_clean_fields.py
pytest tests/test_file_sorter/
```

### Run Specific Test
```bash
pytest tests/test_dog_box/test_ssotsif.py::test_valid_sif
```

### List All Tests
```bash
pytest --co -q
```

### Run with JSON Report (for automation/CI)
```bash
pytest --json-report --json-report-file=test_report.json
```

### Run and Stop on First Failure
```bash
pytest -x
```

### Verbose Output (show print statements)
```bash
pytest -s
pytest -vv
```

## Test Organization

```
tests/
  test_clean_fields.py      # Tests for Clean_fields helper
  test_last_row.py          # Tests for Last_row_finder helper
  test_dog_box/             # Tests for dog_box module
    test_ssotsif.py
    test_load_SSOT.py
    test_file_folder.py
    test_work_files.py
  test_file_sorter/         # Tests for File_sorter module
    test_file_sorter.py
    test_file_identifier.py
    test_config_loader.py
    test_path_resolver.py
    test_readers.py
    test_cell_utils.py
    test_file_cache.py
    test_unique_path.py
```

## Test Markers

Markers help organize tests by category. Tag test functions with `@pytest.mark.<marker>`:

```python
@pytest.mark.unit
def test_something():
    pass

@pytest.mark.dog_box
@pytest.mark.integration
def test_with_files(tmp_path):
    pass
```

### Available Markers

- `@pytest.mark.unit` — Fast unit tests (no file I/O)
- `@pytest.mark.integration` — Integration tests (use files or real modules)
- `@pytest.mark.slow` — Tests that take significant time
- `@pytest.mark.helpers` — Tests for Helpers module
- `@pytest.mark.clean_fields` — Tests for Clean_fields helper
- `@pytest.mark.last_row` — Tests for Last_row_finder helper
- `@pytest.mark.dog_box` — Tests for dog_box module
- `@pytest.mark.file_sorter` — Tests for File_sorter module
- `@pytest.mark.needs_files` — Tests that create/read files

## Shared Fixtures (conftest.py)

Common fixtures available in all tests:

### `project_root`
Returns the project root directory as a `Path` object.
```python
def test_something(project_root):
    path = project_root / "Helpers" / "Clean_fields"
    assert path.exists()
```

### `tmp_path` (pytest built-in)
Temporary directory for test files. Automatically cleaned up.
```python
def test_with_temp_files(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("data")
    assert test_file.exists()
```

### `tmp_xlsx` (custom)
Creates a temporary Excel file with sample data.
```python
def test_with_excel(tmp_xlsx):
    # tmp_xlsx is a Path to a temporary .xlsx file
    import openpyxl
    wb = openpyxl.load_workbook(tmp_xlsx)
    assert wb is not None
```

## Adding New Tests

1. Create test file in `tests/` or appropriate subdirectory
2. Name it `test_<module>.py`
3. Add `@pytest.mark.<feature>` decorators to group tests
4. Use `tmp_path` fixture for temporary files
5. Run: `pytest tests/test_<module>.py`

### Example
```python
import pytest
from Helpers.Clean_fields.clean_field import field_cleaner

@pytest.mark.clean_fields
@pytest.mark.unit
def test_field_cleaner_simple():
    assert field_cleaner("Hello World") == "helloworld"

@pytest.mark.clean_fields
@pytest.mark.integration
def test_field_cleaner_with_files(tmp_path):
    # Test that uses files
    pass
```

## Configuration

Test discovery and configuration is in `pytest.ini`:
- `testpaths = tests` — Search for tests in `tests/` directory
- `python_files = test_*.py` — Test file naming convention
- `python_functions = test_*` — Test function naming convention
- `addopts = -v --strict-markers` — Default options (verbose, strict markers)

## CI/CD Integration

To generate a JSON report for CI/CD pipelines:
```bash
pytest --json-report --json-report-file=test_report.json
```

The report is written to `test_report.json` and can be parsed by CI/CD tools.
