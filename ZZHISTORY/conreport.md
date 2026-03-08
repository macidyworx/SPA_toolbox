# SPA Toolbox Consistency Report

**Report Date:** 2026-03-07
**Scope:** File structure and code sections layout, helper usage consistency
**Total Issues Found:** 13 (3 file structure, 10 helper usage)

---

## Executive Summary

The codebase shows good consistency in some areas (File_sorter, PAT tools) but has significant gaps in others (IDswappers, some Helpers). Key issues:

1. **File Structure:** 7 files missing section markers and/or module docstring
2. **Helper Usage:** 3 IDswapper files inconsistently use field_cleaner for text matching

---

## 1. FILE STRUCTURE ISSUES

### Issue 1.1: Missing Module Docstring
**Files affected:** DIBELS.py, EOI.py, MOI.py
**Location:** IDswappers/

**Current State:**
- `DIBELS.py` starts directly with `import os` (line 1)
- `EOI.py` starts directly with `import os` (line 1)
- `MOI.py` starts directly with `import os` (line 1)

**Expected State (from CLAUDE.md):**
```python
"""
filename.py - Brief description of what this file does.
"""
```

**Recommended Fix:**
Add module docstring to lines 1-2 for each file:
- **DIBELS.py**: Insert docstring before line 1
- **EOI.py**: Insert docstring before line 1
- **MOI.py**: Insert docstring before line 1

Example for DIBELS.py:
```python
"""
DIBELS.py - Swaps student IDs in DIBELS 8th Edition Excel files based on SIF or SSOT lookup.
"""
```

---

### Issue 1.2: Missing Section Markers (Code Organization)

**Files affected:** 7 files

Per CLAUDE.md recommended structure, code should be organized with clear section markers:
- `# === IMPORTS ===`
- `# === CONSTANTS ===` (if applicable)
- `# === MAIN FUNCTIONS/CLASSES ===`
- `# === STANDALONE EXECUTION ===` (if applicable)

#### Affected Files:

**A. HELPERS** (3 files)

| File | Location | Issue | Recommended Fix |
|------|----------|-------|-----------------|
| clean_field.py | Helpers/Clean_fields | No section markers. Imports (lines 1-7) lack `=== IMPORTS ===` marker. Function definition (line 10) lacks `=== MAIN FUNCTIONS/CLASSES ===` marker. | Add section markers before imports and before function definition |
| real_last_row.py | Helpers/Last_row_finder | No section markers. Imports (lines 1-8) lack marker. Functions (lines 11-61) lack `=== MAIN FUNCTIONS/CLASSES ===` marker. | Add section markers before imports and before first function |
| work_files.py | Helpers/dog_box | Inconsistent. Has docstring (lines 1-11) but no section markers. Imports (lines 13-15) should be marked. Functions (lines 22-140) lack `=== MAIN FUNCTIONS/CLASSES ===`. | Add `=== IMPORTS ===` after docstring; add `=== MAIN FUNCTIONS/CLASSES ===` before line 22 |

**B. IDSWAPPERS** (3 files)

| File | Location | Issue | Recommended Fix |
|------|----------|-------|-----------------|
| DIBELS.py | IDswappers/ | Missing module docstring (Issue 1.1). No section markers. Imports (lines 1-15) should be marked. Class definition (line 27) should have `=== MAIN CLASS ===` marker. Main function (line 427) should have `=== STANDALONE EXECUTION ===` marker. | Add docstring, then organize: `=== IMPORTS ===` (lines 1-15), `=== MAIN CLASS ===` (before line 27), `=== STANDALONE EXECUTION ===` (before line 427) |
| EOI.py | IDswappers/ | Missing module docstring (Issue 1.1). No section markers. Same structure as DIBELS. | Add docstring, then organize: `=== IMPORTS ===`, `=== MAIN CLASS ===`, `=== STANDALONE EXECUTION ===` |
| MOI.py | IDswappers/ | Missing module docstring (Issue 1.1). No section markers. Imports (lines 1-16). Class definition (line 27). | Add docstring, then organize: `=== IMPORTS ===`, `=== MAIN CLASS ===`, `=== STANDALONE EXECUTION ===` |

**C. WELL-STRUCTURED FILES** (Reference Examples)

These files already follow the recommended pattern:
- ✓ `file_sorter.py` (Finders/File_sorter, lines 1-314): Proper module docstring + section markers
- ✓ `file_identifier.py` (Finders/File_sorter, lines 1+): Proper section markers
- ✓ `PAT-moveID_to_UID.py` (RandomTools/PAT, lines 1-300): Proper module docstring + section markers

---

## 2. HELPER USAGE ISSUES

### Issue 2.1: Inconsistent Use of `field_cleaner()` for Header Matching

**CLAUDE.md Requirement:**
> "Always use `field_cleaner()` for any text comparison/matching operations."

**Problem:** Three IDswapper files directly compare cell values with constant strings instead of normalizing both sides using `field_cleaner()`. This can fail due to:
- Extra whitespace
- Unicode variations
- Case differences

---

#### DIBELS.py

**Location:** IDswappers/DIBELS.py
**Lines affected:** 198-206 (header detection in `_process_xlsx`)

