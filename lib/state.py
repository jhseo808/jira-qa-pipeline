"""
PipelineState - JSON-backed state management for the QA automation pipeline.
"""

import json
from datetime import datetime
from pathlib import Path

DEFAULT_STATE = {
    "ticket": "",
    "project_key": "",
    "target_url": "",
    "steps_completed": [],
    "artifacts": {
        "qa_plan": None,
        "test_cases": None,
        "playwright_dir": None,
        "test_results": None,
        "qa_report": None,
        "created_bugs": None,
        "dashboard": None,
        "side_effects": None,
    },
    "jira_context": {},
    "created_at": "",
    "last_updated": "",
}


def create_state(
    ticket: str,
    project_key: str,
    output_base: str,
    target_url: str = "",
) -> dict:
    """Create a fresh pipeline state dict and set all artifact paths."""
    state = DEFAULT_STATE.copy()
    state["artifacts"] = DEFAULT_STATE["artifacts"].copy()
    state["ticket"] = ticket
    state["project_key"] = project_key
    state["target_url"] = target_url
    state["created_at"] = datetime.now().isoformat()
    state["last_updated"] = state["created_at"]

    base = Path(output_base) / ticket
    state["artifacts"] = {
        "qa_plan": str(base / "qa_plan.md"),
        "test_cases": str(base / "test_cases.md"),
        "playwright_dir": str(base / "playwright"),
        "test_results": str(base / "test_results.json"),
        "qa_report": str(base / "qa_report.md"),
        "created_bugs": str(base / "created_bugs.json"),
        "dashboard": str(base / "dashboard.html"),
        "side_effects": str(base / "side_effects.md"),
    }
    return state


def save_state(state: dict, output_base: str) -> None:
    """Persist state to pipeline_state.json inside the ticket output directory."""
    state["last_updated"] = datetime.now().isoformat()
    path = Path(output_base) / state["ticket"] / "pipeline_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_state(ticket: str, output_base: str) -> dict | None:
    """Load existing state from disk. Returns None if not found."""
    path = Path(output_base) / ticket / "pipeline_state.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def mark_step_complete(state: dict, step_name: str) -> dict:
    """Add step_name to steps_completed (idempotent)."""
    if step_name not in state["steps_completed"]:
        state["steps_completed"].append(step_name)
    return state


def list_active_tickets(output_base: str) -> list[str]:
    """Return list of all ticket keys that have a pipeline_state.json."""
    base = Path(output_base)
    tickets = []
    for state_file in base.glob("*/pipeline_state.json"):
        try:
            s = json.loads(state_file.read_text(encoding="utf-8"))
            tickets.append(s["ticket"])
        except Exception:
            pass
    return tickets
