"""
Step 5: Test results + QA plan → QA result report.
Claude Code reads results and generates the report interactively.
"""

import json
from pathlib import Path

from lib.state import mark_step_complete, save_state


def read_results_summary(state: dict) -> dict:
    """Read and return test results as dict."""
    results_path = Path(state["artifacts"]["test_results"])
    if not results_path.exists():
        raise RuntimeError("Test results not found. Run step 'run' first.")
    return json.loads(results_path.read_text(encoding="utf-8"))


def write_report(state: dict, config: dict, report_content: str) -> dict:
    """Write Claude-generated QA report to output file."""
    output_path = Path(state["artifacts"]["qa_report"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_content, encoding="utf-8")
    print(f"[Step 5] QA report written to {output_path}")
    mark_step_complete(state, "report")
    save_state(state, config["output"]["base_dir"])
    return state


def run(state: dict, config: dict) -> dict:
    print(f"[Step 5] Loading test results for {state['ticket']}...")
    results = read_results_summary(state)
    stats = results.get("stats", {})
    print(
        f"[Step 5] Results: {stats.get('expected', 0)} passed / "
        f"{stats.get('unexpected', 0)} failed / {stats.get('skipped', 0)} skipped"
    )
    print(f"[Step 5] Output path: {state['artifacts']['qa_report']}")
    print("[Step 5] Claude Code will now generate the QA report.")
    return state
