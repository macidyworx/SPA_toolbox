# Clean_fields Module Overview

The `Clean_fields` module provides robust text normalization utilities for consistent and reliable cell/text comparison across datasets. It is designed to be used as a helper for other tools in the SPA Toolbox, ensuring that text data is compared in a uniform way regardless of formatting, encoding, or Unicode variations.

## Contents

- **clean_field.py**: Core normalization utility.
  - Main function: `field_cleaner`.
    - Normalizes Unicode (NFKC by default).
    - Replaces all Unicode whitespace with ASCII space.
    - Collapses multiple spaces.
    - Optionally lowercases text.
    - Strips leading/trailing whitespace.
    - Removes BOM (Byte Order Mark) if present.
    - Replaces em dash (—) with hyphen (-), ß with ss, and normalizes Roman numerals and fullwidth forms.
  - Returns a cleaned string suitable for reliable comparison in data processing.

- **test_clean_fields.py**: Comprehensive pytest suite for the cleaning function.
  - Tests a wide range of normalization scenarios: whitespace, Unicode, BOM, dashes, accents, lowercasing, and more.
  - Ensures the cleaning function is robust and reliable for various input types.

## How It Works

- The `field_cleaner` function is called with a text value and optional parameters for lowercasing, whitespace collapsing, BOM stripping, and Unicode normalization form.
- The function returns a normalized string, making it suitable for robust comparison in data processing, file identification, and other tools.

## Usage

- **As a module:**
  ```python
  from tool_box.Clean_fields.clean_field import field_cleaner
  cleaned = field_cleaner("Some Text")
  ```
- **Testing:**
  Run the tests with pytest to ensure normalization is working as expected:
  ```sh
  pytest test_clean_fields.py
  ```

## Extensibility

- The normalization logic can be extended to handle additional Unicode or formatting cases as needed.
- Designed to be used by other modules (such as File_IDer2) for consistent text processing.


## Relationships

- Used by the following files for robust and consistent text comparison:
  - `tool_box/File_IDer2/File_Identifier.py`
  - `tool_box/File_IDer2/test_Manager/add_test.py`
  - `tool_box/File_IDer2/test_Manager/edit_test.py`
  - `tool_box/Clean_fields/test_clean_fields.py`

---
This module is essential for preparing and comparing text data in a reliable, repeatable way in the SPA Toolbox.
