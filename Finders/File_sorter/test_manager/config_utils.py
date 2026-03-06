"""
config_utils.py - Utilities for saving and modifying test_identifiers.yaml.
"""

import os
import yaml


# === CONSTANTS ===
YAML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "test_configs", "test_identifiers.yaml"
)

FILETYPES = ["xlsx", "xlsm", "xls", "csv"]
META_FIELDS = {
    "priority", "folder", "group", "area", "variant", "sort_strategy",
    "SWAPPER_FILE", "SURNAME_HEADER", "FIRSTNAME_HEADER", "ID_HEADER",
}


def load_raw_configs(yaml_path=None):
    """Load YAML as a raw dict (not sorted tuples)."""
    path = yaml_path or YAML_PATH
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def save_configs(configs, yaml_path=None):
    """Save configs dict to YAML, preserving key order."""
    path = yaml_path or YAML_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(configs, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def get_next_priority(configs):
    """Return the next available priority number."""
    max_p = 0
    for cfg in configs.values():
        try:
            p = int(cfg.get("priority", 0))
            if p > max_p:
                max_p = p
        except (TypeError, ValueError):
            continue
    return max_p + 1


def get_all_folders(configs):
    """Return sorted list of unique folder names."""
    return sorted(set(
        cfg.get("folder", "") for cfg in configs.values() if cfg.get("folder")
    ))


def build_test_entry(folder, group, area, variant, sort_strategy,
                     keys_dict, find_keys_dict, priority=None,
                     swapper="", surname_h="", firstname_h="", id_h=""):
    """Build a test entry dict from form values."""
    entry = {
        "priority": priority,
        "folder": folder,
        "group": group,
        "area": area,
        "variant": variant,
        "sort_strategy": sort_strategy,
    }

    for ft in FILETYPES:
        ft_section = {}
        keys = keys_dict.get(ft, [])
        find_keys = find_keys_dict.get(ft, [])
        if keys:
            ft_section["KEYS"] = keys
        if find_keys:
            ft_section["FIND_KEYS"] = find_keys
        if ft_section:
            entry[ft] = ft_section

    if swapper:
        entry["SWAPPER_FILE"] = swapper
    if surname_h:
        entry["SURNAME_HEADER"] = surname_h
    if firstname_h:
        entry["FIRSTNAME_HEADER"] = firstname_h
    if id_h:
        entry["ID_HEADER"] = id_h

    return entry
