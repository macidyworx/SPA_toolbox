# MF-testing-process.md — Testing Workflow Standardization

## Context & Analysis

### Current State
- **Tests scattered**: Across Helpers/ and Finders/ directories
  - `Helpers/Clean_fields/test_clean_fields.py`
  - `Helpers/Last_row_finder/test_last_row.py`
  - `Helpers/dog_box/tests/` (5 test files)
  - `Finders/File_sorter/tests/` (inferred)
- **Framework**: Using pytest with parametrize
- **Custom runner**: `ZZ_test-RUNNER.py` provides git-diff-based selective testing + custom JSON reporting
- **No configuration**: No pytest.ini, setup.cfg, or pyproject.toml in project root

### Current Workflow Strengths
- ✓ Existing ZZ_test-RUNNER.py automates change detection
- ✓ Custom reporting shows only failures
- ✓ Can run full suite or changed tests only
- ✓ Proven in another repo (user likes it)

### Current Workflow Gaps
- ✗ No standardized test directory layout
- ✗ No pytest configuration (discovery, markers, fixtures)
- ✗ No way to easily run "all tests for a feature" (e.g., all dog_box tests, all File_sorter tests)
- ✗ Tests coexist with source code (not separated into tests/ folder)
- ✗ No centralized test markers or tagging system

---

## Pythonic/Industry Standard Practices

**Standard Python testing layout:**
```
project/
  src/
    module_a/
    module_b/
  tests/
    test_module_a.py
    test_module_b.py
  pytest.ini (or pyproject.toml [tool.pytest.ini_options])
```

**pytest conventions:**
- `tests/` folder separate from source
- `test_*.py` or `*_test.py` naming
- Markers for categorizing tests (`@pytest.mark.unit`, `@pytest.mark.integration`)
- `conftest.py` for shared fixtures
- `pytest.ini` for configuration (testpaths, markers, discovery rules)

**Benefits of standardization:**
- Test discovery is automatic and predictable
- Other tools and developers understand structure immediately
- CI/CD integration is easier
- Flexible test selection with markers

---

## Testing Workflow Options

### OPTION 1: Minimal Change (MACish) — Keep ZZ_test-RUNNER.py, Add Markers

**Description:**
- Keep current scattered test layout (tests stay in Helpers/ and Finders/ folders)
- Keep ZZ_test-RUNNER.py as is for git-diff-based selective runs
- Add pytest.ini with marker definitions
- Add `@pytest.mark` decorators to group tests by feature
- Add `.venv/bin/pytest --co -q` tip for users to list tests by marker

**Is it Pythonic/Standard?**
- **MACish** — This is pragmatic for a personal project but not a standard structure. Pytest *can* discover scattered tests, but the standard is `/tests` folder.

**Pros:**
- ✓ Minimal refactoring (no file moves)
- ✓ Keeps ZZ_test-RUNNER.py working as-is
- ✓ Markers allow selective runs: `pytest -m dog_box`
- ✓ Very familiar to user (builds on existing script)
- ✓ Fast to implement
- ✓ Works for personal projects

**Cons:**
- ✗ Not standard Python structure (harder to onboard others)
- ✗ Tests stay mixed with source (harder to package/distribute)
- ✗ pytest discovery could be fragile if structure changes
- ✗ CI/CD integration assumes knowledge of custom runner
- ✗ Doesn't address "where should test X go?" question long-term

---

### OPTION 2: Standardized Layout + Keep Custom Runner (Hybrid)

**Description:**
- Create top-level `tests/` directory
- Move all tests to `tests/` with same structure as source:
  ```
  tests/
    test_clean_fields.py
    test_last_row.py
    test_dog_box/
      test_ssotsif.py
      test_ssotsif_load.py
      ...
    test_file_sorter/
      test_file_identification.py
      ...
  ```
- Keep ZZ_test-RUNNER.py but update paths
- Add `pytest.ini` with testpaths, markers, fixtures
- Add `conftest.py` for shared fixtures if needed
- Both selective runs (via git diff) and marker-based runs work

**Is it Pythonic/Standard?**
- **Industry Standard** — This follows PEP 420 and standard pytest/setuptools conventions.

**Pros:**
- ✓ Tests completely separated from source (cleaner structure)
- ✓ Standard Python layout (familiar to anyone coming to project)
- ✓ `pytest.ini` documents test configuration centrally
- ✓ Scales well as project grows
- ✓ Easy to document: "pytest discovers tests/ automatically"
- ✓ ZZ_test-RUNNER.py still works with updated paths
- ✓ Can use both git-diff selective AND marker-based selective runs
- ✓ Enables CI/CD without custom script knowledge

