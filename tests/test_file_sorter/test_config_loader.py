"""
Tests for config_loader.py
"""

import os
import pytest
import yaml

from Finders.File_sorter.config_loader import (
    load_test_configs,
    _validate_test_type,
    _validate_template,
    FORMAT_KEYS,
)


# === FIXTURES ===

MINIMAL_VALID = {
    "priority": 1,
    "folder": "TestFolder",
    "group": "",
    "area": "",
    "variant": "",
    "sort_strategy": "{folder}",
    "xlsx": {
        "KEYS": [{"sheet": 0, "cell": "A1", "startswith": "test"}]
    },
}


def _write_yaml(tmp_path, data):
    """Helper to write a YAML file and return its path."""
    path = tmp_path / "test_identifiers.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
    return str(path)


# === TESTS: load_test_configs ===

class TestLoadTestConfigs:
    """Tests for the main load_test_configs function."""

    def test_loads_bundled_yaml(self):
        """Bundled test_identifiers.yaml loads without errors."""
        configs = load_test_configs()
        assert len(configs) == 45

    def test_sorted_by_priority(self):
        """Results are sorted by priority ascending."""
        configs = load_test_configs()
        priorities = [cfg["priority"] for _, cfg in configs]
        assert priorities == sorted(priorities)

    def test_first_entry_is_priority_1(self):
        """First entry has priority 1."""
        configs = load_test_configs()
        name, cfg = configs[0]
        assert cfg["priority"] == 1

    def test_last_entry_is_priority_45(self):
        """Last entry has priority 45."""
        configs = load_test_configs()
        name, cfg = configs[-1]
        assert cfg["priority"] == 45

    def test_all_have_required_fields(self):
        """Every test type has priority and folder."""
        configs = load_test_configs()
        for name, cfg in configs:
            assert "priority" in cfg, f"{name} missing priority"
            assert "folder" in cfg, f"{name} missing folder"

    def test_all_have_at_least_one_format(self):
        """Every test type has at least one format key."""
        configs = load_test_configs()
        for name, cfg in configs:
            has_fmt = any(k in cfg for k in FORMAT_KEYS)
            assert has_fmt, f"{name} has no format keys"

    def test_all_have_sort_strategy(self):
        """Every test type has variant and sort_strategy fields."""
        configs = load_test_configs()
        for name, cfg in configs:
            assert "variant" in cfg, f"{name} missing variant"
            assert "sort_strategy" in cfg, f"{name} missing sort_strategy"

    def test_no_list_cell_refs_remain(self):
        """No cell values should be lists (all converted to A1 strings)."""
        configs = load_test_configs()
        for name, cfg in configs:
            for fmt in FORMAT_KEYS:
                if fmt not in cfg or not isinstance(cfg[fmt], dict):
                    continue
                for key_type in ("KEYS", "FIND_KEYS"):
                    if key_type not in cfg[fmt]:
                        continue
                    for entry in cfg[fmt][key_type]:
                        if "cell" in entry:
                            assert not isinstance(entry["cell"], list), (
                                f"{name} -> {fmt} -> {key_type}: "
                                f"cell is still a list: {entry['cell']}"
                            )

    def test_no_row_col_keys_remain(self):
        """No csv entries should have row/col keys (all converted to cell)."""
        configs = load_test_configs()
        for name, cfg in configs:
            if "csv" not in cfg or not isinstance(cfg["csv"], dict):
                continue
            for key_type in ("KEYS", "FIND_KEYS"):
                if key_type not in cfg["csv"]:
                    continue
                for entry in cfg["csv"][key_type]:
                    assert "row" not in entry, (
                        f"{name} -> csv -> {key_type}: still has 'row' key"
                    )
                    assert "col" not in entry, (
                        f"{name} -> csv -> {key_type}: still has 'col' key"
                    )

    def test_custom_yaml_path(self, tmp_path):
        """Can load from a custom YAML path."""
        data = {"MyTest": MINIMAL_VALID}
        path = _write_yaml(tmp_path, data)
        configs = load_test_configs(yaml_path=path)
        assert len(configs) == 1
        assert configs[0][0] == "MyTest"

    def test_file_not_found(self):
        """Raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_test_configs(yaml_path="/nonexistent/path.yaml")

    def test_invalid_yaml_top_level(self, tmp_path):
        """Raises ValueError if YAML top level is not a dict."""
        path = tmp_path / "bad.yaml"
        path.write_text("- item1\n- item2\n")
        with pytest.raises(ValueError, match="top-level"):
            load_test_configs(yaml_path=str(path))

    def test_skip_validation(self, tmp_path):
        """Can skip validation with validate=False."""
        data = {"Bad": {"priority": 1}}  # missing folder and format
        path = _write_yaml(tmp_path, data)
        configs = load_test_configs(yaml_path=path, validate=False)
        assert len(configs) == 1


# === TESTS: _validate_test_type ===

class TestValidateTestType:
    """Tests for individual test type validation."""

    def test_valid_minimal(self):
        """Minimal valid config passes validation."""
        _validate_test_type("Test", MINIMAL_VALID)

    def test_missing_priority(self):
        """Raises ValueError when priority is missing."""
        cfg = {**MINIMAL_VALID}
        del cfg["priority"]
        with pytest.raises(ValueError, match="missing required"):
            _validate_test_type("Test", cfg)

    def test_missing_folder(self):
        """Raises ValueError when folder is missing."""
        cfg = {**MINIMAL_VALID}
        del cfg["folder"]
        with pytest.raises(ValueError, match="missing required"):
            _validate_test_type("Test", cfg)

    def test_priority_not_int(self):
        """Raises ValueError when priority is not an integer."""
        cfg = {**MINIMAL_VALID, "priority": "high"}
        with pytest.raises(ValueError, match="priority must be an integer"):
            _validate_test_type("Test", cfg)

    def test_no_format_keys(self):
        """Raises ValueError when no format keys present."""
        cfg = {"priority": 1, "folder": "X"}
        with pytest.raises(ValueError, match="at least one format"):
            _validate_test_type("Test", cfg)

    def test_format_not_dict(self):
        """Raises ValueError when format value is not a dict."""
        cfg = {**MINIMAL_VALID, "xlsx": "bad"}
        with pytest.raises(ValueError, match="expected dict"):
            _validate_test_type("Test", cfg)

    def test_format_missing_keys_or_find_keys(self):
        """Raises ValueError when format has no KEYS or FIND_KEYS."""
        cfg = {**MINIMAL_VALID, "xlsx": {"OTHER": []}}
        with pytest.raises(ValueError, match="KEYS or FIND_KEYS"):
            _validate_test_type("Test", cfg)

    def test_keys_entry_not_dict(self):
        """Raises ValueError when KEYS entry is not a dict."""
        cfg = {**MINIMAL_VALID, "xlsx": {"KEYS": ["bad"]}}
        with pytest.raises(ValueError, match="expected dict"):
            _validate_test_type("Test", cfg)

    def test_keys_missing_cell(self):
        """Raises ValueError when KEYS entry has no cell field."""
        cfg = {
            **MINIMAL_VALID,
            "xlsx": {"KEYS": [{"sheet": 0, "startswith": "x"}]},
        }
        with pytest.raises(ValueError, match="missing 'cell'"):
            _validate_test_type("Test", cfg)

    def test_keys_cell_is_list(self):
        """Raises ValueError when cell is still a list (not converted)."""
        cfg = {
            **MINIMAL_VALID,
            "xlsx": {
                "KEYS": [{"sheet": 0, "cell": [0, 0], "startswith": "x"}]
            },
        }
        with pytest.raises(ValueError, match="A1 notation"):
            _validate_test_type("Test", cfg)

    def test_keys_missing_match_type(self):
        """Raises ValueError when entry has no startswith/contains/tag."""
        cfg = {
            **MINIMAL_VALID,
            "xlsx": {"KEYS": [{"sheet": 0, "cell": "A1"}]},
        }
        with pytest.raises(ValueError, match="missing match type"):
            _validate_test_type("Test", cfg)

    def test_xml_tag_valid(self):
        """XML entries with tag match type are valid."""
        cfg = {
            **MINIMAL_VALID,
            "xml": {"KEYS": [{"tag": "CASES21_message"}]},
        }
        _validate_test_type("Test", cfg)

    def test_contains_valid(self):
        """KEYS entry with contains match type is valid."""
        cfg = {
            **MINIMAL_VALID,
            "xlsx": {
                "KEYS": [
                    {"sheet": 0, "cell": "B2", "contains": ["a", "b"]}
                ]
            },
        }
        _validate_test_type("Test", cfg)

    def test_find_keys_valid(self):
        """FIND_KEYS entries are valid without cell field."""
        cfg = {
            **MINIMAL_VALID,
            "xlsx": {
                "FIND_KEYS": [{"sheet": 0, "startswith": "find this"}]
            },
        }
        _validate_test_type("Test", cfg)


# === TESTS: _validate_template ===

class TestValidateTemplate:
    """Tests for sort_strategy template validation."""

    def test_valid_folder_template(self):
        """Default {folder} template is valid."""
        _validate_template("{folder}", "Test")

    def test_valid_compound_template(self):
        """Compound template with multiple vars is valid."""
        _validate_template("{group}/{variant}", "Test")

    def test_all_valid_vars(self):
        """All valid template variables pass."""
        _validate_template("{type}/{group}/{variant}/{area}/{folder}", "Test")

    def test_invalid_variable(self):
        """Invalid template variable raises ValueError."""
        with pytest.raises(ValueError, match="invalid template variables"):
            _validate_template("{bogus}", "Test")

    def test_plain_string(self):
        """Plain string with no variables is valid."""
        _validate_template("static_folder", "Test")
