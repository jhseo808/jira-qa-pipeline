from __future__ import annotations

from pathlib import Path


def test_bump_version_dry_run_does_not_change_files(tmp_path: Path) -> None:
    # Arrange: minimal pyproject + changelog
    pyproject = tmp_path / "pyproject.toml"
    changelog = tmp_path / "CHANGELOG.md"
    pyproject.write_text(
        '[project]\nname="x"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    changelog.write_text("## [Unreleased]\n\n", encoding="utf-8")

    # Import module and patch paths
    import importlib

    m = importlib.import_module("scripts.bump_version")
    m.PYPROJECT = pyproject
    m.CHANGELOG = changelog

    before_py = pyproject.read_text(encoding="utf-8")
    before_cl = changelog.read_text(encoding="utf-8")

    # Act
    m.bump_pyproject("0.1.1", dry_run=True)
    m.scaffold_changelog("0.1.1", dry_run=True)

    # Assert: unchanged
    assert pyproject.read_text(encoding="utf-8") == before_py
    assert changelog.read_text(encoding="utf-8") == before_cl


def test_scaffold_changelog_inserts_version(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("## [Unreleased]\n\n### Added\n\n", encoding="utf-8")

    import importlib

    m = importlib.import_module("scripts.bump_version")
    m.CHANGELOG = changelog

    m.scaffold_changelog("1.2.3", dry_run=False)
    text = changelog.read_text(encoding="utf-8")
    assert "## [1.2.3]" in text

