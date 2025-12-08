# PSA Tool

A small Tkinter utility to copy RS assets (MOV + WAV) and stitch MS assets (MP4) into a weekly destination folder. Defaults for network paths and ffmpeg can be customized via config.

## Setup
- Requires Python 3.10+ with Tkinter.
- Clone this repo, then run the app with `python PSA_Tool.py`.
- ffmpeg: the app will look for `ffmpeg`/`ffmpeg.exe` on PATH or next to the app; if missing, it auto-downloads the Windows build to `ffmpeg-bin`.

## Configuration
- `psa_config.json`: stores defaults such as source/destination roots, logo path, ffmpeg names, and download URL. Safe to edit directly.
- User-specific selections (source/dest root) are persisted to `psa_tool_settings.json` in the app directory.

## Usage
1) Launch: `python PSA_Tool.py`.
2) Click **Settings** to set source and destination root paths.
3) Pick a destination subfolder and week number; add new folders if needed.
4) Select RS clips to copy; select MS clips and order them; set date + initials for the stitched filename.
5) Click **Copy Files** to perform the operations. Status/logs show progress.

## Packaging (optional)
- Install PyInstaller: `pip install pyinstaller`
- Quick build from the script: `pyinstaller --onefile PSA_Tool.py`
- Or use the provided spec: `pyinstaller PSA_Tool.spec`
- Output lands in `dist/PSA_Tool.exe`. Place `ffmpeg.exe` next to it or rely on auto-download on first run.
