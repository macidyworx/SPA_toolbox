"""
Tests for file_cache.py
"""

import os
import pytest

from Finders.File_sorter.file_cache import FileCache


# === HELPERS ===

def _make_file(tmp_path, name, content="test"):
    """Create a file with given content and return its path."""
    path = tmp_path / name
    path.write_text(content)
    return str(path)


# === TESTS ===

class TestFileCache:
    """Tests for the FileCache class."""

    def test_miss_returns_none(self, tmp_path):
        """Cache miss returns None."""
        cache = FileCache()
        path = _make_file(tmp_path, "a.xlsx")
        assert cache.get_cached_type(path) is None

    def test_set_and_get(self, tmp_path):
        """Can store and retrieve a cached type."""
        cache = FileCache()
        path = _make_file(tmp_path, "a.xlsx")
        cache.set_cached_type(path, "PAT-R")
        assert cache.get_cached_type(path) == "PAT-R"

    def test_different_files(self, tmp_path):
        """Different files get different cache entries."""
        cache = FileCache()
        a = _make_file(tmp_path, "a.xlsx", "aaa")
        b = _make_file(tmp_path, "b.xlsx", "bbb")
        cache.set_cached_type(a, "PAT-R")
        cache.set_cached_type(b, "SSSR")
        assert cache.get_cached_type(a) == "PAT-R"
        assert cache.get_cached_type(b) == "SSSR"

    def test_modified_file_invalidates(self, tmp_path):
        """Cache miss if file content changes."""
        cache = FileCache()
        path = _make_file(tmp_path, "a.xlsx", "original")
        cache.set_cached_type(path, "PAT-R")

        # Modify the file content (changes hash)
        with open(path, "w") as f:
            f.write("modified")

        assert cache.get_cached_type(path) is None

    def test_nonexistent_file(self):
        """Non-existent file returns None, doesn't error."""
        cache = FileCache()
        assert cache.get_cached_type("/nonexistent/file.xlsx") is None

    def test_set_nonexistent_file(self):
        """Setting cache for non-existent file is a no-op."""
        cache = FileCache()
        cache.set_cached_type("/nonexistent/file.xlsx", "PAT")
        assert cache.size == 0

    def test_bounded_size(self, tmp_path):
        """Cache evicts oldest entries when max_size is exceeded."""
        cache = FileCache(max_size=3)
        paths = []
        for i in range(5):
            p = _make_file(tmp_path, f"f{i}.xlsx", f"content{i}")
            paths.append(p)
            cache.set_cached_type(p, f"Type{i}")

        assert cache.size == 3
        # Oldest entries (0, 1) should be evicted
        assert cache.get_cached_type(paths[0]) is None
        assert cache.get_cached_type(paths[1]) is None
        # Newest entries should remain
        assert cache.get_cached_type(paths[4]) == "Type4"

    def test_clear(self, tmp_path):
        """Clear empties the cache."""
        cache = FileCache()
        path = _make_file(tmp_path, "a.xlsx")
        cache.set_cached_type(path, "PAT")
        cache.clear()
        assert cache.size == 0
        assert cache.get_cached_type(path) is None

    def test_size_property(self, tmp_path):
        """Size tracks number of entries."""
        cache = FileCache()
        assert cache.size == 0
        path = _make_file(tmp_path, "a.xlsx")
        cache.set_cached_type(path, "PAT")
        assert cache.size == 1

    def test_lru_eviction_order(self, tmp_path):
        """Recently accessed entries survive eviction."""
        cache = FileCache(max_size=3)
        p0 = _make_file(tmp_path, "f0.xlsx", "c0")
        p1 = _make_file(tmp_path, "f1.xlsx", "c1")
        p2 = _make_file(tmp_path, "f2.xlsx", "c2")

        cache.set_cached_type(p0, "T0")
        cache.set_cached_type(p1, "T1")
        cache.set_cached_type(p2, "T2")

        # Access p0 to make it recently used
        cache.get_cached_type(p0)

        # Add new entry, should evict p1 (least recently used)
        p3 = _make_file(tmp_path, "f3.xlsx", "c3")
        cache.set_cached_type(p3, "T3")

        assert cache.get_cached_type(p0) == "T0"  # survived (recently accessed)
        assert cache.get_cached_type(p1) is None   # evicted
        assert cache.get_cached_type(p2) is not None
        assert cache.get_cached_type(p3) == "T3"