**Cons:**
- ✗ Requires moving files (medium refactoring effort)
- ✗ Git blame gets muddied by moves (mitigable with `-C` flag)
- ✗ If other repos depend on test locations, they break
- ✗ More boilerplate (pytest.ini, conftest.py) initially

---

### OPTION 3: Full pytest + pytest-markers + Documentation (Pure Standard)

**Description:**
- Same layout as Option 2 (`tests/` folder, separated from source)
- Create `pytest.ini` with:
  - Markers: `unit`, `integration`, `slow`, `helpers`, `file_sorter`, `dog_box`, etc.
  - testpaths = ["tests"]
  - Python path configuration
- Create `conftest.py` with shared fixtures (temp paths, sample data, cleanup)
- Create `TESTING.md` documenting:
  - How to run all tests
  - How to run by marker
  - How to run a single feature
  - What each marker means
- Retire or minimize ZZ_test-RUNNER.py (pytest does most of it natively)
- Use `pytest -k` for pattern matching, `-m` for markers

**Example commands** (from TESTING.md):
```bash
pytest                          # all tests
pytest tests/test_dog_box/      # feature-specific
pytest -m dog_box               # by marker
pytest -k "clean_field"         # by keyword
pytest --co -q                  # list all tests
```

**Is it Pythonic/Standard?**
- **Pythonic + Industry Standard** — This is the approach used by Django, Flask, requests, pytest itself, etc.

**Pros:**
- ✓ Fully standard Python testing layout
- ✓ No custom tooling needed (pytest is enough)
- ✓ Markers enable flexible test selection without custom script
- ✓ conftest.py centralizes test setup (DRY)
- ✓ TESTING.md is self-documenting (others understand immediately)
- ✓ Easy CI/CD integration (just `pytest`)
- ✓ Best for learning Python testing best practices
- ✓ Easier to add plugins later (pytest-cov, pytest-timeout, etc.)

**Cons:**
- ✗ Requires most refactoring (moving files, creating config, learning markers)
- ✗ ZZ_test-RUNNER.py becomes less relevant (might feel like "lost" work)
- ✗ More setup initially (pytest.ini, conftest.py, TESTING.md)
- ✗ Overkill if project stays small and isolated
- ✗ Pytest.ini/pyproject.toml adds files to gitignore/maintenance

---

## Clarifying Questions

Before finalizing the mission plan, I need to understand your preferences:

1. **Team/Publishing Context**
   - Will anyone else (now or future) work on this project or use these tests?
   - Do you plan to publish or distribute SPA_toolbox?
   - → *Affects: Option 2/3 more valuable if sharing; Option 1 fine for solo projects*

2. **ZZ_test-RUNNER.py Attachment**
   - How attached are you to the ZZ_test-RUNNER.py as it is?
   - Would you be willing to simplify or retire it if pytest + markers do 90% of it?
   - → *Affects: Option 2 keeps it; Option 3 minimizes it*

3. **Feature-Based vs. Full-Suite Runs**
   - When you test during development, do you:
     - Usually: Run tests for the feature you're changing (selective)?
     - Or: Run full suite every time (git diff detection is bonus)?
   - → *Affects: All options support selective, but Option 3 makes it easiest*

4. **Growth Expectations**
   - Do you expect more test files as you add features?
   - Is the codebase relatively stable, or will it grow significantly?
   - → *Affects: Option 1 works now; Option 2/3 scale better*

5. **Skill Building vs. Pragmatism**
   - You mentioned "sticking to Pythonic practices helps me develop skills"
   - How much do you weight: *current efficiency* vs. *long-term skill growth*?
   - → *Affects: Option 1 is fastest; Option 3 is most educational*

---

## Recommendation (Pending Your Answers)

**If you want to stay flexible and build skills:**
→ **Option 2 (Hybrid)** is the sweet spot
- Standard layout, but keep ZZ_test-RUNNER.py
- Less work than Option 3, more professional than Option 1
- Opens door to markers without forcing it

**If you want maximum long-term value:**
→ **Option 3 (Pure Standard)**
- Most "Pythonic," best for learning
- Small initial time investment pays off in clarity
- Scales to any future collaborators or publishing

**If you value "works great, don't fix it":**
→ **Option 1 (MACish)**
- Minimal changes, keeps momentum
- Fine for personal projects
- Revisit in 6 months if structure becomes a pain point

