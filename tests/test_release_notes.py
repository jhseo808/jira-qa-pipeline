from __future__ import annotations

import pytest

from scripts.release_notes import extract_notes, normalize_version


def test_normalize_version_accepts_v_prefix() -> None:
    assert normalize_version("v1.2.3") == "1.2.3"


def test_extract_notes_returns_section_body() -> None:
    text = (
        "# Changelog\n\n"
        "## [Unreleased]\n\n"
        "## [1.0.0] - 2026-01-01\n\n"
        "### Added\n\n"
        "- A\n\n"
        "## [0.9.0] - 2025-12-01\n\n"
        "- Older\n"
    )
    notes = extract_notes(text, "1.0.0")
    assert "### Added" in notes
    assert "- A" in notes
    assert "Older" not in notes


def test_extract_notes_errors_when_missing() -> None:
    with pytest.raises(SystemExit):
        extract_notes("## [Unreleased]\n", "9.9.9")

