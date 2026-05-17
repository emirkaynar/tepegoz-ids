import os
from typing import Dict


def parse_key_value_file(path: str) -> Dict[str, str]:
    """Parses simple KEY=VALUE files and ignores blank/comment lines."""
    values: Dict[str, str] = {}
    if not os.path.exists(path):
        return values

    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key:
                continue
            values[key] = value.strip()

    return values


def get_setting(name: str, default: str, config_path: str) -> str:
    """Lookup order: environment, config file, default."""
    env_value = os.getenv(name)
    if env_value is not None:
        return env_value

    config_values = parse_key_value_file(config_path)
    if name in config_values:
        return config_values[name]

    return default


def get_bool_setting(name: str, default: bool, config_path: str) -> bool:
    raw_default = "true" if default else "false"
    value = get_setting(name, raw_default, config_path).strip().lower()
    return value in {"1", "true", "yes", "on"}
