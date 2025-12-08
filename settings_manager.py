import json
from pathlib import Path
from typing import Dict

from config import base_dir


def _settings_path(config: Dict) -> Path:
    filename = config.get("settings_file", "psa_tool_settings.json")
    return base_dir() / filename


def load_settings(config: Dict) -> Dict:
    defaults = {
        "source": config.get("default_source", ""),
        "dest_root": config.get("default_dest_root", ""),
    }
    path = _settings_path(config)
    if not path.exists():
        return defaults

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return defaults

    defaults.update(data)
    return defaults


def save_settings(settings: Dict, config: Dict) -> None:
    path = _settings_path(config)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)
