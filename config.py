import json
import os
import sys
from pathlib import Path

CONFIG_FILENAME = "psa_config.json"

DEFAULT_CONFIG = {
    "settings_file": "psa_tool_settings.json",
    "default_source": r"\\\\\\\\sbcreative\\ActiveProjects\\ADULTS\\_2025\\PSAs_OUTROs\\PSAs\\EXPORTS_FINAL\\Segments",
    "default_dest_root": r"\\\\\\\\sccserver\\Production Event Media\\Sermon Series",
    "logo_path": "Sagebrush.png",
    "ffmpeg_names": ["ffmpeg.exe", "ffmpeg"],
    "ffmpeg_download_url": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
}


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def config_path() -> Path:
    return base_dir() / CONFIG_FILENAME


def _write_default_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        _write_default_config(path)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    merged = DEFAULT_CONFIG.copy()
    merged.update(data)
    return merged
