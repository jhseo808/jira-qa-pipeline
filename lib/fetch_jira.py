"""
Fetch Jira ticket data and print as structured JSON.
Claude Code uses this to read ticket context before generating artifacts.

Usage:
  python lib/fetch_jira.py PA-21
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.acli import AcliClient
from lib.config import load_config


def main():
    if len(sys.argv) < 2:
        print("Usage: python lib/fetch_jira.py <TICKET-KEY>", file=sys.stderr)
        sys.exit(1)

    ticket_key = sys.argv[1]

    config = load_config()

    acli = AcliClient(config)

    print(f"Fetching {ticket_key}...", file=sys.stderr)
    issue = acli.get_issue(ticket_key)
    if not issue:
        print(f"ERROR: Could not fetch {ticket_key}", file=sys.stderr)
        sys.exit(1)

    fields = issue.get("fields", {})
    result = {
        "key": ticket_key,
        "summary": fields.get("summary", ""),
        "description": fields.get("description", ""),
        "status": fields.get("status", {}).get("name", "") if fields.get("status") else "",
        "priority": fields.get("priority", {}).get("name", "") if fields.get("priority") else "",
        "labels": fields.get("labels", []),
        "components": [c.get("name", "") for c in fields.get("components", [])],
        "created": fields.get("created", ""),
        "updated": fields.get("updated", ""),
        "reporter": fields.get("reporter", {}).get("displayName", "")
        if fields.get("reporter")
        else "",
        "assignee": fields.get("assignee", {}).get("displayName", "")
        if fields.get("assignee")
        else "",
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
