"""
file_identifier.py - Identifies file types based on YAML-configured matching rules.
"""

# === IMPORTS ===
import os

from Helpers.Clean_fields.clean_field import field_cleaner
from Finders.File_sorter.readers import READERS


# === CONSTANTS ===
SUPPORTED_EXTENSIONS = {".xlsx", ".xlsm", ".xls", ".csv"}
_FORMAT_FROM_EXT = {
    ".xlsx": "xlsx",
    ".xlsm": "xlsm",
    ".xls": "xls",
    ".csv": "csv",
}


# === MAIN FUNCTION ===
def identify_file(filepath, test_configs, max_scan_rows=20, max_scan_cols=30):
    """Identify a file's test type by matching against configured rules.

    Args:
        filepath: Path to the file to identify.
        test_configs: List of (name, config) tuples sorted by priority,
            as returned by config_loader.load_test_configs().
        max_scan_rows: Max rows to scan for FIND_KEYS.
        max_scan_cols: Max columns to scan for FIND_KEYS.

    Returns:
        Tuple of (test_type_name, config_dict) if matched, or (None, None).
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return (None, None)

    fmt = _FORMAT_FROM_EXT[ext]
    reader_cls = READERS.get(ext)
    if reader_cls is None:
        return (None, None)

    reader = reader_cls()

    for name, config in test_configs:
        fmt_config = config.get(fmt)
        if fmt_config is None:
            continue

        if _check_keys(reader, filepath, fmt_config.get("KEYS")):
            return (name, config)

        if _check_find_keys(
            reader, filepath, fmt_config.get("FIND_KEYS"),
            max_scan_rows, max_scan_cols,
        ):
            return (name, config)

    return (None, None)


# === MATCHING LOGIC ===
def _check_keys(reader, filepath, keys_list):
    """Check KEYS rules — specific cell value matches.

    All entries in keys_list must match for the rule to pass.
    """
    if not keys_list:
        return False

    for entry in keys_list:
        cell_ref = entry.get("cell")
        sheet = entry.get("sheet", 0)

        if cell_ref is None:
            return False

        try:
            cell_value = reader.read_cell(filepath, sheet, cell_ref)
        except Exception:
            return False

        if not _match_entry(cell_value, entry):
            return False

    return True


def _check_find_keys(reader, filepath, find_keys_list, max_rows, max_cols):
    """Check FIND_KEYS rules — search area for matching values.

    All entries in find_keys_list must match for the rule to pass.
    Each entry looks for its startswith value anywhere in the scanned area.
    """
    if not find_keys_list:
        return False

    scanned_cache = {}

    for entry in find_keys_list:
        sheet = entry.get("sheet", 0)
        target = entry.get("startswith")
        if target is None:
            return False

        normalized_target = field_cleaner(str(target), strip_spaces=True)
        if not normalized_target:
            return False

        cache_key = (filepath, sheet)
        if cache_key not in scanned_cache:
            try:
                scanned_cache[cache_key] = reader.scan_area(
                    filepath, sheet, max_rows, max_cols
                )
            except Exception:
                return False

        area_values = scanned_cache[cache_key]
        found = any(v.startswith(normalized_target) for v in area_values)
        if not found:
            return False

    return True


def _match_entry(cell_value, entry):
    """Check if a cell value matches a single KEYS entry."""
    if "startswith" in entry:
        target = field_cleaner(str(entry["startswith"]), strip_spaces=True)
        return cell_value.startswith(target)

    if "contains" in entry:
        fragments = entry["contains"]
        for fragment in fragments:
            target = field_cleaner(str(fragment), strip_spaces=True)
            if target not in cell_value:
                return False
        return True

    return False
