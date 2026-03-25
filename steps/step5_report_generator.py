"""
Step 5: Test results + QA plan → QA result report.
Claude Code reads results and generates the report interactively.
"""

import json
import os
import re
from datetime import date
from pathlib import Path

from lib.state import mark_step_complete, save_state


def read_results_summary(state: dict) -> dict:
    """Read and return test results as dict."""
    results_path = Path(state["artifacts"]["test_results"])
    if not results_path.exists():
        raise RuntimeError("Test results not found. Run step 'run' first.")
    return json.loads(results_path.read_text(encoding="utf-8"))

def _read_optional_json(path: Path) -> dict | None:
    try:
        if not path.exists():
            return None
        # rerun output might be saved via PowerShell Set-Content (UTF-8 with BOM)
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


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
    stats = results.get("stats", {}) or {}

    passed = int(stats.get("expected", 0) or 0)
    failed = int(stats.get("unexpected", 0) or 0)
    skipped = int(stats.get("skipped", 0) or 0)
    total = passed + failed + skipped

    print(f"[Step 5] Results: {passed} passed / {failed} failed / {skipped} skipped")
    print(f"[Step 5] Output path: {state['artifacts']['qa_report']}")

    ticket = state.get("ticket", "")
    jira_summary = (state.get("jira_context") or {}).get("summary", "") or ""
    project_name = state.get("project_key", "") or "N/A"
    version = "N/A"

    m = re.search(r"\b([A-Za-z][A-Za-z0-9_-]*)\s+v(\d+(?:\.\d+){0,3})\b", jira_summary)
    if m:
        project_name = m.group(1)
        version = f"v{m.group(2)}"

    def iter_failed_specs(payload: dict) -> list[dict]:
        """
        Walk Playwright JSON suites and collect failed specs with TC id inferred from parent suite titles.
        """
        failures: list[dict] = []

        def first_error(spec: dict) -> str:
            for t in spec.get("tests", []) or []:
                for r in t.get("results", []) or []:
                    errors = r.get("errors", []) or []
                    if not errors:
                        continue
                    msg = errors[0].get("message") or errors[0].get("value") or ""
                    if msg:
                        return msg
            return ""

        def walk_suite(suite: dict, tc_hint: str | None) -> None:
            title = suite.get("title") or ""
            tc = tc_hint
            m_tc = re.search(r"\b(TC-\d{3})\b", title)
            if m_tc:
                tc = m_tc.group(1)

            for child in suite.get("suites", []) or []:
                walk_suite(child, tc)

            for spec in suite.get("specs", []) or []:
                if spec.get("ok", True):
                    continue
                msg = first_error(spec)
                failures.append(
                    {
                        "tc": tc or "",
                        "title": spec.get("title", "(no title)"),
                        "file": spec.get("file", ""),
                        "line": spec.get("line", ""),
                        "reason": (msg.strip().splitlines() or ["failed"])[0][:200],
                        "raw_error": msg,
                    }
                )

        for root_suite in payload.get("suites", []) or []:
            walk_suite(root_suite, None)

        return failures

    def classify_root_cause(failure: dict) -> str:
        msg = (failure.get("raw_error") or "").lower()
        if "failed to load resource" in msg or " 403" in msg or "status of 403" in msg:
            return "외부 리소스(403)"
        if "timeout" in msg:
            return "Timeout(대기/네트워크/셀렉터)"
        if "songid url" in msg or "songid" in msg:
            return "테스트 결함(songId 로직 불일치)"
        if "expected" in msg and "received" in msg:
            return "Assertion 불일치"
        return "기타"

    _ansi_re = re.compile(r"\x1b\[[0-9;]*m")

    def sanitize_md_cell(text: str) -> str:
        s = _ansi_re.sub("", text or "")
        s = s.replace("\r", " ").replace("\n", " ").strip()
        # keep markdown tables stable
        s = s.replace("|", "\\|")
        return s[:240]

    def suggest_analysis(failure: dict) -> str:
        tc = (failure.get("tc") or "").strip()
        msg = (failure.get("raw_error") or "")
        msg_l = msg.lower()
        if tc == "TC-008" or "songid url" in msg_l:
            return "getSongId(곡명 링크) vs gotoSongDetail(곡정보 링크) songId 소스 불일치 → 기준 통일 필요"
        if tc == "TC-019" or "failed to load resource" in msg_l or "403" in msg_l:
            return "외부 리소스 403로 console.error 발생 → 필터/허용목록 또는 제품 정책 확인"
        if "timeout" in msg_l:
            return "locator/네트워크 대기 타임아웃 → 대기 조건/셀렉터 안정화 필요"
        return "-"

    def bug_judgement(failure: dict) -> tuple[str, str]:
        """
        Returns (decision, rationale).
        decision: '등록 비권장' | '조건부' | '등록 권장' | '보류'
        """
        tc = (failure.get("tc") or "").strip()
        msg_l = (failure.get("raw_error") or "").lower()

        if tc == "TC-008" or "songid url" in msg_l or "songid" in msg_l:
            return (
                "등록 비권장",
                "제품 결함 증거 부족: songId 추출/이동 기준 불일치(테스트 결함 가능). 기준 통일 후 재검증 필요",
            )

        if tc == "TC-019" or "failed to load resource" in msg_l or "403" in msg_l:
            return (
                "조건부",
                "외부/보안 정책(봇 차단, CDN, 트래킹) 가능성. 실제 사용자 영향·재현 조건 확인 후 제품 결함이면 등록",
            )

        if "timeout" in msg_l:
            return ("보류", "타임아웃은 환경/테스트 결함 가능. 재현 조건/대기 조건 정리 후 판단")

        if "expected" in msg_l and "received" in msg_l:
            return ("조건부", "Assertion 불일치: 스펙 변경/데이터 변동/제품 결함 중 무엇인지 확인 후 등록")

        return ("보류", "정보 부족: 추가 로그/증거 확보 후 판단")

    failures = iter_failed_specs(results)
    if failures:
        failures_rows = ""
        for f in failures[:30]:
            tc = f.get("tc", "") or "N/A"
            loc = f"{f['file']}:{f['line']}" if f["file"] else ""
            failures_rows += (
                f"| {sanitize_md_cell(tc)} | `{sanitize_md_cell(loc)}` | "
                f"{sanitize_md_cell(f['title'])} | {sanitize_md_cell(f['reason'] or '-')} |\n"
            )
        if len(failures) > 30:
            failures_rows += f"| - | - | (…and {len(failures) - 30} more) | - |\n"
    else:
        failures_rows = "| 해당 없음 | - | - | - |\n"

    exit_criteria = "충족" if failed == 0 else "미충족"
    release = "Go" if failed == 0 else "No-Go"
    scope_summary = f"자동화 {total}건 실행, {passed} PASS / {failed} FAIL / {skipped} SKIP"
    report_date = os.environ.get("QA_PIPELINE_REPORT_DATE", "").strip()
    today = report_date or date.today().isoformat()

    report_md = f"""---
ticket: {ticket}
project: {project_name}
version: {version}
report_date: {today}
qa_owner: N/A
---

# QA Summary Report

## 1. 개요

| 항목 | 내용 |
|------|------|
| QA 요청 티켓 | {ticket} |
| 제품 / 버전 | {project_name} / {version} |
| 보고 일자 | {today} |
| 검증 범위 요약 | {scope_summary} |

---

## 2. 테스트 범위 및 기준

- **계획서** (`output/{ticket}/qa_plan.md`) 대비 수행 범위: 부분 수행 (자동화 실행 기준)
- **Exit Criteria** 충족 여부: {exit_criteria} — 근거: 실패 {failed}건

---

## 3. 자동화 실행 결과

> 산출물: `output/{ticket}/test_results.json` (Playwright JSON reporter), 부가 산출물: `output/{ticket}/playwright/test-results/`

| 구분 | 건수 |
|------|------|
| Passed | {passed} |
| Failed | {failed} |
| Skipped | {skipped} |
| 총 실행 | {total} |

### 실패 요약

| TC | 스펙 위치 | 테스트 | 실패 원인(첫 줄) |
|---|---|---|---|
{failures_rows}

---

## 4. 결함 요약

- Step 6 (bugs) 미실행: 신규/잔여/해결 집계는 N/A

---

## 5. 품질 판정

| 항목 | 결과 |
|------|------|
| 릴리즈 권고 | {release} |
| 조건 | 실패 케이스(특히 Critical/Major) 해소 후 재실행 필요 |

---

## 6. 리스크 및 잔여 이슈

- 자동화 실패 {failed}건에 대한 원인 분석/우선순위 분류 필요(환경/데이터/제품 결함/테스트 결함).

---

## 7. 부록

- **QA 계획서**: `output/{ticket}/qa_plan.md`
- **테스트케이스**: `output/{ticket}/test_cases.md`
- **자동화 결과**: `output/{ticket}/test_results.json`
"""

    # History: 1차 원인 분석 + 2차 재테스트(실패만) 결과가 있으면 포함
    rerun_path = Path(state["artifacts"]["test_results"]).parent / "test_results_rerun.json"
    rerun = _read_optional_json(rerun_path)
    if rerun:
        rerun_stats = rerun.get("stats", {}) or {}
        rerun_failures = iter_failed_specs(rerun)
        rerun_passed = int(rerun_stats.get("expected", 0) or 0)
        rerun_failed = int(rerun_stats.get("unexpected", 0) or 0)
        rerun_skipped = int(rerun_stats.get("skipped", 0) or 0)
        rerun_total = rerun_passed + rerun_failed + rerun_skipped

        rerun_rows = ""
        if rerun_failures:
            for f in rerun_failures[:30]:
                tc = f.get("tc", "") or "N/A"
                decision, rationale = bug_judgement(f)
                rerun_rows += (
                    f"| {sanitize_md_cell(tc)} | {sanitize_md_cell(f['reason'] or '-')} | "
                    f"{sanitize_md_cell(decision)} | {sanitize_md_cell(rationale)} |\n"
                )
        else:
            rerun_rows = "| 해당 없음 | - | - | - |\n"

        history_rows = ""
        for f in failures[:30]:
            tc = f.get("tc", "") or "N/A"
            loc = f"{f['file']}:{f['line']}" if f["file"] else ""
            history_rows += (
                f"| {sanitize_md_cell(tc)} | `{sanitize_md_cell(loc)}` | {sanitize_md_cell(f['title'])} | "
                f"{sanitize_md_cell(classify_root_cause(f))} | {sanitize_md_cell(f['reason'] or '-')} | "
                f"{sanitize_md_cell(suggest_analysis(f))} |\n"
            )
        if not history_rows:
            history_rows = "| - | - | - | - | - | - |\n"

        report_md += f"""

## 8. 히스토리 (1차 실패 분석 → 2차 재테스트)

### 8.1 1차 실행(전체) 실패 원인 분석

| TC | 스펙 위치 | 테스트 | 원인 분류(초안) | 메시지(첫 줄) | 분석/조치(초안) |
|---|---|---|---|---|---|
{history_rows}

### 8.2 2차 재테스트(실패 케이스만 1회)

- 결과 파일: `output/{ticket}/test_results_rerun.json`

| 구분 | 건수 |
|------|------|
| Passed | {rerun_passed} |
| Failed | {rerun_failed} |
| Skipped | {rerun_skipped} |
| 총 실행 | {rerun_total} |

| TC | 실패 원인(첫 줄) | 버그 등록 판단 | 판단 근거 |
|---|---|---|---|
{rerun_rows}
"""

    else:
        report_md += f"""

## 8. 히스토리 (1차 실패 분석 → 2차 재테스트)

- 2차 재테스트 결과 파일이 없습니다: `output/{ticket}/test_results_rerun.json`
- Step 4가 생성한 `output/{ticket}/rerun_failed.ps1`로 실패 케이스만 1회 재실행 후, 본 섹션이 자동으로 채워지도록 합니다.
"""

    return write_report(state, config, report_md)
