# Orphaned Tests

These test files are **not part of the active test suite** and are excluded from pytest discovery by `norecursedirs = orphaned_tests` in `pytest.ini`.

## Why They're Here

These tests were written for modules that no longer exist in the current codebase:

- `test_file_folder.py` — Tests for `Helpers.dog_box.file_folder` (module removed/refactored)
- `test_load_SSOT.py` — Tests for `Helpers.dog_box.load_SSOT` (functionality moved to `ssotsif.py`)
- `test_try_me_load_SSOT.py` — Tests for demo code; depends on external `tool_box.water_logged` logger

## What to Do

### Option 1: Delete Permanently
If these modules are no longer needed, delete this directory:
```bash
rm -rf tests/orphaned_tests
```

### Option 2: Restore/Refactor
If you want to restore these tests:
1. Review the test code to understand what was being tested
2. Check if similar functionality exists in current modules (e.g., `_validate_sif` in `ssotsif.py`)
3. Rewrite tests to match current module structure
4. Move back to `tests/test_dog_box/` and update imports

## Next Steps

- [ ] Review if these modules should be restored
- [ ] If not needed, delete this directory
- [ ] Update project documentation if functionality was replaced
