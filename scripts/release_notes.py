#!/usr/bin/env python3
"""
Extract release notes for a specific version from CHANGELOG.md.

Assumes Keep a Changelog headings:
  ## [Unreleased]
  ## [0.1.0] - YYYY-MM-DD

Usage:
  python scripts/release_notes.py --version 0.1.0
  python scripts/release_notes.py --version v0.1.0
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"


_HEADING_RE = re.compile(r"^## \[(?P<v>[0-9]+\.[0-9]+\.[0-9]+)\].*$", re.MULTILINE)


def normalize_version(v: str) -> str:
    v = v.strip()
    if v.startswith("v"):
        v = v[1:]
    if not re.fullmatch(r"\d+\.\d+\.\d+", v):
        raise SystemExit("ERROR: --version must be X.Y.Z (or vX.Y.Z)")
    return v


def extract_notes(changelog_text: str, version: str) -> str:
    """
    Return the section for `version` excluding the heading line, up to the next version heading.
    """
    headings = list(_HEADING_RE.finditer(changelog_text))
    for i, m in enumerate(headings):
        if m.group("v") != version:
            continue
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(changelog_text)
        body = changelog_text[start:end].strip("\n")
        return body.strip() + "\n"
    raise SystemExit(f"ERROR: version not found in CHANGELOG.md: {version}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, help="X.Y.Z or vX.Y.Z")
    ap.add_argument("--changelog", default=str(CHANGELOG), help="Path to CHANGELOG.md")
    args = ap.parse_args()

    version = normalize_version(args.version)
    path = Path(args.changelog)
    text = path.read_text(encoding="utf-8")
    notes = extract_notes(text, version)
    print(notes, end="")


if __name__ == "__main__":
    main()
