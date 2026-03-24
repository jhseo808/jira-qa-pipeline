"""
Step 8: Fetch recent Jira bugs → Claude Code analyzes side effects → updates test cases.
"""

from datetime import datetime, timedelta
from pathlib import Path

from lib.acli import AcliClient
from lib.state import mark_step_complete, save_state


def fetch_recent_bugs(state: dict, config: dict, days: int = 7) -> list[dict]:
    """Fetch bugs created in the last N days from Jira."""
    acli = AcliClient(config)
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    jql = (
        f"project = {state['project_key']} AND issuetype = 버그 "
        f'AND created >= "{since_date}" ORDER BY created DESC'
    )
    keys = acli.search_issues(jql, state["project_key"])
    bugs = []
    for key in keys[:20]:
        detail = acli.get_issue_detail(key)
        if detail:
            bugs.append(detail)
    return bugs


def write_side_effects(state: dict, config: dict, content: str, append_testcases: str = "") -> dict:
    """Write side effects report and optionally append new test cases."""
    output_path = Path(state["artifacts"]["side_effects"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    if append_testcases:
        tc_path = Path(state["artifacts"]["test_cases"])
        if tc_path.exists():
            with open(tc_path, "a", encoding="utf-8") as f:
                f.write(
                    f"\n\n---\n\n"
                    f"*사이드이펙트 감지 자동 추가 - {datetime.now().strftime('%Y-%m-%d')}*\n\n"
                )
                f.write(append_testcases)
            print(f"[Step 8] Additional test cases appended to {tc_path}")

    print(f"[Step 8] Side effects written to {output_path}")
    mark_step_complete(state, "sideeffects")
    save_state(state, config["output"]["base_dir"])
    return state


def run(state: dict, config: dict) -> dict:
    print(f"[Step 8] Fetching recent bugs for {state['ticket']}...")
    bugs = fetch_recent_bugs(state, config)

    if not bugs:
        print("[Step 8] No new bugs in last 7 days.")
        no_bugs_md = "# 사이드 이펙트 분석\n\n분석 기간 내 새로운 버그가 없습니다.\n"
        write_side_effects(state, config, no_bugs_md)
        return state

    print(f"[Step 8] Found {len(bugs)} recent bugs:")
    for b in bugs:
        print(f"  {b['key']} [{b.get('severity', '?')}] {b.get('summary', '')}")

    # 버그가 있어도 산출물·단계 완료는 반드시 기록한다 (Claude 수동 보강 전 초안).
    lines = [
        "# 사이드 이펙트 분석",
        "",
        f"최근 7일 이내 프로젝트 `{state['project_key']}` 버그 **{len(bugs)}건** (조회 상한 20건).",
        "",
        "## 조회된 버그 목록",
        "",
    ]
    for b in bugs:
        sev = b.get("severity", "?")
        summ = b.get("summary", "")
        lines.append(f"- **{b['key']}** [{sev}] {summ}")
    lines.extend(
        [
            "",
            "---",
            "",
            "*추가 분석·테스트케이스 반영은 수동 또는 Claude Code에서 보강할 수 있다.*",
        ]
    )
    content = "\n".join(lines) + "\n"

    state["recent_bugs"] = bugs
    save_state(state, config["output"]["base_dir"])

    print(f"[Step 8] Output path: {state['artifacts']['side_effects']}")
    write_side_effects(state, config, content)
    return state
