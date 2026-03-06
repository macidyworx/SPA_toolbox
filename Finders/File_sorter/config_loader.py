"""
config_loader.py - Loads and validates test_identifiers.yaml configuration.
"""

# === IMPORTS ===
import os
import yaml


# === CONSTANTS ===
_YAML_PATH = os.path.join(
    os.path.dirname(__file__), "test_configs", "test_identifiers.yaml"
)

REQUIRED_FIELDS = {"priority", "folder"}
FORMAT_KEYS = {"xlsx", "xlsm", "xls", "csv", "xml"}
VALID_TEMPLATE_VARS = {"type", "group", "variant", "area", "folder"}
VALID_MATCH_TYPES = {"KEYS", "FIND_KEYS"}


# === VALIDATION ===
def _validate_template(strategy, test_name):
    """Validate sort_strategy template contains only valid variables."""
    import re
    variables = re.findall(r"\{(\w+)\}", strategy)
    invalid = [v for v in variables if v not in VALID_TEMPLATE_VARS]
    if invalid:
        raise ValueError(
            f"Test type '{test_name}': sort_strategy contains invalid "
            f"template variables: {invalid}. "
            f"Valid variables: {sorted(VALID_TEMPLATE_VARS)}"
        )


def _validate_key_entry(entry, test_name, fmt, key_type):
    """Validate a single KEYS or FIND_KEYS entry."""
    if not isinstance(entry, dict):
        raise ValueError(
            f"Test type '{test_name}' -> {fmt} -> {key_type}: "
            f"expected dict, got {type(entry).__name__}"
        )

    if key_type == "KEYS":
        if fmt != "xml":
            if "cell" not in entry:
                raise ValueError(
                    f"Test type '{test_name}' -> {fmt} -> KEYS: "
                    f"missing 'cell' field"
                )
            if isinstance(entry["cell"], list):
                raise ValueError(
                    f"Test type '{test_name}' -> {fmt} -> KEYS: "
                    f"cell value is a list — should be A1 notation string"
                )

    has_match = any(k in entry for k in ("startswith", "contains", "tag"))
    if not has_match:
        raise ValueError(
            f"Test type '{test_name}' -> {fmt} -> {key_type}: "
            f"missing match type (startswith, contains, or tag)"
        )


def _validate_test_type(name, config):
    """Validate a single test type configuration."""
    if not isinstance(config, dict):
        raise ValueError(
            f"Test type '{name}': expected dict, got {type(config).__name__}"
        )

    missing = REQUIRED_FIELDS - set(config.keys())
    if missing:
        raise ValueError(
            f"Test type '{name}': missing required fields: {sorted(missing)}"
        )

    if not isinstance(config["priority"], int):
        raise ValueError(
            f"Test type '{name}': priority must be an integer, "
            f"got {type(config['priority']).__name__}"
        )

    has_format = any(k in config for k in FORMAT_KEYS)
    if not has_format:
        raise ValueError(
            f"Test type '{name}': must define at least one format "
            f"({', '.join(sorted(FORMAT_KEYS))})"
        )

    strategy = config.get("sort_strategy", "{folder}")
    _validate_template(strategy, name)

    for fmt in FORMAT_KEYS:
        if fmt not in config:
            continue
        fmt_config = config[fmt]
        if not isinstance(fmt_config, dict):
            raise ValueError(
                f"Test type '{name}' -> {fmt}: expected dict, "
                f"got {type(fmt_config).__name__}"
            )
        has_keys = any(k in fmt_config for k in VALID_MATCH_TYPES)
        if not has_keys:
            raise ValueError(
                f"Test type '{name}' -> {fmt}: must contain "
                f"KEYS or FIND_KEYS"
            )
        for key_type in VALID_MATCH_TYPES:
            if key_type not in fmt_config:
                continue
            entries = fmt_config[key_type]
            if not isinstance(entries, list):
                raise ValueError(
                    f"Test type '{name}' -> {fmt} -> {key_type}: "
                    f"expected list, got {type(entries).__name__}"
                )
            for entry in entries:
                _validate_key_entry(entry, name, fmt, key_type)


# === LOADER ===
def load_test_configs(yaml_path=None, validate=True):
    """Load test identifiers from YAML, validate, return sorted by priority.

    Args:
        yaml_path: Path to YAML file. Defaults to bundled test_identifiers.yaml.
        validate: If True, validate each test type config.

    Returns:
        list of (name, config) tuples sorted by priority (lowest first).

    Raises:
        FileNotFoundError: If YAML file doesn't exist.
        ValueError: If validation fails.
        yaml.YAMLError: If YAML is malformed.
    """
    path = yaml_path or _YAML_PATH

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError(
            f"Expected top-level YAML dict, got {type(raw).__name__}"
        )

    if validate:
        for name, config in raw.items():
            _validate_test_type(name, config)

    sorted_configs = sorted(raw.items(), key=lambda x: x[1]["priority"])
    return sorted_configs


# === STANDALONE EXECUTION ===
if __name__ == "__main__":
    configs = load_test_configs()
    print(f"Loaded {len(configs)} test types:")
    for name, cfg in configs:
        formats = [k for k in cfg if k in FORMAT_KEYS]
        print(f"  {cfg['priority']:3d}  {name} ({', '.join(formats)})")
