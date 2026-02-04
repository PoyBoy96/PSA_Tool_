import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "version.py"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"


def read_version() -> str:
    content = VERSION_FILE.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if not match:
        raise RuntimeError("Could not find __version__ in version.py")
    return match.group(1)


def write_version(new_version: str) -> None:
    content = VERSION_FILE.read_text(encoding="utf-8")
    content = re.sub(r'(__version__\s*=\s*")[^"]+(")', rf'\g<1>{new_version}\2', content)
    VERSION_FILE.write_text(content, encoding="utf-8")


def bump_version(current: str, kind: str) -> str:
    major, minor, patch = (int(p) for p in current.split("."))
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unknown bump kind: {kind}")


def update_changelog(new_version: str, notes: list[str]) -> None:
    if not CHANGELOG_FILE.exists():
        CHANGELOG_FILE.write_text("# Changelog\n\n", encoding="utf-8")

    content = CHANGELOG_FILE.read_text(encoding="utf-8")
    header = f"## {new_version}"
    if header in content:
        return

    bullets = notes if notes else ["TBD"]
    bullet_lines = "\n".join(f"- {note}" for note in bullets)
    new_section = f"{header}\n{bullet_lines}\n\n"

    if content.startswith("# Changelog"):
        head, rest = content.split("\n", 1)
        rest = rest.lstrip("\n")
        updated = f"{head}\n\n{new_section}{rest}"
    else:
        updated = f"{new_section}{content}"

    CHANGELOG_FILE.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bump version and update changelog.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--set", dest="set_version", help="Set version explicitly, e.g. 1.2.3")
    group.add_argument("kind", nargs="?", choices=["major", "minor", "patch"], help="Bump kind")
    parser.add_argument("--note", action="append", default=[], help="Changelog note (repeatable)")
    parser.add_argument("--no-changelog", action="store_true", help="Skip changelog update")
    args = parser.parse_args()

    current = read_version()
    if args.set_version:
        new_version = args.set_version.strip()
    else:
        new_version = bump_version(current, args.kind)

    write_version(new_version)

    if not args.no_changelog:
        update_changelog(new_version, args.note)

    print(f"Bumped version: {current} -> {new_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
