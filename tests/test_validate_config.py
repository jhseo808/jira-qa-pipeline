from __future__ import annotations

from pathlib import Path

from lib.validate_config import validate_config


def test_validate_ok_with_existing_acli_and_output(tmp_path: Path) -> None:
    fake_acli = tmp_path / "acli.exe"
    fake_acli.write_text("stub", encoding="utf-8")
    out_dir = tmp_path / "out"

    cfg = {
        "_meta": {"config_path": str(tmp_path / "config.yaml")},
        "acli": {"path": str(fake_acli)},
        "output": {"base_dir": str(out_dir)},
        "jira": {"severity_field": "customfield_10058"},
    }
    issues = validate_config(cfg)
    assert [i for i in issues if i.level == "ERROR"] == []


def test_validate_fails_when_acli_missing(tmp_path: Path) -> None:
    cfg = {
        "_meta": {"config_path": str(tmp_path / "config.yaml")},
        "acli": {"path": str(tmp_path / "nope.exe")},
        "output": {"base_dir": str(tmp_path / "out")},
    }
    issues = validate_config(cfg)
    assert any(i.level == "ERROR" and i.key == "acli.path" for i in issues)
