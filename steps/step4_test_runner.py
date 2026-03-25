"""
Step 4: Run Playwright tests → test_results.json
"""

import json
import os
import re
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


def _extract_failed_specs(results: dict) -> list[dict]:
    """
    Return list of failed specs with best-effort TC id (from parent suite title).
    Each item: {tc, file, line, title, first_error_line}
    """
    failed: list[dict] = []

    def first_error(spec: dict) -> str:
        for t in spec.get("tests", []) or []:
            for r in t.get("results", []) or []:
                errs = r.get("errors") or []
                if errs:
                    msg = errs[0].get("message") or errs[0].get("value") or ""
                    if msg:
                        return (msg.splitlines() or [""])[0]
        return ""

    def walk_suite(suite: dict, tc_hint: str | None) -> None:
        title = suite.get("title") or ""
        tc = tc_hint
        m = re.search(r"\b(TC-\d{3})\b", title)
        if m:
            tc = m.group(1)

        for child in suite.get("suites", []) or []:
            walk_suite(child, tc)

        for spec in suite.get("specs", []) or []:
            if spec.get("ok", True):
                continue
            failed.append(
                {
                    "tc": tc or "",
                    "file": spec.get("file", "") or "",
                    "line": spec.get("line", "") or "",
                    "title": spec.get("title", "") or "",
                    "first_error_line": first_error(spec),
                }
            )

    for root in results.get("suites", []) or []:
        walk_suite(root, None)

    return failed


def _parse_int(value, default=None) -> int | None:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        s = str(value).strip()
        if not s:
            return default
        return int(s)
    except Exception:
        return default


def _parse_bool(value, default: bool | None = None) -> bool | None:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if not s:
        return default
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    return default


def _slow_tests_summary(results: dict, limit: int = 5) -> list[tuple[int, str, str]]:
    rows: list[tuple[int, str, str]] = []

    def walk_suite(suite: dict, file_hint: str | None = None) -> None:
        file_hint = suite.get("file") or file_hint
        for child in suite.get("suites", []) or []:
            walk_suite(child, file_hint)
        for spec in suite.get("specs", []) or []:
            file = spec.get("file") or file_hint or ""
            for t in spec.get("tests", []) or []:
                title = t.get("title") or spec.get("title") or ""
                for r in t.get("results", []) or []:
                    dur = r.get("duration") or 0
                    rows.append((int(dur), str(file), str(title)))

    for root in results.get("suites", []) or []:
        walk_suite(root, None)

    rows.sort(key=lambda x: x[0], reverse=True)
    return rows[: max(0, int(limit))]


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

    # Optional speed/debug controls (CLI overrides without editing playwright.config.ts)
    pw_cfg = (config.get("playwright") or {}) if isinstance(config, dict) else {}
    workers = _parse_int(pw_cfg.get("workers"))
    fully_parallel = _parse_bool(pw_cfg.get("fully_parallel"))
    max_failures = _parse_int(pw_cfg.get("max_failures"))
    test_timeout_ms = _parse_int(pw_cfg.get("test_timeout_ms"))

    if fully_parallel is True:
        cmd.append("--fully-parallel")
    if workers and workers > 0:
        cmd.append(f"--workers={workers}")
    if max_failures is not None and max_failures > 0:
        cmd.append(f"--max-failures={max_failures}")
    if test_timeout_ms and test_timeout_ms > 0:
        cmd.append(f"--timeout={test_timeout_ms}")
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

    # Prefer parsing stdout (Playwright writes JSON to stdout with --reporter=json)
    test_results = None
    if (result.stdout or "").strip():
        try:
            test_results = json.loads(result.stdout)
            results_json_path.parent.mkdir(parents=True, exist_ok=True)
            results_json_path.write_text(
                json.dumps(test_results, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            test_results = None

    # Fallback: read existing results file (if any)
    if not test_results:
        if results_json_path.exists():
            try:
                test_results = json.loads(results_json_path.read_text(encoding="utf-8"))
            except Exception:
                test_results = None

    # Final fallback: write an error payload
    if not test_results:
        raw_path = results_json_path.parent / "test_results_raw.txt"
        results_json_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(result.stdout or "", encoding="utf-8")
        test_results = {
            "stats": {"expected": 0, "unexpected": 0, "skipped": 0, "duration": 0},
            "suites": [],
            "error": f"Could not parse test results. returncode={result.returncode}",
        }
        results_json_path.write_text(
            json.dumps(test_results, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    stats = test_results.get("stats", {}) or {}
    print(
        f"[Step 4] Results: {stats.get('expected', 0)} passed, "
        f"{stats.get('unexpected', 0)} failed, "
        f"{stats.get('skipped', 0)} skipped"
    )

    # Quick perf hints: show slowest tests (best-effort)
    try:
        slow = _slow_tests_summary(test_results, limit=5)
        if slow:
            print("[Step 4] Slowest tests (top 5):")
            for dur, file, title in slow:
                file_short = Path(file).name if file else ""
                print(f"  - {dur}ms {file_short} :: {title}")
    except Exception:
        pass

    # Write helpers for "re-run failed only once" workflow (docs-driven, low overhead)
    try:
        failed_specs = _extract_failed_specs(test_results)
        if failed_specs:
            out_dir = results_json_path.parent
            out_dir.mkdir(parents=True, exist_ok=True)

            failed_list_path = out_dir / "failed_tests.txt"
            selectors: list[str] = []
            lines: list[str] = []

            for f in failed_specs:
                file = (f.get("file") or "").strip()
                line = str(f.get("line") or "").strip()
                tc = (f.get("tc") or "").strip()
                title = (f.get("title") or "").strip()
                first = (f.get("first_error_line") or "").strip()
                sel = f"tests/{file}:{line}" if file and line else ""
                if sel:
                    selectors.append(sel)
                lines.append(f"- {tc or 'N/A':7} {sel or 'N/A':28} | {title} | {first}")

            failed_list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            if selectors:
                rerun_out_dir = playwright_dir / "test-results-rerun"
                rerun_results_path = out_dir / "test_results_rerun.json"
                rerun_script_path = out_dir / "rerun_failed.ps1"
                selector_args = " ".join(f"\"{s}\"" for s in selectors)
                rerun_script_path.write_text(
                    "\n".join(
                        [
                            "# Re-run failed Playwright specs once (generated by Step 4)",
                            f"Set-Location \"{playwright_dir}\"",
                            f"npx playwright test {selector_args} --reporter=json --output=\"{rerun_out_dir}\" | Set-Content -Encoding utf8 \"{rerun_results_path}\"",
                        ]
                    )
                    + "\n",
                    encoding="utf-8",
                )
                print(f"[Step 4] Failed list:  {failed_list_path}")
                print(f"[Step 4] Re-run script: {rerun_script_path}")
    except Exception:
        # best-effort only
        pass

    # If Playwright itself failed to execute (e.g., spawn error), don't mark the step as complete.
    if result.returncode != 0 and test_results.get("error") and not test_results.get("suites"):
        raise RuntimeError(
            "Playwright execution failed (no runnable results). "
            f"returncode={result.returncode}. "
            f"stderr_tail={result.stderr[-300:] if result.stderr else ''}"
        )

    mark_step_complete(state, "run")
    save_state(state, config["output"]["base_dir"])
    return state
