"""
Step 7: Generate bug tracking dashboard (reuses generate_dashboard.py logic)
"""

from pathlib import Path

import generate_dashboard as gd
from lib.state import mark_step_complete, save_state


def run(state: dict, config: dict) -> dict:
    print(f"[Step 7] Generating dashboard for {state['ticket']}...")

    # Ensure generate_dashboard uses the same config source as the pipeline runner.
    meta = config.get("_meta") if isinstance(config, dict) else None
    cfg_path = (meta or {}).get("config_path") if isinstance(meta, dict) else None
    if cfg_path:
        try:
            gd.apply_runtime_settings(cfg_path)
        except Exception:
            pass

    dash_cfg = config.get("dashboard") or {}
    summary_kw = (dash_cfg.get("bug_summary_contains") or "").strip()
    jql_suffix = (dash_cfg.get("bug_jql_suffix") or "").strip()
    if summary_kw and not jql_suffix:
        # Jira 텍스트 검색: 제목에 키워드 포함 (예: 멜론 검증 범위만)
        jql_suffix = f'AND summary ~ "{summary_kw}"'

    jql = f"project = {state['project_key']} AND issuetype = 버그 {jql_suffix} ORDER BY created ASC"
    jql = " ".join(jql.split())

    output_path = Path(state["artifacts"]["dashboard"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    keys = gd.fetch_ticket_keys(jql, state["project_key"])
    bugs = [gd.fetch_bug_detail(k) for k in keys if k]
    bugs = [b for b in bugs if b]
    if summary_kw:
        bugs = [b for b in bugs if summary_kw in (b.get("summary") or "")]

    jc = state.get("jira_context") or {}
    summary_line = jc.get("summary") or state["project_key"]

    dashboard_cfg = {
        "qa_ticket": state["ticket"],
        "project": summary_line,
        "version": "",
        "description": "",
        "period_start": "",
        "period_end": "",
        "qa_plan_path": state["artifacts"].get("qa_plan"),
        "jql": jql,
        "output": str(output_path),
    }

    agg = gd.aggregate(bugs)
    html = gd.build_html(bugs, agg, dashboard_cfg)
    output_path.write_text(html, encoding="utf-8")

    print(f"[Step 7] Dashboard written to {output_path}")
    mark_step_complete(state, "dashboard")
    save_state(state, config["output"]["base_dir"])
    return state
