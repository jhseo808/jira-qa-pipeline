"""
Step 1: Fetch Jira ticket → cache context in pipeline state.
Claude Code (interactive session) generates the actual QA plan and writes it.
"""

from pathlib import Path

from lib.acli import AcliClient
from lib.state import mark_step_complete, save_state


def run(state: dict, config: dict) -> dict:
    """Fetch Jira ticket data and cache in state."""
    acli = AcliClient(config)
    ticket_key = state["ticket"]

    print(f"[Step 1] Fetching Jira ticket {ticket_key}...")
    issue = acli.get_issue(ticket_key)
    if not issue:
        raise RuntimeError(f"Cannot fetch ticket {ticket_key} from Jira")

    fields = issue.get("fields", {})
    state["jira_context"] = {
        "key": ticket_key,
        "summary": fields.get("summary", ""),
        "description": fields.get("description", ""),
        "status": (fields.get("status") or {}).get("name", ""),
        "priority": (fields.get("priority") or {}).get("name", ""),
        "labels": fields.get("labels", []),
        "components": [c.get("name", "") for c in (fields.get("components") or [])],
        "created": fields.get("created", ""),
        "reporter": (fields.get("reporter") or {}).get("displayName", ""),
    }

    save_state(state, config["output"]["base_dir"])
    print(f"[Step 1] Ticket fetched: {state['jira_context']['summary']}")
    print(f"[Step 1] Output path: {state['artifacts']['qa_plan']}")
    print("[Step 1] Claude Code will now generate the QA plan.")
    return state


def write_plan(state: dict, config: dict, plan_content: str) -> dict:
    """Write Claude-generated QA plan to output file and mark step complete."""
    output_path = Path(state["artifacts"]["qa_plan"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(plan_content, encoding="utf-8")
    print(f"[Step 1] QA plan written to {output_path}")
    mark_step_complete(state, "plan")
    save_state(state, config["output"]["base_dir"])
    return state