---

## Your Context (From Clarification)

- **Solo learning project**: Not sharing, but want to learn industry practices for personal development ✓
- **JSON reporting is essential**: Keep the failed-test JSON report feature ✓
- **Flexible testing needs**: Support both selective and full-suite runs; agent can advise what to test ✓
- **Speed is priority**: Fastest implementation preferred ✓

---

## CHOSEN STRATEGY: Option 3 (Pure Standard)

### Why Option 3 for You

✓ **Fully Pythonic** (industry-standard pytest + markers)
✓ **Zero maintenance as repo grows** (pytest handles everything natively)
✓ **Better for AI agents** (standard pytest is well-documented and understood)
✓ **JSON reports via pytest plugin** (not custom script; scales automatically)
✓ **Dynamic repo ready** (markers + pytest scale with your growing codebase)
✓ **Selective + full testing is trivial** (no script logic needed)

---

## Implementation Strategy

### Phase 1: Create Test Directory Structure

Create `tests/` directory mirroring the source layout:
```
tests/
  conftest.py                     # Shared fixtures
  test_clean_fields.py            # From Helpers/Clean_fields/
  test_last_row.py                # From Helpers/Last_row_finder/
  test_dog_box/
    __init__.py
    test_ssotsif.py
    test_load_ssot.py              # Renamed from test_try_me_load_SSOT.py / test_load_SSOT.py
    test_file_folder.py
    test_work_files.py
  test_file_sorter/
    __init__.py
    test_file_identification.py    # Identify file tests
    # (Consolidate any other File_sorter tests here)
```

### Phase 2: Move Test Files

```bash
mkdir -p tests/test_dog_box tests/test_file_sorter

# From Helpers/Clean_fields/
mv Helpers/Clean_fields/test_clean_fields.py tests/

# From Helpers/Last_row_finder/
mv Helpers/Last_row_finder/test_last_row.py tests/

# From Helpers/dog_box/tests/
mv Helpers/dog_box/tests/*.py tests/test_dog_box/

# From Finders/File_sorter/tests/ (if exists)
# mv Finders/File_sorter/tests/*.py tests/test_file_sorter/

# Create package markers
touch tests/__init__.py tests/test_dog_box/__init__.py tests/test_file_sorter/__init__.py
```

### Phase 3: Create pytest.ini

Create `pytest.ini` in project root:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers

# Test markers for organizing tests
markers =
    unit: Unit tests (fast, no I/O)
    integration: Integration tests (may use real files)
    slow: Tests that take significant time
    helpers: Tests for Helpers/ modules
    clean_fields: Tests for Clean_fields helper
    last_row: Tests for Last_row_finder helper
    dog_box: Tests for dog_box (file dialogs)
    file_sorter: Tests for File_sorter
    needs_files: Tests that create/read files
```

### Phase 4: Create conftest.py

Create `tests/conftest.py` with shared fixtures:
```python
import pytest
from pathlib import Path
import sys

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture
def tmp_xlsx(tmp_path):
    """Create a temporary Excel file for testing."""
    try:
        import openpyxl
        xlsx_path = tmp_path / "test.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Header1", "Header2"])
        ws.append(["Value1", "Value2"])
        wb.save(xlsx_path)
        wb.close()
        return xlsx_path
    except ImportError:
        pytest.skip("openpyxl not available")
```

### Phase 5: Add pytest-json-report Plugin

Install the JSON reporting plugin:
```bash
pip install pytest-json-report
```

This gives you:
- `pytest --json-report` generates JSON report automatically
- Report written to `.report.json`
- Can be integrated into CI/CD or automated workflows
- No custom script needed

### Phase 6: Update/Retire ZZ_test-RUNNER.py

**Option A (Minimal):** Keep it for git-diff automation, update to use pytest-json-report:
```python
# ZZ_test-RUNNER.py (simplified)
import subprocess
from pathlib import Path

def main():
    result = subprocess.run(
        ["pytest", "--json-report", "--json-report-file=.report.json"],
        capture_output=True,
        text=True
    )

    # Print output
    print(result.stdout)

    if result.returncode != 0:
        print("❌ Tests failed. See .report.json for details.")
    else:
        print("✅ All tests passed.")

if __name__ == "__main__":
    main()
