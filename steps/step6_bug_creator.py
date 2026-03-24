"""
Step 6: Failed tests → Create Jira bug tickets
"""

import json
from pathlib import Path

from lib.acli import AcliClient
from lib.state import mark_step_complete, save_state

PRIORITY_TO_SEVERITY = {
    "Critical": "Critical",
    "High": "Major",
    "Medium": "Medium",
    "Low": "Minor",
}


def extract_failed_tests(test_results: dict) -> list[dict]:
    """Extract failed test specs from Playwright JSON results."""
    failed = []
    for suite in test_results.get("suites", []):
        for spec in suite.get("specs", []):
            if not spec.get("ok", True):
                error_msg = ""
                for test in spec.get("tests", []):
                    if test.get("status") in ("failed", "timedOut"):
                        err = test.get("error", {})
                        error_msg = err.get("message", "") if isinstance(err, dict) else str(err)
                        break
                failed.append(
                    {
                        "suite": suite.get("title", ""),
                        "title": spec.get("title", ""),
                        "error": error_msg,
                        "file": spec.get("file", ""),
                    }
                )
    return failed


def build_bug_description(failed: dict, ticket: str) -> str:
    return f"""*자동 생성된 버그 리포트 (QA 파이프라인)*

*QA 티켓:* {ticket}
*테스트 스위트:* {failed["suite"]}
*테스트 케이스:* {failed["title"]}

h2. 재현 단계
1. Playwright 자동화 테스트 실행
2. 테스트: {failed["title"]}

h2. 기대 결과
테스트가 정상적으로 통과해야 함

h2. 실제 결과 (오류 메시지)
{{code}}
{failed["error"][:2000]}
{{code}}

h2. 환경 정보
- 자동화 테스트 (Playwright)
- 소스 파일: {failed["file"]}
"""


def run(state: dict, config: dict) -> dict:
    print(f"[Step 6] Creating Jira bugs for failed tests in {state['ticket']}...")

    results_path = Path(state["artifacts"]["test_results"])
    if not results_path.exists():
        raise RuntimeError("Test results not found. Run step 'run' first.")

    test_results = json.loads(results_path.read_text(encoding="utf-8"))
    failed_tests = extract_failed_tests(test_results)

    if not failed_tests:
        print("[Step 6] No failed tests. No bugs to create.")
        created = []
    else:
        acli = AcliClient(config)
        created = []
        for failed in failed_tests:
            summary = f"[자동] {failed['title']}"
            description = build_bug_description(failed, state["ticket"])
            bug_key = acli.create_bug(
                project=state["project_key"],
                summary=summary,
                description=description,
                severity="Medium",
                components=[],
            )
            if bug_key:
                print(f"[Step 6] Created bug: {bug_key}")
                created.append(bug_key)

    output_path = Path(state["artifacts"]["created_bugs"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(created, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[Step 6] Created {len(created)} Jira bugs: {created}")
    mark_step_complete(state, "bugs")
    save_state(state, config["output"]["base_dir"])
    return state
