"""
Step 7: Generate bug tracking dashboard (reuses generate_dashboard.py logic)
"""

from pathlib import Path

import generate_dashboard as gd
from lib.acli import AcliClient
from lib.jira_rest import JiraRestClient
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

    jira_cfg = config.get("jira") or {}
    issue_type_cfg = (jira_cfg.get("bug_issue_type") or "Bug").strip()
    issue_type_candidates: list[str] = []
    for v in (issue_type_cfg, "Bug", "버그"):
        if v and v not in issue_type_candidates:
            issue_type_candidates.append(v)

    output_path = Path(state["artifacts"]["dashboard"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    acli = AcliClient(config)

    selected_issue_type = issue_type_candidates[0] if issue_type_candidates else "Bug"
    keys: list[str] = []
    jql = ""
    last_error: Exception | None = None
    for it in issue_type_candidates:
        jql = (
            f'project = {state["project_key"]} AND issuetype = "{it}" {jql_suffix} '
            "ORDER BY created ASC"
        )
        jql = " ".join(jql.split())
        try:
            keys = acli.search_issues_checked(jql, state["project_key"])
        except Exception as e:
            last_error = e
            msg = str(e).lower()
            # If acli isn't authenticated (OAuth), fall back to Jira REST API using token.txt.
            if "unauthorized" in msg or "auth login" in msg:
                break
            raise RuntimeError(
                "Step 7 must fetch Jira issues, but the Jira CLI query failed.\n"
                "- Verify your JQL / project key / issue type name.\n"
                f"Details: {e}"
            ) from e
        if keys:
            selected_issue_type = it
            break

    # Fallback: Jira REST API (token.txt) when acli is unauthorized.
    if not keys and last_error and ("unauthorized" in str(last_error).lower()):
        jira = JiraRestClient.from_config(config)
        fields = [
            "summary",
            "created",
            "status",
            "labels",
            (jira_cfg.get("severity_field") or "").strip(),
        ]
        fields = [f for f in fields if f]

        issues_payload: list[dict] = []
        for it in issue_type_candidates:
            jql = (
                f'project = {state["project_key"]} AND issuetype = "{it}" {jql_suffix} '
                "ORDER BY created ASC"
            )
            jql = " ".join(jql.split())
            try:
                issues_payload = jira.search_issues(jql, fields=fields, max_results=200)
            except Exception as e:
                raise RuntimeError(
                    "Step 7 Jira REST fetch failed.\n"
                    f"- Jira site: {config.get('acli', {}).get('site')}\n"
                    "- Check network/VPN/firewall/proxy that blocks atlassian.net:443.\n"
                    f"Details: {e}"
                ) from e
            if issues_payload:
                selected_issue_type = it
                keys = [i.get("key") for i in issues_payload if i.get("key")]
                break

        # Build bug objects from search payload (single round-trip)
        bugs: list[dict] = []
        for issue in issues_payload:
            k = issue.get("key") or ""
            f = issue.get("fields") or {}
            summary = f.get("summary") or ""
            status_obj = f.get("status") or {}
            severity_obj = f.get((jira_cfg.get("severity_field") or "").strip()) or {}
            jira_labels = f.get("labels") or []
            bugs.append(
                {
                    "key": k,
                    "summary": summary,
                    "created": f.get("created") or "",
                    "status": status_obj.get("name") or "",
                    "severity": severity_obj.get("value") or "Unknown",
                    "area": gd.detect_area(summary, jira_labels),
                    "labels": gd.extract_labels(summary, jira_labels),
                }
            )

        if summary_kw:
            bugs = [b for b in bugs if summary_kw in (b.get("summary") or "")]

    elif not keys:
        print(
            "[Step 7] Warning: no Jira issues matched the dashboard JQL. "
            f"Checked issuetype candidates={issue_type_candidates}. "
            "If your Jira issue type name differs, set jira.bug_issue_type in config.local.yaml."
        )
        bugs = []

    # Normal path: acli is authenticated and returned keys.
    if keys:
        bugs = []
        for k in keys:
            raw = acli.get_issue_detail(k)
            if not raw:
                continue
            summary = raw.get("summary") or ""
            jira_labels = raw.get("labels") or []
            bugs.append(
                {
                    "key": raw.get("key") or k,
                    "summary": summary,
                    "created": raw.get("created") or "",
                    "status": raw.get("status") or "",
                    "severity": raw.get("severity") or "Unknown",
                    "area": gd.detect_area(summary, jira_labels),
                    "labels": gd.extract_labels(summary, jira_labels),
                }
            )

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
        "jql": jql or f'project = {state["project_key"]} AND issuetype = "{selected_issue_type}"',
        "output": str(output_path),
    }

    agg = gd.aggregate(bugs)
    html = gd.build_html(bugs, agg, dashboard_cfg)
    output_path.write_text(html, encoding="utf-8")

    print(f"[Step 7] Dashboard written to {output_path}")
    mark_step_complete(state, "dashboard")
    save_state(state, config["output"]["base_dir"])
    return state
