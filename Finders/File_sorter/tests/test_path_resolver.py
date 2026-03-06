"""
Tests for path_resolver.py
"""

import os
import pytest

from Finders.File_sorter.path_resolver import resolve_sort_path


# === HELPERS ===

def _cfg(**kwargs):
    """Build a minimal test config with overrides."""
    base = {
        "priority": 1,
        "folder": "DefaultFolder",
        "group": "TestGroup",
        "area": "TestArea",
        "variant": "online",
        "sort_strategy": "{folder}",
    }
    base.update(kwargs)
    return base


# === TESTS ===

class TestResolveSortPath:
    """Tests for resolve_sort_path function."""

    def test_default_folder_strategy(self):
        """Default {folder} strategy uses the folder field."""
        cfg = _cfg()
        result = resolve_sort_path("MyTest", cfg, "/output")
        assert result == os.path.join("/output", "DefaultFolder")

    def test_type_variable(self):
        """The {type} variable uses the test_name."""
        cfg = _cfg(sort_strategy="{type}")
        result = resolve_sort_path("PAT-R ONLINE", cfg, "/output")
        assert result == os.path.join("/output", "PAT-R ONLINE")

    def test_group_variable(self):
        cfg = _cfg(sort_strategy="{group}")
        result = resolve_sort_path("Test", cfg, "/output")
        assert result == os.path.join("/output", "TestGroup")

    def test_variant_variable(self):
        cfg = _cfg(sort_strategy="{variant}")
        result = resolve_sort_path("Test", cfg, "/output")
        assert result == os.path.join("/output", "online")

    def test_area_variable(self):
        cfg = _cfg(sort_strategy="{area}")
        result = resolve_sort_path("Test", cfg, "/output")
        assert result == os.path.join("/output", "TestArea")

    def test_compound_strategy(self):
        """Multiple variables in a path template."""
        cfg = _cfg(sort_strategy="{group}/{variant}")
        result = resolve_sort_path("Test", cfg, "/output")
        assert result == os.path.join("/output", "TestGroup", "online")

    def test_three_level_strategy(self):
        cfg = _cfg(sort_strategy="{group}/{area}/{type}")
        result = resolve_sort_path("PAT-R", cfg, "/output")
        assert result == os.path.join("/output", "TestGroup", "TestArea", "PAT-R")

    def test_empty_variant_filtered(self):
        """Empty variant in compound path doesn't create empty segments."""
        cfg = _cfg(variant="", sort_strategy="{group}/{variant}")
        result = resolve_sort_path("Test", cfg, "/output")
        assert result == os.path.join("/output", "TestGroup")

    def test_empty_strategy_falls_back_to_folder(self):
        """Empty resolved strategy falls back to folder name."""
        cfg = _cfg(variant="", sort_strategy="{variant}")
        result = resolve_sort_path("Test", cfg, "/output")
        assert result == os.path.join("/output", "DefaultFolder")

    def test_missing_sort_strategy_uses_folder(self):
        """Config without sort_strategy defaults to {folder}."""
        cfg = _cfg()
        del cfg["sort_strategy"]
        result = resolve_sort_path("Test", cfg, "/output")
        assert result == os.path.join("/output", "DefaultFolder")

    def test_invalid_variable_raises(self):
        """Invalid template variable raises ValueError."""
        cfg = _cfg(sort_strategy="{bogus}")
        with pytest.raises(ValueError, match="Invalid template variable"):
            resolve_sort_path("Test", cfg, "/output")

    def test_parent_traversal_raises(self):
        """Path with '..' raises ValueError."""
        cfg = _cfg(sort_strategy="../escape")
        with pytest.raises(ValueError, match="Unsafe path"):
            resolve_sort_path("Test", cfg, "/output")

    def test_static_string_strategy(self):
        """Plain string with no variables works."""
        cfg = _cfg(sort_strategy="StaticFolder")
        result = resolve_sort_path("Test", cfg, "/output")
        assert result == os.path.join("/output", "StaticFolder")
