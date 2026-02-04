# PSA Tool

A small Tkinter utility to copy RS assets (MOV + WAV) and stitch MS assets (MP4) into a weekly destination folder. Defaults for paths and ffmpeg can be customized via config.

## Prerequisites (Windows)
1. Install Python 3.10+ and check **Add Python to PATH** during install.
2. Install Git for Windows (only needed if you plan to clone the repo).

## Setup (Step‑By‑Step)
1. Open **PowerShell**.
2. Clone the repo and enter it:
   ```powershell
   git clone https://github.com/PoyBoy96/PSA-TOOL.git
   cd PSA_TOOL
   ```
3. Create and activate a virtual environment:
   ```powershell
   py -3.10 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
4. Install dependencies:
   ```powershell
   pip install pillow
   ```
5. Run the app:
   ```powershell
   python PSA_Tool.py
   ```

## First‑Run Configuration (In the App)
1. Click **Settings**.
2. Set **Source Folder Path** to the folder that contains your RS `.mov` files and a `Music` subfolder with `.wav` files.
3. Set **Destination Root Folder** to the folder where weekly output should be created.
4. Click **Save**.

## Daily Usage (In the App)
1. Select the destination subfolder and week number (or create a new folder).
2. Select RS clips to copy.
3. Select MS clips and order them.
4. The output filename is auto‑generated for next Saturday; click the field to edit if needed.
5. Click **Copy Files**.
6. Click **Open Folder** to open the final destination path.

## Configuration Files
1. `psa_config.json` is created on first run and stores defaults (source/dest roots, logo path, ffmpeg settings). Safe to edit.
2. `psa_tool_settings.json` stores your last-used settings in the app folder.

## ffmpeg
1. The app looks for `ffmpeg.exe` on PATH, next to the app, or in `ffmpeg-bin`.
2. If not found, it auto-downloads the Windows build into `ffmpeg-bin` on first MS stitch.

## Update Notifications (Optional)
The app can notify users when a newer release is available.

1. Create a GitHub Release for each version (tag name like `v1.2.0`).
2. Set your repo in `psa_config.json`:
   ```json
   "update_repo": "OWNER/REPO"
   ```
3. If the repo is private, create a fine‑grained GitHub token with **read-only** access to that repo and save it in:
   ```text
   update_token.txt
   ```
   or set an environment variable:
   ```powershell
   $env:PSA_TOOL_GITHUB_TOKEN="your_token_here"
   ```

Auto‑update behavior:
- When an update is available, the app can download the new exe and replace itself.
- Existing settings (`psa_tool_settings.json`) are kept because the update only swaps the exe file.

## Versioning and Release Checklist
We use **Semantic Versioning**: `MAJOR.MINOR.PATCH`

- `1.2.1` = small fix
- `1.3.0` = new feature
- `2.0.0` = breaking change

Release steps:
1. Update `version.py` to the new version.
2. Add an entry to `CHANGELOG.md`.
3. Commit and push:
   ```powershell
   git add -A
   git commit -m "Release v1.2.1"
   git push
   ```
4. GitHub Actions will build and publish the release automatically based on `version.py`.

### Optional: Auto Bump Version + Changelog
Use the helper script to bump versions and insert a new changelog section.

```powershell
python scripts/bump_version.py patch --note "Fix small issue"
```

Other examples:
```powershell
python scripts/bump_version.py minor --note "Add new feature"
python scripts/bump_version.py major --note "Big overhaul"
python scripts/bump_version.py --set 2.1.0 --note "Manual set"
```

Skip changelog edits:
```powershell
python scripts/bump_version.py patch --no-changelog
```


## Packaging (Optional)
1. Install PyInstaller:
   ```powershell
   pip install pyinstaller
   ```
2. Build using the spec:
   ```powershell
   pyinstaller --clean PSA_Tool.spec
   ```
3. The exe is created at `dist\PSA_Tool.exe`.
4. Place `ffmpeg.exe` next to the exe if you don’t want auto-download on first run.
