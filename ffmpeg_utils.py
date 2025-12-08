import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional
import urllib.request

from config import base_dir


def find_ffmpeg_existing(ffmpeg_names: List[str]) -> Optional[str]:
    candidates = [base_dir(), base_dir() / "ffmpeg-bin", Path.cwd()]
    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS))

    for folder in candidates:
        for name in ffmpeg_names:
            candidate = Path(folder) / name
            if candidate.is_file():
                return str(candidate)
    return shutil.which("ffmpeg")


def _download_ffmpeg(download_url: str) -> str:
    bin_dir = base_dir() / "ffmpeg-bin"
    bin_dir.mkdir(exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp_path = Path(tmp.name)
    try:
        with urllib.request.urlopen(download_url) as resp, open(tmp_path, "wb") as out:
            shutil.copyfileobj(resp, out)
        with zipfile.ZipFile(tmp_path, "r") as zf:
            member = next((m for m in zf.namelist() if m.lower().endswith("bin/ffmpeg.exe")), None)
            if not member:
                raise RuntimeError("Could not find ffmpeg.exe in downloaded archive.")
            target = bin_dir / "ffmpeg.exe"
            with zf.open(member) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
        return str(target)
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def ensure_ffmpeg(ffmpeg_names: List[str], download_url: str) -> str:
    existing = find_ffmpeg_existing(ffmpeg_names)
    if existing:
        return existing
    return _download_ffmpeg(download_url)