```

**Option B (Retirement):** Delete ZZ_test-RUNNER.py entirely. Standard pytest commands replace it:
```bash
pytest                    # Full suite
pytest -m dog_box        # By marker
pytest tests/test_dog_box/ # By path
```

**Recommendation:** Start with Option B (retire it). If you find you need git-diff automation later, add it back with the simplified version above.

### Phase 7: Create TESTING.md

Create `TESTING.md` in project root (user documentation):
```markdown
# Testing Guide

## Running Tests

### Full Test Suite
\`\`\`bash
pytest
\`\`\`

### Run Tests by Feature
\`\`\`bash
pytest -m dog_box
pytest -m clean_fields
pytest -m file_sorter
pytest -m helpers
\`\`\`

### Run Tests by Path
\`\`\`bash
pytest tests/test_dog_box/
pytest tests/test_clean_fields.py
\`\`\`

### Run Specific Test
\`\`\`bash
pytest tests/test_dog_box/test_ssotsif.py::test_valid_sif
\`\`\`

### List All Tests
\`\`\`bash
pytest --co -q
\`\`\`

### Run with JSON Report (for CI/automation)
\`\`\`bash
pytest --json-report --json-report-file=test_report.json
\`\`\`

## Test Markers

- `@pytest.mark.unit` — Fast tests, no file I/O
- `@pytest.mark.integration` — Tests that use files or external resources
- `@pytest.mark.slow` — Tests that take significant time
- `@pytest.mark.helpers` — Tests for Helpers module tests
- `@pytest.mark.dog_box` — dog_box tests
- `@pytest.mark.clean_fields` — clean_field tests
- `@pytest.mark.last_row` — Last_row_finder tests
- `@pytest.mark.file_sorter` — File_sorter tests

## Adding Tests

1. Create test file in `tests/`
2. Name it `test_<module>.py`
3. Add `@pytest.mark.<feature>` to test functions
4. Run: `pytest tests/test_<module>.py`

## Fixtures (conftest.py)

- `tmp_path` (pytest built-in) — Temporary directory
- `project_root` (custom) — Path to project root
- `tmp_xlsx` (custom) — Temporary Excel file
```

### Phase 8: Test Commands Reference

All testing needs covered by standard pytest:
```bash
# Development: run tests for what you changed
pytest tests/test_dog_box/

# Audit: run all tests
pytest

# By marker: run all dog_box tests (even across directories)
pytest -m dog_box

# Debugging: stop on first failure
pytest -x

# Verbosity: see more details
pytest -vv

# Show print statements
pytest -s

# JSON report (for automation/CI)
pytest --json-report
```

---

## Files to Create/Modify

| File | Action | Reason |
|------|--------|--------|
| `tests/` | **Create** | Standard test layout |
| `tests/conftest.py` | **Create** | Shared fixtures |
| `tests/test_clean_fields.py` | **Move** | From Helpers/Clean_fields/ |
| `tests/test_last_row.py` | **Move** | From Helpers/Last_row_finder/ |
| `tests/test_dog_box/` | **Create + move files** | Group dog_box tests |
| `tests/test_file_sorter/` | **Create + move files** | Group File_sorter tests |
| `pytest.ini` | **Create** | Configure pytest + markers |
| `TESTING.md` | **Create** | User documentation |
| `ZZ_test-RUNNER.py` | **Delete** | Replaced by pytest + markers |
| Old test directories | **Delete** | After move verified |

---

## Dependencies to Add

```bash
pip install pytest-json-report
```

This gives you JSON reporting without a custom script.

---

## Rollout Plan (2 Phases)

### Phase 1: Setup (Day 1-2)
1. Create `tests/` directory structure
2. Move test files (use `git mv` to preserve history)
3. Create `pytest.ini`, `conftest.py`, `TESTING.md`
4. Install `pytest-json-report`
5. Verify: `pytest` should pass

### Phase 2: Cleanup & Markers (Day 3-4)
1. Delete old test directories from Helpers/Finders
2. Add `@pytest.mark.<feature>` to existing tests
3. Delete `ZZ_test-RUNNER.py`
4. Commit: "refactor: standardize testing structure with pytest markers"
5. Document in TESTING.md (already done)

---

## Why This Works for Your Repo

✓ **No maintenance burden** — pytest + markers scale automatically as you add tests
✓ **AI-friendly** — Standard pytest is well-understood by agents
✓ **Flexible testing** — Markers + paths handle selective + full suite easily
✓ **JSON reports** — pytest-json-report plugin handles this natively
✓ **Growing repo ready** — Just add tests + markers, no script changes needed
✓ **Pythonic** — Industry-standard testing layout and practices
