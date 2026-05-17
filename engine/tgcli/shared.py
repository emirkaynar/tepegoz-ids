import json
import os
from datetime import datetime, timezone
from typing import Dict


def get_sensor_config_path() -> str:
    return os.getenv("TEPEGOZ_SENSOR_CONFIG_PATH", "/etc/tepegoz-ids/sensor.conf")


def get_dash_state_path() -> str:
    return os.getenv("TEPEGOZ_DASH_STATE_PATH", "/var/lib/tepegoz-ids/dash-state.json")


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def update_key_value_file(path: str, key: str, value: str) -> None:
    ensure_parent_dir(path)

    lines = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.readlines()

    updated = False
    new_lines = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped.startswith("#") or "=" not in stripped:
            new_lines.append(raw_line)
            continue

        current_key, _ = stripped.split("=", 1)
        if current_key.strip() == key:
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(raw_line)

    if not updated:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append(f"{key}={value}\n")

    with open(path, "w", encoding="utf-8") as handle:
        handle.writelines(new_lines)


def read_dash_state(path: str) -> Dict[str, object]:
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_dash_state(path: str, state: Dict[str, object]) -> None:
    ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)
        handle.write("\n")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
