from __future__ import annotations

from pathlib import Path

from lib.init_project import init_project


def test_init_project_creates_env_and_local_yaml(tmp_path: Path) -> None:
    results = init_project(tmp_path)
    created = {r.path.name for r in results if r.created}
    assert ".env" in created
    assert "config.local.yaml" in created
    assert (tmp_path / ".env").is_file()
    assert (tmp_path / "config.local.yaml").is_file()


def test_init_project_does_not_overwrite(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("x", encoding="utf-8")
    (tmp_path / "config.local.yaml").write_text("y", encoding="utf-8")
    results = init_project(tmp_path)
    skipped = {r.path.name for r in results if not r.created}
    assert ".env" in skipped
    assert "config.local.yaml" in skipped
    assert (tmp_path / ".env").read_text(encoding="utf-8") == "x"
    assert (tmp_path / "config.local.yaml").read_text(encoding="utf-8") == "y"
