import os
from pathlib import Path
import tkinter as tk

from config import base_dir

LOGO_BASE64 = (
    "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"
)


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        path = base_dir() / path_str
    return path


def load_logo_image(root: tk.Tk, path_str: str):
    path = resolve_path(path_str)
    if path.exists():
        try:
            return tk.PhotoImage(master=root, file=str(path))
        except Exception:
            pass
    try:
        return tk.PhotoImage(master=root, data=LOGO_BASE64)
    except Exception:
        return None
