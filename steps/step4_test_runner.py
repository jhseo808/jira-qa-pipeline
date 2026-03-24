"""
Step 4: Run Playwright tests → test_results.json
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

from lib.state import mark_step_complete, save_state


def _resolve_npx() -> str:
    """Windows에서 `npx` 단독 실행이 실패하는 경우(.cmd 확장자)를 피한다."""
    return shutil.which("npx") or shutil.which("npx.cmd") or "npx"


def _playwright_test_argv(config: dict) -> list[str]:
    exe = config["playwright"].get("executable") or "npx"
    if exe == "npx":
        return [_resolve_npx(), "playwright", "test"]
    return [exe, "playwright", "test"]


def run(state: dict, config: dict) -> dict:
    print(f"[Step 4] Running Playwright tests for {state['ticket']}...")

    playwright_dir = Path(state["artifacts"]["playwright_dir"])
    if not playwright_dir.exists():
        raise RuntimeError(
            f"Playwright dir not found: {playwright_dir}. Run step 'playwright' first."
        )

    pkg_json = playwright_dir / "package.json"
    if not pkg_json.exists():
        raise RuntimeError(f"package.json not found in {playwright_dir}")

    # Install dependencies if node_modules doesn't exist
    if not (playwright_dir / "node_modules").exists():
        print("[Step 4] Installing Playwright dependencies...")
        result = subprocess.run(
            ["npm", "install"],
            cwd=str(playwright_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            print(f"[Step 4] npm install warning: {result.stderr}")

        # Install browser binary
        subprocess.run(
            [_resolve_npx(), "playwright", "install", config["playwright"]["browser"]],
            cwd=str(playwright_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    results_json_path = Path(state["artifacts"]["test_results"])
    # Playwright --output 은 산출물(스크린샷 등) 디렉터리이며 JSON 리포트 파일과 별개다.
    artifact_out = playwright_dir / "test-results"

    # Run playwright tests with JSON reporter (JSON은 기본적으로 stdout)
    cmd = _playwright_test_argv(config) + [
        "--reporter=json",
        f"--output={artifact_out}",
    ]
    # headless 가 기본; --headed=false 는 CLI에서 유효하지 않음

    print(f"[Step 4] Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=str(playwright_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PWTEST_SKIP_TEST_OUTPUT": "1"},
    )

    stdout_tail = result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout
    print(stdout_tail)
    if result.stderr:
        print(f"STDERR: {result.stderr[-1000:]}")

    # Try reading the JSON results file first
    test_results = None
    if results_json_path.exists():
        try:
            test_results = json.loads(results_json_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Fallback: parse stdout (Playwright writes JSON to stdout with --reporter=json)
    if not test_results:
        try:
            test_results = json.loads(result.stdout)
            results_json_path.parent.mkdir(parents=True, exist_ok=True)
            results_json_path.write_text(
                json.dumps(test_results, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            raw_path = results_json_path.parent / "test_results_raw.txt"
            raw_path.write_text(result.stdout, encoding="utf-8")
            test_results = {
                "stats": {"expected": 0, "unexpected": 0, "skipped": 0, "duration": 0},
                "suites": [],
                "error": f"Could not parse test results. returncode={result.returncode}",
            }
            results_json_path.parent.mkdir(parents=True, exist_ok=True)
            results_json_path.write_text(
                json.dumps(test_results, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    stats = test_results.get("stats", {})
    print(
        f"[Step 4] Results: {stats.get('expected', 0)} passed, "
        f"{stats.get('unexpected', 0)} failed, "
        f"{stats.get('skipped', 0)} skipped"
    )

    mark_step_complete(state, "run")
    save_state(state, config["output"]["base_dir"])
    return state
