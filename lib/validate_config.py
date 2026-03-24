"""
Config validation (fast fail) for CI / new machines.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ValidationIssue:
    level: str  # "ERROR" | "WARN"
    key: str
    message: str


def _which(cmd: str) -> str | None:
    return shutil.which(cmd) or shutil.which(f"{cmd}.cmd") or shutil.which(f"{cmd}.exe")


def _is_bare_name(path_like: str) -> bool:
    return ("/" not in path_like) and ("\\" not in path_like)


def _check_writable_dir(path: Path) -> tuple[bool, str]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".__write_probe__"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True, str(path)
    except Exception as e:
        return False, f"{path} ({e})"


def validate_config(config: dict) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    meta = config.get("_meta") if isinstance(config, dict) else None
    cfg_path = (meta or {}).get("config_path") if isinstance(meta, dict) else ""
    if cfg_path:
        p = Path(cfg_path)
        if not p.exists():
            issues.append(
                ValidationIssue(
                    "WARN",
                    "config",
                    f"config file not found: {p}",
                )
            )
    else:
        issues.append(ValidationIssue("WARN", "config", "config_path metadata missing"))

    # acli
    acli_cfg = config.get("acli") or {}
    acli_path = str(acli_cfg.get("path") or "").strip()
    if not acli_path:
        issues.append(
            ValidationIssue(
                "ERROR",
                "acli.path",
                "missing (set config.local.yaml or env QA_PIPELINE_ACLI_PATH)",
            )
        )
    else:
        if _is_bare_name(acli_path):
            resolved = _which(acli_path)
            if not resolved:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "acli.path",
                        f"not found on PATH: {acli_path}",
                    )
                )
        else:
            p = Path(os.path.expandvars(acli_path)).expanduser()
            if not p.exists():
                issues.append(ValidationIssue("ERROR", "acli.path", f"file not found: {p}"))

    # output
    out_cfg = config.get("output") or {}
    out_dir_raw = str(out_cfg.get("base_dir") or "").strip() or "output"
    out_dir = Path(out_dir_raw)
    ok, detail = _check_writable_dir(out_dir)
    if not ok:
        issues.append(ValidationIssue("ERROR", "output.base_dir", detail))

    # jira
    jira_cfg = config.get("jira") or {}
    sev_field = str(jira_cfg.get("severity_field") or "").strip()
    if not sev_field:
        issues.append(ValidationIssue("WARN", "jira.severity_field", "missing"))

    return issues


def print_validation(issues: list[ValidationIssue]) -> int:
    errors = 0
    for it in issues:
        if it.level == "ERROR":
            errors += 1
        print(f"[Validate] {it.level:5} {it.key}: {it.message}")
    if not issues:
        print("[Validate] OK: config looks valid")
    return 0 if errors == 0 else 2
