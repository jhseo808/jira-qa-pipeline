#!/usr/bin/env python3
"""
Bump project version in pyproject.toml and scaffold CHANGELOG.md entry.

Usage:
  python scripts/bump_version.py --new-version 0.1.1
  python scripts/bump_version.py --new-version 0.2.0 --dry-run
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"


_VERSION_RE = re.compile(r'(?m)^version\s*=\s*"(?P<v>[^"]+)"\s*$')
_HEADING_RE = re.compile(r"(?m)^## \[(?P<v>[0-9]+\.[0-9]+\.[0-9]+)\]\s+-\s+(?P<d>\d{4}-\d{2}-\d{2})\s*$")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, content: str, *, dry_run: bool) -> None:
    if dry_run:
        return
    path.write_text(content, encoding="utf-8")


def bump_pyproject(new_version: str, *, dry_run: bool) -> tuple[str, str]:
    raw = _read(PYPROJECT)
    m = _VERSION_RE.search(raw)
    if not m:
        raise SystemExit("ERROR: could not find [project].version in pyproject.toml")
    old_version = m.group("v")
    if old_version == new_version:
        return old_version, raw
    updated = _VERSION_RE.sub(f'version = "{new_version}"', raw, count=1)
    _write(PYPROJECT, updated, dry_run=dry_run)
    return old_version, updated


def scaffold_changelog(new_version: str, *, dry_run: bool) -> None:
    if not CHANGELOG.exists():
        raise SystemExit("ERROR: CHANGELOG.md not found")

    raw = _read(CHANGELOG)
    if f"## [{new_version}]" in raw:
        return

    today = date.today().isoformat()
    entry = (
        f"## [{new_version}] - {today}\n\n"
        "### Added\n\n"
        "### Changed\n\n"
        "### Fixed\n\n"
    )

    # Insert right after [Unreleased] section header.
    idx = raw.find("## [Unreleased]")
    if idx == -1:
        raise SystemExit("ERROR: CHANGELOG.md missing '## [Unreleased]' heading")

    # Find end of the Unreleased header line.
    after = raw.find("\n", idx)
    if after == -1:
        raise SystemExit("ERROR: invalid CHANGELOG.md format")
    after += 1

    updated = raw[:after] + "\n" + entry + "\n" + raw[after:]
    _write(CHANGELOG, updated, dry_run=dry_run)


def validate_semver(v: str) -> None:
    if not re.fullmatch(r"\d+\.\d+\.\d+", v):
        raise SystemExit("ERROR: --new-version must be SemVer: X.Y.Z")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-version", required=True, help="SemVer X.Y.Z")
    ap.add_argument("--dry-run", action="store_true", help="Do not write files")
    args = ap.parse_args()

    new_version = args.new_version.strip()
    validate_semver(new_version)

    old_version, _ = bump_pyproject(new_version, dry_run=args.dry_run)
    scaffold_changelog(new_version, dry_run=args.dry_run)

    print(f"[Bump] {old_version} -> {new_version}")
    if args.dry_run:
        print("[Bump] dry-run: no files written")


if __name__ == "__main__":
    main()

