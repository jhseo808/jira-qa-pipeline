"""
Project initialization helper.

Creates portable config/templates without overwriting existing files.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InitResult:
    path: Path
    created: bool
    message: str


def _write_if_missing(path: Path, content: str) -> InitResult:
    if path.exists():
        return InitResult(path, False, "exists (skipped)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return InitResult(path, True, "created")


def init_project(project_root: Path) -> list[InitResult]:
    """
    Create:
      - .env (commented template)
      - config.local.yaml (local-only sample)
    We do NOT create/overwrite config.yaml because the repo already ships a portable one.
    """
    env_content = (
        "# Local environment overrides (optional)\n"
        "# Copy values you need from .env.example\n"
        "#\n"
        "# QA_PIPELINE_CONFIG=./config.local.yaml\n"
        "# QA_PIPELINE_ACLI_PATH=C:\\path\\to\\acli.exe\n"
        "# QA_PIPELINE_ACLI_TOKEN_PATH=C:\\path\\to\\token.txt\n"
        "# QA_PIPELINE_OUTPUT_DIR=./output\n"
    )

    local_yaml_content = (
        "acli:\n"
        "  # Set your local acli.exe path here or via env QA_PIPELINE_ACLI_PATH\n"
        '  path: "acli.exe"\n'
        '  # token_path: "C:\\\\path\\\\to\\\\token.txt"\n'
        '  site: ""\n'
        '  email: ""\n'
        "\n"
        "jira:\n"
        '  severity_field: "customfield_10058"\n'
        '  resolved_statuses: ["완료", "Done", "Resolved", "해결됨", "Closed"]\n'
        '  bug_issue_type: "버그"\n'
        "\n"
        "playwright:\n"
        '  executable: "npx"\n'
        '  browser: "chromium"\n'
        "  timeout_ms: 30000\n"
        "  headless: true\n"
        "\n"
        "output:\n"
        '  base_dir: "./output"\n'
        "\n"
        "dashboard:\n"
        '  bug_summary_contains: ""\n'
    )

    results: list[InitResult] = []
    results.append(_write_if_missing(project_root / ".env", env_content))
    results.append(_write_if_missing(project_root / "config.local.yaml", local_yaml_content))
    return results


def print_init_results(results: list[InitResult]) -> int:
    created = 0
    for r in results:
        if r.created:
            created += 1
        print(f"[Init] {r.message:16} {r.path}")
    if created == 0:
        print("[Init] Nothing to do.")
    return 0
