#!/usr/bin/env python3
"""Copy selected skills between this repository and local agent directories."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil


REPO = Path(__file__).resolve().parents[1]
DEVICES = {"claude": ".claude", "codex": ".codex", "workbuddy": ".workbuddy"}
SKIP_DIRS = {".git", ".system", "node_modules", "__pycache__", ".venv", ".pytest_cache"}
SKIP_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".sqlite", ".db", ".pyc"}


def skill_name(value):
    if not value or value in {".", ".."} or any(c in value for c in '/\\:'):
        raise argparse.ArgumentTypeError("Use a skill folder name, not a path")
    return value


def files_under(root):
    """Follow an installed skill junction, but reject escaping child links."""
    base = root.resolve()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if not path.is_file():
            continue
        path.resolve().relative_to(base)
        name = path.name.lower()
        if name.startswith(".env") or ".env." in name or name.endswith(".env"):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES or name in {".ds_store", "_user_meta.json"}:
            continue
        yield path, relative


def copy_skill(source, destination, backup):
    if not (source / "SKILL.md").is_file():
        raise ValueError(f"No SKILL.md in {source}")
    changed = 0
    for path, relative in files_under(source):
        target = destination / relative
        # Existing skill roots may be junctions. Child links must stay in that root.
        target.resolve().relative_to(destination.resolve())
        if target.exists():
            if not target.is_file():
                raise ValueError(f"Destination is not a file: {target}")
            if path.read_bytes() == target.read_bytes():
                continue
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        changed += 1
    print(f"{destination}: {changed} files updated")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("direction", choices=["install", "collect"])
    parser.add_argument("skills", nargs="+", type=skill_name)
    parser.add_argument("--source", choices=DEVICES, default="claude", help="collect source")
    parser.add_argument("--home", type=Path, default=Path.home(), help="local user home")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backups = home / ".cache" / "ai-skills-backups" / stamp
    for name in args.skills:
        if args.direction == "install":
            for device, folder in DEVICES.items():
                copy_skill(REPO / "skills" / name, home / folder / "skills" / name,
                           backups / device / name)
        else:
            copy_skill(home / DEVICES[args.source] / "skills" / name,
                       REPO / "skills" / name, backups / "repository" / name)
    print("Existing files absent from the source were preserved; no files were deleted.")
    print(f"Overwritten-file backups (if any): {backups}")


if __name__ == "__main__":
    main()
