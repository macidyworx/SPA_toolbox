"""
cell_utils.py - Utilities for parsing Excel-style cell references.
"""

# === IMPORTS ===
import re


# === CONSTANTS ===
_CELL_RE = re.compile(r"^([A-Za-z]{1,3})(\d+)$")


# === FUNCTIONS ===
def parse_cell_ref(cell_ref):
    """Parse an Excel-style cell reference into a (row, col) tuple.

    Both row and col are 1-indexed to match openpyxl conventions.

    Args:
        cell_ref: String like "A1", "B2", "AA10", "c3".

    Returns:
        Tuple of (row, col) as 1-indexed integers.

    Raises:
        ValueError: If cell_ref is not a valid cell reference.
    """
    if not isinstance(cell_ref, str):
        raise ValueError(f"Cell reference must be a string, got {type(cell_ref).__name__}")

    match = _CELL_RE.match(cell_ref.strip())
    if not match:
        raise ValueError(f"Invalid cell reference: '{cell_ref}'")

    col_str = match.group(1).upper()
    row = int(match.group(2))

    if row < 1:
        raise ValueError(f"Row must be >= 1, got {row} in '{cell_ref}'")

    col = _col_letters_to_number(col_str)
    return (row, col)


def _col_letters_to_number(letters):
    """Convert column letters to a 1-indexed number.

    A=1, B=2, ..., Z=26, AA=27, AB=28, ...
    """
    result = 0
    for char in letters:
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result
