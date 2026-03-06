"""
file_cache.py - Hash + mtime cache for file identification results.
"""

# === IMPORTS ===
import hashlib
import os
from collections import OrderedDict


# === CONSTANTS ===
DEFAULT_MAX_SIZE = 1000
_HASH_CHUNK_SIZE = 65536


# === CLASS ===
class FileCache:
    """Cache file identification results keyed on content hash + mtime.

    Uses an LRU-style bounded OrderedDict to limit memory usage.
    """

    def __init__(self, max_size=DEFAULT_MAX_SIZE):
        self._cache = OrderedDict()
        self._max_size = max_size

    def get_cached_type(self, filepath):
        """Look up cached test type for a file.

        Args:
            filepath: Path to the file.

        Returns:
            Cached test type name (str) if found and still valid, else None.
        """
        key = self._make_key(filepath)
        if key is None:
            return None

        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        return None

    def set_cached_type(self, filepath, test_type):
        """Store a file identification result in the cache.

        Args:
            filepath: Path to the file.
            test_type: The identified test type name.
        """
        key = self._make_key(filepath)
        if key is None:
            return

        self._cache[key] = test_type
        self._cache.move_to_end(key)

        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()

    @property
    def size(self):
        """Number of entries in the cache."""
        return len(self._cache)

    @staticmethod
    def _make_key(filepath):
        """Create a cache key from file path, mtime, and content hash."""
        try:
            stat = os.stat(filepath)
            mtime = stat.st_mtime
            file_hash = _compute_hash(filepath)
            return (filepath, mtime, file_hash)
        except OSError:
            return None


def _compute_hash(filepath):
    """Compute MD5 hash of a file's contents."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(_HASH_CHUNK_SIZE)
            if not chunk:
                break
            md5.update(chunk)
    return md5.hexdigest()
