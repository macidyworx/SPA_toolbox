"""
path_resolver.py - Resolves output directory paths using sort_strategy templates.
"""

# === IMPORTS ===
import os
import re


# === CONSTANTS ===
VALID_TEMPLATE_VARS = {"type", "group", "variant", "area", "folder"}
_VAR_RE = re.compile(r"\{(\w+)\}")


# === FUNCTIONS ===
def resolve_sort_path(test_name, test_config, base_output_dir):
    """Resolve the output directory path for a matched test type.

    Uses the sort_strategy template from the test config to build the path.
    Falls back to {folder} if sort_strategy is not specified.

    Args:
        test_name: The matched test type name.
        test_config: The config dict for the matched test type.
        base_output_dir: Root output directory (e.g. "SORTED/").

    Returns:
        Absolute path to the output directory for this test type.

    Raises:
        ValueError: If template contains invalid variables or resolves
            to an unsafe path.
    """
    strategy = test_config.get("sort_strategy", "{folder}")

    values = {
        "type": test_name,
        "group": test_config.get("group", ""),
        "variant": test_config.get("variant", ""),
        "area": test_config.get("area", ""),
        "folder": test_config.get("folder", test_name),
    }

    def _replace(match):
        var = match.group(1)
        if var not in VALID_TEMPLATE_VARS:
            raise ValueError(
                f"Invalid template variable '{{{var}}}' in sort_strategy"
            )
        return values[var]

    resolved = _VAR_RE.sub(_replace, strategy)

    # Filter out empty path segments
    parts = [p for p in resolved.replace("\\", "/").split("/") if p.strip()]

    # Safety: no parent traversal
    for part in parts:
        if part == "..":
            raise ValueError(
                f"Unsafe path component '..' in resolved strategy: {resolved}"
            )

    if not parts:
        parts = [test_config.get("folder", test_name)]

    return os.path.join(base_output_dir, *parts)
