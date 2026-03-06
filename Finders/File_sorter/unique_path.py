"""
unique_path.py - Generate unique file paths to avoid overwrites.
"""

# === IMPORTS ===
import os


# === FUNCTIONS ===
def get_unique_path(filepath):
    """Return a unique path by appending _1, _2, etc. if file already exists.

    Args:
        filepath: The desired file path.

    Returns:
        The original path if it doesn't exist, otherwise a suffixed version.
    """
    if not os.path.exists(filepath):
        return filepath

    base, ext = os.path.splitext(filepath)
    counter = 1

    while True:
        candidate = f"{base}_{counter}{ext}"
        if not os.path.exists(candidate):
            return candidate
        counter += 1
