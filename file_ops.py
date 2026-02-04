import os
import shutil
import subprocess
import tempfile
from typing import List


def build_folder_structure(dest: str) -> None:
    paths = [
        os.path.join(dest, "PSAs"),
        os.path.join(dest, "PSAs", "RS"),
        os.path.join(dest, "PSAs", "RS", "Music"),
        os.path.join(dest, "PSAs", "MS"),
    ]
    for path in paths:
        os.makedirs(path, exist_ok=True)


def copy_selected_files(dest: str, selected: List[str], source: str) -> None:
    rs_folder = os.path.join(dest, "PSAs", "RS")
    music_folder = os.path.join(rs_folder, "Music")

    for name in selected:
        video_src = os.path.join(source, f"{name}.mov")
        music_src = os.path.join(source, "Music", f"{name}.wav")

        if os.path.exists(video_src):
            shutil.copy2(video_src, rs_folder)
        if os.path.exists(music_src):
            shutil.copy2(music_src, music_folder)


def stitch_ms_files(dest: str, ordered_names: List[str], source: str, output_filename: str, ffmpeg_path: str) -> str:
    output_dir = os.path.join(dest, "PSAs", "MS")
    os.makedirs(output_dir, exist_ok=True)

    source_ms = os.path.join(source, "MS")
    input_paths = []
    for name in ordered_names:
        path = os.path.join(source_ms, f"{name}.mp4")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing source clip: {path}")
        input_paths.append(path)

    output_path = os.path.join(output_dir, output_filename)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as tf:
        for path in input_paths:
            safe_path = path.replace("\\", "/").replace("'", r"'\''")
            tf.write(f"file '{safe_path}'\n")
        list_path = tf.name

    cmd = [
        ffmpeg_path,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_path,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        output_path,
    ]

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=creationflags,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ffmpeg failed")
    finally:
        if os.path.exists(list_path):
            os.remove(list_path)

    return output_path