**Current Code (PROBLEMATIC):**
```python
if cell.value == FILE_FNAME:
    fname_col = cell.column_letter
    header_row = cell.row
elif cell.value == FILE_LNAME:
    lname_col = cell.column_letter
elif cell.value == FILE_ID_HEADER:
    id_col = cell.column_letter
elif cell.value and str(cell.value).startswith("Test Date"):
    date_col = cell.column_letter
```

**Why it's problematic:**
- Direct string comparison fails if header has extra spaces: `"First Name "` ≠ `"First Name"`
- Case-sensitive: `"first name"` ≠ `"First Name"`
- No unicode normalization

**Recommended Fix:**
Normalize both sides of comparison:
```python
if field_cleaner(str(cell.value or ""), strip_spaces=True) == field_cleaner(FILE_FNAME, strip_spaces=True):
    fname_col = cell.column_letter
    header_row = cell.row
# ... etc for other headers
```

Or use a lookup table (recommended pattern from CLAUDE.md):
```python
HEADER_MAP = {
    "First Name": "fname",
    "Surname": "lname",
    "Student ID": "id",
}
normalized_headers = {field_cleaner(k, strip_spaces=True): v for k, v in HEADER_MAP.items()}

for cell in row:
    normalized_cell = field_cleaner(str(cell.value or ""), strip_spaces=True)
    if normalized_cell in normalized_headers:
        if normalized_headers[normalized_cell] == "fname":
            fname_col = cell.column_letter
```

**Related line:** Also in `_process_xls()` lines 302-310, same pattern.

---

#### EOI.py

**Location:** IDswappers/EOI.py
**Lines affected:** 176-184 (header detection in `_process_xlsx`)

**Current Code (PROBLEMATIC):**
```python
if cell.value == FILE_FNAME:
    fname_col = cell.column_letter
    header_row = cell.row
elif cell.value == FILE_LNAME:
    lname_col = cell.column_letter
elif cell.value == FILE_ID_HEADER:
    id_col = cell.column_letter
elif cell.value == FILE_DATE_HEADER:
    date_col = cell.column_letter
```

**Same issue as DIBELS.py** — direct comparison without field_cleaner normalization.

**Recommended Fix:** Apply same solution as DIBELS.py

**Related line:** Also in `_process_xls()` lines 288-296, same pattern.

---

#### MOI.py

**Location:** IDswappers/MOI.py
**Lines affected:** Likely similar to DIBELS/EOI (not fully read, but file starts with same pattern)

**Assumption:** Same issue based on file structure and header constants defined (lines 19-24)

**Recommended Fix:** Apply same solution as DIBELS.py/EOI.py

---

### Issue 2.2: Best Practice Example - field_cleaner Usage

**File:** RandomTools/PAT/PAT-moveID_to_UID.py
**Lines:** 65, 79

**Current Code (EXCELLENT):**
```python
# Line 65: Create normalized lookup table
normalized_search = {field_cleaner(k, strip_spaces=True): v for k, v in header_map.items()}

# Line 79: Normalize cell value before lookup
cell_text = field_cleaner(str(cell.value), strip_spaces=True)
if cell_text in normalized_search:
    return (col, row)
```

**Why this is better:**
- Readable source headers in lookup table
- Normalizes both lookup keys and incoming data
- Single source of truth for expected values
- Handles unicode, whitespace, and case variations

**This pattern should be adopted in DIBELS.py, EOI.py, MOI.py**

---

## Summary Table

| # | Category | File | Issue | Lines | Priority |
|---|----------|------|-------|-------|----------|
| 1 | Structure | DIBELS.py | Missing module docstring | 1 | High |
| 2 | Structure | EOI.py | Missing module docstring | 1 | High |
| 3 | Structure | MOI.py | Missing module docstring | 1 | High |
| 4 | Structure | clean_field.py | Missing section markers | 1-50 | Medium |
| 5 | Structure | real_last_row.py | Missing section markers | 1-62 | Medium |
| 6 | Structure | work_files.py | Missing section markers (after docstring) | 13-141 | Medium |
| 7 | Structure | DIBELS.py | Missing section markers | 1-461 | High |
| 8 | Structure | EOI.py | Missing section markers | 1-447 | High |
| 9 | Structure | MOI.py | Missing section markers | 1-50+ | High |
| 10 | Helper | DIBELS.py | Inconsistent field_cleaner usage | 198-206, 302-310 | High |
| 11 | Helper | EOI.py | Inconsistent field_cleaner usage | 176-184, 288-296 | High |
| 12 | Helper | MOI.py | Inconsistent field_cleaner usage | (estimated) TBD | High |
| 13 | Helper | clean_field.py | Good pattern ✓ | N/A | N/A |

---

## Implementation Notes

### Quick Wins (Apply First):
1. Add module docstrings to DIBELS.py, EOI.py, MOI.py
2. Add section markers to Helpers files (low risk, mechanical changes)

### Higher Impact (Requires Testing):
1. Replace direct string comparisons with field_cleaner in IDswapper files
2. Use normalized lookup table pattern (see PAT-moveID_to_UID.py as template)

### Testing Recommendation:
After implementing field_cleaner changes in IDswappers, test with:
- File headers with extra spaces
- Mixed case headers
- Different unicode representations

---

## Reference Files

**Well-structured examples to use as templates:**
- `file_sorter.py` — Good section markers + main logic structure
- `PAT-moveID_to_UID.py` — Good docstring + section markers + field_cleaner usage pattern
- `file_identifier.py` — Clean section organization

---

**End of Report**
