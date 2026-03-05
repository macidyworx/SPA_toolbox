# Clean_fields Module Overview

The `Clean_fields` module provides text normalization for consistent and reliable comparison of names, IDs, and other text fields across datasets. It is applied to both sides of a comparison at match time without modifying the original data.

## Contents

- **clean_field.py**: Core normalization utility.
  - Main function: `field_cleaner`
    - Normalizes Unicode (NFKC by default, handles fullwidth forms, circled digits, etc.)
    - Replaces all Unicode whitespace with ASCII space
    - Collapses multiple spaces (or removes all spaces with `strip_spaces=True`)
    - Optionally lowercases text
    - Strips leading/trailing whitespace
    - Removes BOM (Byte Order Mark) if present
    - Replaces em dash and en dash with hyphen (-), ß with ss

- **test_clean_fields.py**: pytest suite covering normalization scenarios and the `strip_spaces` option for name/ID matching.

## Usage

```python
from Helpers.Clean_fields.clean_field import field_cleaner

# Default: lowercase + strip spaces (ideal for name/ID matching)
field_cleaner("  Hello   World  ")  # -> "helloworld"
field_cleaner("Van Owen")           # -> "vanowen"
field_cleaner("ABC0001")            # -> "abc0001"

# Preserve spaces when needed
field_cleaner("  Hello   World  ", strip_spaces=False)  # -> "hello world"
```

## Options

| Parameter | Default | Description |
|---|---|---|
| `lowercase` | `True` | Convert text to lowercase |
| `collapse_whitespace` | `True` | Collapse multiple spaces into one (ignored when `strip_spaces=True`) |
| `strip_spaces` | `True` | Remove all spaces — useful for matching names like "Van Owen" vs "Vanowen" |
| `strip_bom` | `True` | Remove BOM (Byte Order Mark) characters |
| `unicode_form` | `'NFKC'` | Unicode normalization form (e.g. `'NFKC'`, `'NFC'`) |

## Testing

```sh
pytest Helpers/Clean_fields/test_clean_fields.py
```

## Extensibility

The normalization logic can be extended to handle additional Unicode or formatting cases as needed.
Designed to be used by other modules for consistent text comparison.
