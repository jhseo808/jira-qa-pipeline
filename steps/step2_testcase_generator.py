"""
Step 2: QA plan → Test cases markdown.
Claude Code generates test cases interactively based on the QA plan.
"""

from pathlib import Path

from lib.state import mark_step_complete, save_state


def read_qa_plan(state: dict) -> str:
    """Read and return the QA plan content."""
    qa_plan_path = Path(state["artifacts"]["qa_plan"])
    if not qa_plan_path.exists():
        raise RuntimeError(f"QA plan not found at {qa_plan_path}. Run step 'plan' first.")
    return qa_plan_path.read_text(encoding="utf-8")


def write_testcases(state: dict, config: dict, content: str) -> dict:
    """Write Claude-generated test cases to output file."""
    output_path = Path(state["artifacts"]["test_cases"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"[Step 2] Test cases written to {output_path}")
    mark_step_complete(state, "testcases")
    save_state(state, config["output"]["base_dir"])
    return state


def run(state: dict, config: dict) -> dict:
    print(f"[Step 2] Reading QA plan for {state['ticket']}...")
    qa_plan = read_qa_plan(state)
    print(f"[Step 2] QA plan loaded ({len(qa_plan)} chars)")
    print(f"[Step 2] Output path: {state['artifacts']['test_cases']}")
    print("[Step 2] Claude Code will now generate test cases.")
    return state
