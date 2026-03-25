"""
Step 3: Analyze target page with playwright-cli → Claude Code generates POM tests.

Workflow:
  1. playwright-cli open + snapshot → DOM structure for Claude Code to analyze
  2. Claude Code generates POM TypeScript test files
  3. write_playwright_files() saves the generated files
"""

import subprocess
from pathlib import Path

from lib.state import mark_step_complete, save_state


def _write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _infer_base_url(url: str) -> str:
    try:
        # avoid importing urllib for minimal dependency; simple parse works for http(s)
        if "://" not in url:
            return url.rstrip("/")
        scheme, rest = url.split("://", 1)
        host = rest.split("/", 1)[0]
        if not host:
            return url.rstrip("/")
        return f"{scheme}://{host}"
    except Exception:
        return url.rstrip("/")


def _scaffold_playwright_project(playwright_dir: Path, ticket: str, target_url: str) -> None:
    """
    Create a minimal Playwright project skeleton (non-destructive).
    This helps Step 3/4 work out of the box and provides utilities for
    selective evidence screenshots without capturing screenshots for all tests.
    """
    safe_name = "".join(ch.lower() if ch.isalnum() else "-" for ch in ticket).strip("-")
    if not safe_name:
        safe_name = "qa-ticket"

    _write_if_missing(
        playwright_dir / "package.json",
        (
            "{\n"
            f'  "name": "{safe_name}-playwright",\n'
            '  "private": true,\n'
            '  "scripts": {\n'
            '    "test": "playwright test",\n'
            '    "test:headed": "playwright test --headed"\n'
            "  },\n"
            '  "devDependencies": {\n'
            '    "@playwright/test": "^1.58.2"\n'
            "  }\n"
            "}\n"
        ),
    )

    base_url = _infer_base_url(target_url) if target_url else "http://localhost:3000"

    _write_if_missing(
        playwright_dir / "playwright.config.ts",
        (
            "import { defineConfig, devices } from '@playwright/test';\n"
            "\n"
            "const baseURL =\n"
            f"  process.env.BASE_URL?.replace(/\\/$/, '') ?? '{base_url}';\n"
            "const workersEnv = (process.env.PW_WORKERS ?? '').trim();\n"
            "const workers = workersEnv ? Number.parseInt(workersEnv, 10) : undefined;\n"
            "const fullyParallelEnv = (process.env.PW_FULLY_PARALLEL ?? '').trim();\n"
            "const fullyParallel = fullyParallelEnv ? fullyParallelEnv !== '0' : true;\n"
            "\n"
            "export default defineConfig({\n"
            "  testDir: './tests',\n"
            "  fullyParallel,\n"
            "  forbidOnly: !!process.env.CI,\n"
            "  retries: process.env.CI ? 1 : 0,\n"
            "  workers,\n"
            "  timeout: 90_000,\n"
            "  expect: { timeout: 30_000 },\n"
            "  use: {\n"
            "    baseURL,\n"
            "    ...devices['Desktop Chrome'],\n"
            "    viewport: { width: 1920, height: 1080 },\n"
            "    trace: 'on-first-retry',\n"
            "    screenshot: 'only-on-failure',\n"
            "    ignoreHTTPSErrors: true,\n"
            "  },\n"
            "  projects: [{ name: 'chromium', use: {} }],\n"
            "});\n"
        ),
    )

    _write_if_missing(
        playwright_dir / "fixtures" / "evidence.ts",
        (
            "import type { Page, TestInfo } from '@playwright/test';\n"
            "\n"
            "function _sanitizeLabel(label: string): string {\n"
            "  const normalized = label\n"
            "    .toLowerCase()\n"
            "    .replace(/[^a-z0-9_-]+/g, '_')\n"
            "    .replace(/^_+|_+$/g, '');\n"
            "  return (normalized || 'evidence').slice(0, 80);\n"
            "}\n"
            "\n"
            "/**\n"
            " * Capture an evidence screenshot only where you call it.\n"
            " * - Output goes under Playwright's output dir (Step 4 uses --output=test-results).\n"
            " * - Also attaches to the JSON report (attachments).\n"
            " */\n"
            "export async function captureEvidenceScreenshot(\n"
            "  page: Page,\n"
            "  testInfo: TestInfo,\n"
            "  label = 'evidence'\n"
            "): Promise<string> {\n"
            "  const name = `${_sanitizeLabel(label)}.png`;\n"
            "  const outPath = testInfo.outputPath(name);\n"
            "  await page.screenshot({ path: outPath, fullPage: true });\n"
            "  await testInfo.attach(name, { path: outPath, contentType: 'image/png' });\n"
            "  return outPath;\n"
            "}\n"
        ),
    )

    _write_if_missing(
        playwright_dir / "fixtures" / "test-data.ts",
        (
            "export const TEST_DATA = {\n"
            "  // DATA-001: { ... },\n"
            "};\n"
            "\n"
            "// NFR/SLA defaults (override per project)\n"
            "export const SLA_MS = 3000;\n"
        ),
    )

    (playwright_dir / "pages").mkdir(parents=True, exist_ok=True)
    (playwright_dir / "tests").mkdir(parents=True, exist_ok=True)


def snapshot_page(url: str) -> str:
    """
    Open target URL with playwright-cli and capture page snapshot.
    Returns snapshot text (element refs + accessibility tree).
    """
    result = subprocess.run(
        ["npx", "playwright-cli", "snapshot"],
        input=f"goto {url}\nsnapshot\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    return result.stdout or result.stderr


def screenshot_page(url: str, output_path: str) -> bool:
    """Take a screenshot of the target URL via playwright-cli."""
    result = subprocess.run(
        ["npx", "playwright-cli", "screenshot", url, output_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    return result.returncode == 0


def write_playwright_files(state: dict, config: dict, files: list[tuple[str, str]]) -> dict:
    """
    Write generated Playwright files.
    files: list of (relative_path, content) tuples.
    """
    playwright_dir = Path(state["artifacts"]["playwright_dir"])
    playwright_dir.mkdir(parents=True, exist_ok=True)

    for filepath, content in files:
        full_path = playwright_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        print(f"[Step 3] Written: {full_path}")

    print(f"[Step 3] Playwright project written to {playwright_dir}")
    mark_step_complete(state, "playwright")
    save_state(state, config["output"]["base_dir"])
    return state


def run(state: dict, config: dict) -> dict:
    """Prepare context for Claude Code to generate Playwright tests."""
    print(f"[Step 3] Preparing Playwright generation for {state['ticket']}...")

    if not state.get("target_url"):
        raise RuntimeError("target_url not set. Pass --url flag.")

    test_cases_path = Path(state["artifacts"]["test_cases"])
    if not test_cases_path.exists():
        raise RuntimeError("Test cases not found. Run step 'testcases' first.")

    playwright_dir = Path(state["artifacts"]["playwright_dir"])
    playwright_dir.mkdir(parents=True, exist_ok=True)
    _scaffold_playwright_project(
        playwright_dir, state.get("ticket", "ticket"), state.get("target_url", "")
    )

    print(f"[Step 3] Target URL:      {state['target_url']}")
    print(f"[Step 3] Test cases:      {test_cases_path}")
    print(f"[Step 3] Output dir:      {playwright_dir}")
    print(
        "[Step 3] Claude Code will use playwright-cli to analyze the page and generate POM tests."
    )
    return state
