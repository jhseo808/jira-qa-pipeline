"""lib.state — 상태 생성·단계 완료."""

from __future__ import annotations

import json
from pathlib import Path

from lib.state import create_state, load_state, mark_step_complete, save_state


def test_create_state_paths(tmp_path: Path) -> None:
    st = create_state("PA-99", "PA", str(tmp_path), "https://example.com/")
    assert st["ticket"] == "PA-99"
    assert st["project_key"] == "PA"
    assert st["target_url"] == "https://example.com/"
    ap = Path(st["artifacts"]["qa_plan"])
    assert ap.name == "qa_plan.md"
    assert ap.parent.name == "PA-99"


def test_mark_step_complete_idempotent() -> None:
    st = create_state("PA-1", "PA", "/tmp", "")
    mark_step_complete(st, "plan")
    mark_step_complete(st, "plan")
    assert st["steps_completed"] == ["plan"]


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    st = create_state("PA-1", "PA", str(tmp_path), "")
    mark_step_complete(st, "plan")
    save_state(st, str(tmp_path))
    loaded = load_state("PA-1", str(tmp_path))
    assert loaded is not None
    assert loaded["ticket"] == "PA-1"
    assert "plan" in loaded["steps_completed"]
    path = Path(tmp_path) / "PA-1" / "pipeline_state.json"
    assert path.is_file()
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["ticket"] == "PA-1"
