"""
QA Bug Tracking Dashboard Generator
-------------------------------------
acli를 통해 Jira에서 실시간 데이터를 가져와 HTML 대시보드를 생성합니다.
어떤 제품/프로젝트에도 적용 가능합니다.

Usage:
    # 기본 (Melon v1.2.3 / PA-21 기준)
    python generate_dashboard.py

    # 다른 제품 적용 예시
    python generate_dashboard.py \\
        --qa-ticket CCS-5 \\
        --project "SmartAuth Web Portal" \\
        --version v2.0.0 \\
        --period-start 2026-04-14 \\
        --period-end 2026-04-25 \\
        --jql "project = CCS AND issuetype = 버그" \\
        --output qa_dashboard_CCS5.html
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from lib.acli import AcliClient

# Windows 터미널 UTF-8 출력 강제
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── 고정 설정 ─────────────────────────────────────────────────────────────────
DEFAULT_ACLI_PATH = str(Path(__file__).resolve().parent.parent / "AtlassianCLI" / "acli.exe")
SEVERITY_FIELD = "customfield_10058"
SEVERITY_ORDER = ["Critical", "Major", "Medium", "Minor"]
RESOLVED_STATUSES = {"완료", "Done", "Resolved", "해결됨", "Closed"}


def apply_runtime_settings(config_path: str | None = None) -> None:
    """
    Configure module-level settings from config.yaml / env vars (portable).

    Precedence:
      1) Environment overrides (already handled by lib.config.load_config for most keys)
      2) config.yaml
      3) module defaults (backward-compatible)
    """
    global ACLI, SEVERITY_FIELD, RESOLVED_STATUSES

    ACLI = os.environ.get("QA_PIPELINE_ACLI_PATH", "").strip() or DEFAULT_ACLI_PATH

    try:
        from lib.config import load_config

        # Project root = directory of this file.
        root = Path(__file__).resolve().parent
        cfg = load_config(config_path or "config.yaml", project_root=root)

        acli_cfg = cfg.get("acli") or {}
        jira_cfg = cfg.get("jira") or {}

        acli_path = (acli_cfg.get("path") or "").strip()
        if acli_path:
            ACLI = acli_path

        sev_field = (jira_cfg.get("severity_field") or "").strip()
        if sev_field:
            SEVERITY_FIELD = sev_field

        resolved = jira_cfg.get("resolved_statuses")
        if isinstance(resolved, list) and resolved:
            RESOLVED_STATUSES = set(str(x) for x in resolved if str(x).strip())
    except Exception:
        # No config or config parsing failed → keep defaults.
        pass


# Initialize settings for both CLI and Step 7 dynamic import.
apply_runtime_settings()

# ── 기능 레이블 자동 추출 키워드 ──────────────────────────────────────────────
LABEL_KEYWORDS = {
    "순위 산정": ["순위", "rank", "가중치", "weight", "점수", "score"],
    "순위 집계": ["집계", "aggregate", "합산", "중복"],
    "API 성능": ["응답 시간", "latency", "timeout", "1초", "sla", "성능"],
    "API 응답": ["응답", "response", "반환", "return", "빈 리스트", "empty"],
    "캐시": ["cache", "캐시", "ttl", "redis", "cdn"],
    "DB 성능": ["조회 속도", "query", "slow", "느려", "인덱스"],
    "데이터 정합성": ["정합성", "음수", "overflow", "오버플로", "불일치"],
    "보안/어뷰징": ["매크로", "어뷰징", "abuse", "보안", "security", "조작"],
    "UI": ["ui", "아이콘", "icon", "표시", "노출", "텍스트", "그래프", "다크모드"],
    "플레이어 연동": ["플레이어", "player", "재생", "셔플", "playlist"],
    "Fallback": ["fallback", "장애", "500", "error", "다운", "down"],
    "타입 오류": ["타입", "type", "string", "number", "파싱", "parsing"],
}


# ── acli 유틸 ─────────────────────────────────────────────────────────────────
def run_acli_json(args: list[str]) -> dict | list | None:
    cmd = [ACLI] + args + ["--json"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "LANG": "en_US.UTF-8"},
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except Exception:
        return None


def run_acli_text(args: list[str]) -> str:
    result = subprocess.run(
        [ACLI] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "LANG": "en_US.UTF-8"},
    )
    return result.stdout


# ── 티켓 분석 ─────────────────────────────────────────────────────────────────
def detect_area(summary: str, labels: list = None) -> str:
    """티켓 제목에서 영역 자동 감지. lib.acli.AcliClient.detect_area에 위임."""
    return AcliClient.detect_area(summary, labels)


def extract_labels(summary: str, jira_labels: list[str]) -> list[str]:
    """Jira 레이블 필드 + 제목 키워드 기반으로 기능 레이블 추출."""
    result = []

    # Jira 레이블 필드가 있으면 우선 사용
    if jira_labels:
        result.extend(jira_labels)

    # 제목 키워드 기반 추가
    summary_lower = summary.lower()
    for label, keywords in LABEL_KEYWORDS.items():
        if label not in result and any(k in summary_lower for k in keywords):
            result.append(label)

    return result[:4]  # 최대 4개


def fetch_bug_detail(key: str) -> dict | None:
    """개별 티켓 상세 조회 (심각도, 등록일, 상태, 레이블)"""
    raw = run_acli_json(
        [
            "jira",
            "workitem",
            "view",
            key,
            "--fields",
            f"summary,created,status,labels,{SEVERITY_FIELD}",
        ]
    )
    if not raw:
        return None
    fields = raw.get("fields", {})
    severity_obj = fields.get(SEVERITY_FIELD) or {}
    status_obj = fields.get("status") or {}
    summary = fields.get("summary", "")
    jira_labels = fields.get("labels") or []

    area = detect_area(summary, jira_labels)
    labels = extract_labels(summary, jira_labels)

    return {
        "key": raw.get("key", key),
        "summary": summary,
        "created": fields.get("created", ""),
        "status": status_obj.get("name", "해야 할 일"),
        "severity": severity_obj.get("value", "Unknown"),
        "area": area,
        "labels": labels,
    }


def fetch_ticket_keys(jql: str, project_key: str) -> list[str]:
    """JQL로 티켓 키 목록 조회"""
    text = run_acli_text(["jira", "workitem", "search", "--jql", jql, "--limit", "200"])
    pattern = rf"{re.escape(project_key)}-\d+"
    keys = re.findall(pattern, text)
    return list(dict.fromkeys(keys))  # 중복 제거, 순서 유지


# ── 집계 ──────────────────────────────────────────────────────────────────────
def aggregate(bugs: list[dict]) -> dict:
    sev_count = defaultdict(int)
    area_sev = defaultdict(lambda: defaultdict(int))
    label_count = defaultdict(int)
    daily_reg = defaultdict(int)
    resolved = 0

    for b in bugs:
        sev = b["severity"]
        area = b["area"]

        sev_count[sev] += 1
        area_sev[area][sev] += 1

        for lbl in b["labels"]:
            label_count[lbl] += 1

        dt_str = b["created"][:10] if b["created"] else "unknown"
        daily_reg[dt_str] += 1

        if b["status"] in RESOLVED_STATUSES:
            resolved += 1

    total = len(bugs)
    return {
        "total": total,
        "resolved": resolved,
        "open": total - resolved,
        "rate": round(resolved / total * 100) if total else 0,
        "sev_count": dict(sev_count),
        "area_sev": {k: dict(v) for k, v in area_sev.items()},
        "label_count": dict(label_count),
        "daily_reg": dict(sorted(daily_reg.items())),
    }


# ── HTML 렌더링 헬퍼 ──────────────────────────────────────────────────────────
def label_badges(labels: list[str]) -> str:
    return "".join(f'<span class="label">{label}</span>' for label in labels)


def sev_badge(sev: str) -> str:
    cls = {"Critical": "critical", "Major": "major", "Medium": "medium", "Minor": "minor"}.get(
        sev, "minor"
    )
    return f'<span class="sev sev-{cls}">{sev}</span>'


def render_bug_row(b: dict, border_color: str = "var(--critical)") -> str:
    dt = b["created"][:16].replace("T", " ") if b["created"] else ""
    return f"""
      <div class="bug-item" style="border-left-color:{border_color}">
        <div class="bug-item-header">
          <span class="bug-key">{b["key"]}</span>
          {sev_badge(b["severity"])}
          {label_badges(b["labels"])}
          <span class="label area-label">{b["area"]}</span>
        </div>
        <div class="bug-title">{b["summary"]}</div>
        <div class="bug-meta">📅 {dt} · 영역: {b["area"]}</div>
      </div>"""


def compact_row(b: dict) -> str:
    return f"""
        <div class="compact-item">
          <span class="compact-key">{b["key"]}</span>
          <div>
            <div class="compact-title">{b["summary"]}</div>
            {label_badges(b["labels"])}
            <span class="label area-label">{b["area"]}</span>
          </div>
        </div>"""


# ── QA 기간 날짜 축 생성 (주말 제외) ─────────────────────────────────────────
def build_qa_dates(start: str, end: str) -> list[str]:
    """검증 기간 내 평일 날짜 목록 생성 (M/D 형식)"""
    isos = build_qa_weekday_isos(start, end)
    return [_iso_to_md_label(iso) for iso in isos]


def build_qa_weekday_isos(start: str, end: str) -> list[str]:
    """검증 기간 내 평일만 ISO 날짜(YYYY-MM-DD) 목록."""
    try:
        s = datetime.strptime(start, "%Y-%m-%d")
        e = datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        return []
    out: list[str] = []
    cur = s
    while cur <= e:
        if cur.weekday() < 5:
            out.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=1)
    return out


def _iso_to_md_label(iso: str) -> str:
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.month}/{d.day}"


def parse_qa_period_from_plan(plan_path: str | Path) -> tuple[str, str]:
    """qa_plan.md 등에서 '총 검증 기간: YYYY-MM-DD ~ YYYY-MM-DD' 파싱."""
    p = Path(plan_path)
    if not p.is_file():
        return "", ""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "", ""
    m = re.search(
        r"총\s*검증\s*기간:\s*(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})",
        text,
    )
    if m:
        return m.group(1), m.group(2)
    return "", ""


def infer_period_bounds_from_bugs(bugs: list[dict]) -> tuple[str, str]:
    """버그 created 기준 최소·최대 일자 (검증 기간 미설정 시 차트 축용)."""
    isos = []
    for b in bugs:
        c = (b.get("created") or "")[:10]
        if len(c) == 10 and c[4] == "-" and c[7] == "-":
            isos.append(c)
    if not isos:
        today = datetime.now().strftime("%Y-%m-%d")
        return today, today
    return min(isos), max(isos)


def earliest_bug_iso(bugs: list[dict]) -> str | None:
    """가장 이른 등록일 (YYYY-MM-DD)."""
    isos = []
    for b in bugs:
        c = (b.get("created") or "")[:10]
        if len(c) == 10 and c[4] == "-" and c[7] == "-":
            isos.append(c)
    return min(isos) if isos else None


def cumulative_count_upto_date(daily_map: dict[str, int], upto_iso: str) -> int:
    """해당 일(포함)까지 일별 등록 건수 합산. 주말 등 축에 없는 날짜도 반영."""
    try:
        u = datetime.strptime(upto_iso, "%Y-%m-%d").date()
    except ValueError:
        return 0
    total = 0
    for k, v in daily_map.items():
        if k == "unknown" or not isinstance(v, int):
            continue
        try:
            if datetime.strptime(k, "%Y-%m-%d").date() <= u:
                total += v
        except ValueError:
            continue
    return total


def count_resolved_filed_upto(bugs: list[dict], upto_iso: str) -> int:
    """해당 일(포함)까지 등록된 이슈 중 현재 해결 상태인 건수(누적 해결 곡선용)."""
    try:
        u = datetime.strptime(upto_iso, "%Y-%m-%d").date()
    except ValueError:
        return 0
    n = 0
    for b in bugs:
        if b.get("status") not in RESOLVED_STATUSES:
            continue
        c = (b.get("created") or "")[:10]
        try:
            if datetime.strptime(c, "%Y-%m-%d").date() <= u:
                n += 1
        except ValueError:
            continue
    return n


# ── HTML 생성 ─────────────────────────────────────────────────────────────────
def build_html(bugs: list[dict], agg: dict, cfg: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    project_name = cfg["project"]
    version = cfg["version"]
    qa_ticket = cfg["qa_ticket"]
    period_start = (cfg.get("period_start") or "").strip()
    period_end = (cfg.get("period_end") or "").strip()
    description = cfg.get("description", "QA 검증")

    if not period_start or not period_end:
        ps, pe = parse_qa_period_from_plan(cfg.get("qa_plan_path") or "")
        if ps and pe:
            period_start, period_end = ps, pe
    if not period_start or not period_end:
        period_start, period_end = infer_period_bounds_from_bugs(bugs)

    # ── 차트 데이터 ────────────────────────────────────────────────────────────
    sev_vals = [agg["sev_count"].get(s, 0) for s in SEVERITY_ORDER]

    areas = sorted(agg["area_sev"].keys()) or ["Web", "API", "Engine", "DB"]
    colors = {"Critical": "#ff4d6d", "Major": "#ff9f43", "Medium": "#54a0ff", "Minor": "#1dd1a1"}
    area_datasets = [
        {
            "label": sev,
            "data": [agg["area_sev"].get(a, {}).get(sev, 0) for a in areas],
            "backgroundColor": colors[sev],
            "borderRadius": 3,
        }
        for sev in SEVERITY_ORDER
    ]

    label_sorted = sorted(agg["label_count"].items(), key=lambda x: -x[1])[:10]
    label_names = [x[0] for x in label_sorted]
    label_vals = [x[1] for x in label_sorted]

    # 날짜별 누적 추이: 검증 기간 전에 등록된 이슈도 보이도록 축 시작을 당김
    trend_start = period_start
    eb = earliest_bug_iso(bugs)
    if eb:
        trend_start = min(trend_start, eb)
    trend_end = period_end

    qa_dates = build_qa_dates(trend_start, trend_end)
    period_iso_dates = build_qa_weekday_isos(trend_start, trend_end)
    daily_map = agg["daily_reg"]

    trend_reg = [cumulative_count_upto_date(daily_map, iso) for iso in period_iso_dates]

    resolved_bugs = [b for b in bugs if b["status"] in RESOLVED_STATUSES]
    trend_res = [count_resolved_filed_upto(resolved_bugs, iso) for iso in period_iso_dates]

    # ── 리스트 렌더링 ──────────────────────────────────────────────────────────
    critical_open = [
        b for b in bugs if b["severity"] == "Critical" and b["status"] not in RESOLVED_STATUSES
    ]
    critical_rows = "".join(render_bug_row(b, "#ff4d6d") for b in critical_open)
    medium_rows = "".join(compact_row(b) for b in bugs if b["severity"] == "Medium")
    minor_rows = "".join(compact_row(b) for b in bugs if b["severity"] == "Minor")
    medium_cnt = agg["sev_count"].get("Medium", 0)
    minor_cnt = agg["sev_count"].get("Minor", 0)
    critical_cnt = len(critical_open)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QA Bug Tracking Dashboard — {project_name} {version}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg:#0f1117;--surface:#1a1d27;--surface2:#22263a;--border:#2e3347;
    --text:#e2e8f0;--text-muted:#8892a4;
    --critical:#ff4d6d;--major:#ff9f43;--medium:#54a0ff;--minor:#1dd1a1;
    --resolved:#26de81;--accent:#a78bfa;
  }}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--text);font-family:'Segoe UI','Apple SD Gothic Neo',sans-serif;font-size:14px;}}
  .header{{background:linear-gradient(135deg,#1a1d27,#16213e);border-bottom:1px solid var(--border);padding:20px 32px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;}}
  .header-left h1{{font-size:20px;font-weight:700;color:#fff;}}
  .header-left p{{color:var(--text-muted);font-size:12px;margin-top:4px;}}
  .badge-version{{background:var(--accent);color:#fff;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;}}
  .header-right{{display:flex;gap:12px;align-items:center;flex-wrap:wrap;}}
  .qa-period,.updated{{color:var(--text-muted);font-size:12px;}}
  .container{{padding:24px 32px;}}
  .grid-4{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px;}}
  .grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;}}
  .grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px;}}
  .card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px;}}
  .card-title{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.8px;color:var(--text-muted);margin-bottom:12px;}}
  .stat-card{{text-align:center;position:relative;overflow:hidden;}}
  .stat-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;}}
  .stat-total::before{{background:var(--accent);}} .stat-open::before{{background:var(--critical);}}
  .stat-resolved::before{{background:var(--resolved);}} .stat-rate::before{{background:var(--minor);}}
  .stat-num{{font-size:42px;font-weight:800;line-height:1;margin-bottom:6px;}}
  .stat-label{{font-size:12px;color:var(--text-muted);}}
  .stat-total .stat-num{{color:var(--accent);}} .stat-open .stat-num{{color:var(--critical);}}
  .stat-resolved .stat-num{{color:var(--resolved);}} .stat-rate .stat-num{{color:var(--minor);font-size:36px;}}
  .sev{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;}}
  .sev-critical{{background:rgba(255,77,109,.18);color:var(--critical);border:1px solid rgba(255,77,109,.3);}}
  .sev-major{{background:rgba(255,159,67,.15);color:var(--major);border:1px solid rgba(255,159,67,.3);}}
  .sev-medium{{background:rgba(84,160,255,.15);color:var(--medium);border:1px solid rgba(84,160,255,.3);}}
  .sev-minor{{background:rgba(29,209,161,.12);color:var(--minor);border:1px solid rgba(29,209,161,.25);}}
  .label{{display:inline-block;padding:2px 7px;border-radius:4px;font-size:10px;font-weight:600;background:var(--surface2);color:var(--text-muted);border:1px solid var(--border);margin-right:4px;margin-bottom:2px;}}
  .area-label{{color:#a78bfa;border-color:rgba(167,139,250,.3);background:rgba(167,139,250,.08);}}
  .chart-wrap{{position:relative;}}
  .bug-list{{display:flex;flex-direction:column;gap:10px;}}
  .bug-item{{background:var(--surface2);border:1px solid var(--border);border-left:3px solid var(--critical);border-radius:8px;padding:12px 14px;}}
  .bug-item-header{{display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap;}}
  .bug-key{{font-size:12px;font-weight:700;color:var(--accent);}}
  .bug-title{{font-size:13px;color:var(--text);line-height:1.4;margin-bottom:6px;}}
  .bug-meta{{font-size:11px;color:var(--text-muted);}}
  .sev-row{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;}}
  .sev-chip{{flex:1;min-width:80px;background:var(--surface2);border-radius:8px;padding:10px;text-align:center;border:1px solid var(--border);}}
  .sev-chip .num{{font-size:24px;font-weight:800;}} .sev-chip .lbl{{font-size:10px;color:var(--text-muted);margin-top:2px;}}
  .sev-chip.c .num{{color:var(--critical);}} .sev-chip.ma .num{{color:var(--major);}}
  .sev-chip.me .num{{color:var(--medium);}} .sev-chip.mi .num{{color:var(--minor);}}
  .section-title{{font-size:13px;font-weight:700;color:var(--text);margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px;flex-wrap:wrap;}}
  .section-title span{{font-size:10px;font-weight:500;color:var(--text-muted);}}
  .compact-list{{display:flex;flex-direction:column;gap:6px;}}
  .compact-item{{background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:9px 12px;display:flex;align-items:flex-start;gap:10px;flex-wrap:wrap;}}
  .compact-key{{font-size:11px;font-weight:700;color:var(--accent);white-space:nowrap;}}
  .compact-title{{font-size:12px;color:var(--text);margin-bottom:4px;}}
  .progress-bar-wrap{{height:6px;background:var(--surface2);border-radius:3px;overflow:hidden;margin-top:6px;}}
  .progress-bar{{height:100%;border-radius:3px;}}
  .empty-state{{color:var(--text-muted);font-size:12px;padding:20px;text-align:center;}}
  @media(max-width:900px){{.grid-4,.grid-3{{grid-template-columns:repeat(2,1fr);}}.grid-2{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<div class="header">
  <div class="header-left">
    <h1>🐛 {project_name} — QA Bug Tracking Dashboard</h1>
    <p>{qa_ticket} | {description}</p>
  </div>
  <div class="header-right">
    <span class="qa-period">검증 기간: {period_start} ~ {period_end}</span>
    <span class="updated">업데이트: {now}</span>
    <span class="badge-version">{version}</span>
  </div>
</div>
<div class="container">

  <div class="grid-4">
    <div class="card stat-card stat-total"><div class="stat-num">{agg["total"]}</div><div class="stat-label">전체 등록 이슈</div></div>
    <div class="card stat-card stat-open"><div class="stat-num">{agg["open"]}</div><div class="stat-label">잔여 (미해결)</div></div>
    <div class="card stat-card stat-resolved"><div class="stat-num">{agg["resolved"]}</div><div class="stat-label">해결 완료</div></div>
    <div class="card stat-card stat-rate">
      <div class="stat-num">{agg["rate"]}%</div><div class="stat-label">해결률</div>
      <div class="progress-bar-wrap" style="margin-top:10px;"><div class="progress-bar" style="width:{agg["rate"]}%;background:var(--resolved);"></div></div>
    </div>
  </div>

  <div class="card" style="margin-bottom:20px;">
    <div class="card-title">심각도 분포</div>
    <div class="sev-row">
      <div class="sev-chip c"><div class="num">{agg["sev_count"].get("Critical", 0)}</div><div class="lbl">Critical</div></div>
      <div class="sev-chip ma"><div class="num">{agg["sev_count"].get("Major", 0)}</div><div class="lbl">Major</div></div>
      <div class="sev-chip me"><div class="num">{agg["sev_count"].get("Medium", 0)}</div><div class="lbl">Medium</div></div>
      <div class="sev-chip mi"><div class="num">{agg["sev_count"].get("Minor", 0)}</div><div class="lbl">Minor</div></div>
    </div>
  </div>

  <div class="grid-3">
    <div class="card"><div class="card-title">심각도별 이슈 비율</div>
      <div class="chart-wrap" style="height:220px;display:flex;align-items:center;justify-content:center;">
        <canvas id="chartSeverity"></canvas></div></div>
    <div class="card"><div class="card-title">영역별 이슈 분포</div>
      <div class="chart-wrap" style="height:220px;"><canvas id="chartArea"></canvas></div></div>
    <div class="card"><div class="card-title">기능 레이블별 이슈</div>
      <div class="chart-wrap" style="height:220px;"><canvas id="chartLabel"></canvas></div></div>
  </div>

  <div class="grid-2">
    <div class="card"><div class="card-title">날짜별 누적 등록 / 해결 추이</div>
      <div class="chart-wrap" style="height:200px;"><canvas id="chartTrend"></canvas></div></div>
    <div class="card"><div class="card-title">영역 × 심각도 교차 분포</div>
      <div class="chart-wrap" style="height:200px;"><canvas id="chartCross"></canvas></div></div>
  </div>

  <div class="card" style="margin-bottom:20px;">
    <div class="section-title">🔴 미해결 Critical 이슈 <span>— Exit Criteria 충족 필요 ({critical_cnt}건)</span></div>
    <div class="bug-list">{critical_rows if critical_rows else '<div class="empty-state">미해결 Critical 이슈 없음 ✓</div>'}</div>
  </div>

  <div class="grid-2">
    <div class="card">
      <div class="section-title">🔵 Medium 이슈 <span>{medium_cnt}건</span></div>
      <div class="compact-list">{medium_rows if medium_rows else '<div class="empty-state">없음</div>'}</div>
    </div>
    <div class="card">
      <div class="section-title">🟢 Minor 이슈 <span>{minor_cnt}건</span></div>
      <div class="compact-list">{minor_rows if minor_rows else '<div class="empty-state">없음</div>'}</div>
    </div>
  </div>

</div>
<script>
Chart.defaults.color='#8892a4';
Chart.defaults.borderColor='#2e3347';
Chart.defaults.font.family="'Segoe UI','Apple SD Gothic Neo',sans-serif";
const C={{critical:'#ff4d6d',major:'#ff9f43',medium:'#54a0ff',minor:'#1dd1a1',resolved:'#26de81'}};

new Chart(document.getElementById('chartSeverity'),{{
  type:'doughnut',
  data:{{labels:{json.dumps(SEVERITY_ORDER)},datasets:[{{data:{json.dumps(sev_vals)},
    backgroundColor:[C.critical,C.major,C.medium,C.minor],borderWidth:2,borderColor:'#1a1d27',hoverOffset:6}}]}},
  options:{{responsive:true,maintainAspectRatio:false,cutout:'65%',
    plugins:{{legend:{{position:'bottom',labels:{{boxWidth:10,padding:12,font:{{size:11}}}}}},
      tooltip:{{callbacks:{{label:ctx=>` ${{ctx.label}}: ${{ctx.parsed}}건`}}}}}}}}
}});

new Chart(document.getElementById('chartArea'),{{
  type:'bar',
  data:{{labels:{json.dumps(areas)},datasets:{json.dumps(area_datasets)}}},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{stacked:true,grid:{{display:false}}}},y:{{stacked:true,ticks:{{stepSize:1}}}}}},
    plugins:{{legend:{{position:'bottom',labels:{{boxWidth:10,padding:8,font:{{size:10}}}}}}}}}}
}});

new Chart(document.getElementById('chartLabel'),{{
  type:'bar',
  data:{{labels:{json.dumps(label_names)},datasets:[{{label:'이슈 수',data:{json.dumps(label_vals)},
    backgroundColor:'#a78bfa',borderRadius:4}}]}},
  options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,
    scales:{{x:{{ticks:{{stepSize:1}},grid:{{color:'#2e3347'}}}},y:{{grid:{{display:false}},ticks:{{font:{{size:11}}}}}}}},
    plugins:{{legend:{{display:false}}}}}}
}});

new Chart(document.getElementById('chartTrend'),{{
  type:'line',
  data:{{labels:{json.dumps(qa_dates)},datasets:[
    {{label:'누적 등록',data:{json.dumps(trend_reg)},borderColor:C.critical,backgroundColor:'rgba(255,77,109,0.1)',fill:true,tension:.3,pointRadius:4,spanGaps:false}},
    {{label:'누적 해결',data:{json.dumps(trend_res)},borderColor:C.resolved,backgroundColor:'rgba(38,222,129,0.08)',fill:true,tension:.3,pointRadius:4,borderDash:[4,4],spanGaps:false}}
  ]}},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{grid:{{color:'#2e3347'}}}},y:{{min:0,ticks:{{stepSize:5}},grid:{{color:'#2e3347'}}}}}},
    plugins:{{legend:{{position:'bottom',labels:{{boxWidth:10,padding:10,font:{{size:11}}}}}},tooltip:{{mode:'index',intersect:false}}}}}}
}});

new Chart(document.getElementById('chartCross'),{{
  type:'bar',
  data:{{labels:{json.dumps(areas)},datasets:{json.dumps(area_datasets)}}},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{x:{{grid:{{display:false}}}},y:{{ticks:{{stepSize:1}},grid:{{color:'#2e3347'}}}}}},
    plugins:{{legend:{{position:'bottom',labels:{{boxWidth:10,padding:8,font:{{size:10}}}}}}}}}}
}});
</script>
</body>
</html>"""


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="QA Bug Tracking Dashboard Generator")
    parser.add_argument(
        "--config",
        default=None,
        help="설정 파일 경로 (기본: ./config.yaml 또는 env QA_PIPELINE_CONFIG)",
    )
    parser.add_argument("--qa-ticket", default="PA-21", help="QA 요청 티켓 키 (예: PA-21, CCS-5)")
    parser.add_argument("--project", default="Melon Chart TOP100", help="제품명")
    parser.add_argument("--version", default="v1.2.3", help="버전")
    parser.add_argument(
        "--description", default="Chart DB 변경 및 순위 로직 수정 검증", help="검증 설명"
    )
    parser.add_argument("--period-start", default="2026-03-26", help="검증 시작일 (YYYY-MM-DD)")
    parser.add_argument("--period-end", default="2026-04-09", help="검증 종료일 (YYYY-MM-DD)")
    parser.add_argument("--jql", default=None, help="JQL (미입력 시 자동 생성)")
    parser.add_argument("--output", default=None, help="출력 파일명 (미입력 시 자동 생성)")
    args = parser.parse_args()

    if args.config:
        apply_runtime_settings(args.config)

    # 프로젝트 키 추출 (PA-21 → PA)
    project_key = re.match(r"^([A-Z]+)-\d+", args.qa_ticket)
    project_key = project_key.group(1) if project_key else "PA"

    # JQL 자동 생성
    jql = args.jql or f"project = {project_key} AND issuetype = 버그 ORDER BY created ASC"

    # 출력 파일명 자동 생성
    output_name = args.output or f"qa_dashboard_{args.qa_ticket.replace('-', '')}.html"
    output_path = Path(__file__).parent / output_name

    cfg = {
        "qa_ticket": args.qa_ticket,
        "project": args.project,
        "version": args.version,
        "description": args.description,
        "period_start": args.period_start,
        "period_end": args.period_end,
    }

    print(f"[1/3] 티켓 목록 조회 (JQL: {jql})")
    keys = fetch_ticket_keys(jql, project_key)
    if not keys:
        print("[error] 티켓을 찾지 못했습니다. JQL 또는 acli 인증을 확인하세요.", file=sys.stderr)
        sys.exit(1)
    print(f"  → {len(keys)}개 발견: {', '.join(keys)}")

    print("[2/3] 각 티켓 상세 조회 중...")
    bugs = []
    for key in keys:
        detail = fetch_bug_detail(key)
        if detail:
            bugs.append(detail)
            print(
                f"  OK {key} [{detail['severity']}] [{detail['area']}] {detail['summary'][:35]}..."
            )

    if not bugs:
        print("[error] 데이터 없음.", file=sys.stderr)
        sys.exit(1)

    print("[3/3] HTML 생성 중...")
    agg = aggregate(bugs)
    html = build_html(bugs, agg, cfg)
    output_path.write_text(html, encoding="utf-8")

    print(f"\n완료: {output_path}")
    print(
        f"  전체: {agg['total']} | 미해결: {agg['open']} | 해결: {agg['resolved']} | 해결률: {agg['rate']}%"
    )
    print(f"  영역: {', '.join(f'{k}({sum(v.values())})' for k, v in agg['area_sev'].items())}")


if __name__ == "__main__":
    main()
