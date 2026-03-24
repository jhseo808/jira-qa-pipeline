"""
Lightweight environment/config diagnostics for portability.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DoctorCheck:
    name: str
    ok: bool
    detail: str


def _which(cmd: str) -> str | None:
    return shutil.which(cmd) or shutil.which(f"{cmd}.cmd") or shutil.which(f"{cmd}.exe")


def _run_version(cmd: list[str]) -> str:
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
        out = (r.stdout or r.stderr or "").strip()
        return out.splitlines()[0] if out else ""
    except Exception:
        return ""


def _check_writable_dir(path: Path) -> tuple[bool, str]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".__write_probe__"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True, str(path)
    except Exception as e:
        return False, f"{path} ({e})"


def run_doctor(config: dict) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []

    meta = config.get("_meta") if isinstance(config, dict) else None
    cfg_path = (meta or {}).get("config_path") if isinstance(meta, dict) else ""
    checks.append(DoctorCheck("config", True, cfg_path or "(unknown)"))

    # acli
    acli_cfg = (config.get("acli") or {}) if isinstance(config, dict) else {}
    acli_path = (acli_cfg.get("path") or "").strip()
    if not acli_path:
        checks.append(
            DoctorCheck(
                "acli.path",
                False,
                "missing (set config.local.yaml or env QA_PIPELINE_ACLI_PATH)",
            )
        )
    else:
        # Bare name -> PATH lookup
        if ("/" not in acli_path) and ("\\" not in acli_path):
            resolved = _which(acli_path)
            checks.append(
                DoctorCheck("acli.path", bool(resolved), resolved or f"not on PATH: {acli_path}")
            )
        else:
            p = Path(acli_path)
            checks.append(DoctorCheck("acli.path", p.exists(), str(p)))

    token_path = (acli_cfg.get("token_path") or "").strip()
    if token_path:
        tp = Path(os.path.expandvars(token_path)).expanduser()
        checks.append(DoctorCheck("acli.token_path", tp.exists(), str(tp)))

    # output dir
    out_cfg = (config.get("output") or {}) if isinstance(config, dict) else {}
    out_dir = Path((out_cfg.get("base_dir") or "output"))
    ok, detail = _check_writable_dir(out_dir)
    checks.append(DoctorCheck("output.base_dir", ok, detail))

    # node/npm/npx
    node = _which("node")
    npm = _which("npm")
    npx = _which("npx")
    checks.append(DoctorCheck("node", bool(node), (node or "not found")))
    if node:
        checks.append(DoctorCheck("node.version", True, _run_version([node, "--version"])))
    checks.append(DoctorCheck("npm", bool(npm), (npm or "not found")))
    if npm:
        checks.append(DoctorCheck("npm.version", True, _run_version([npm, "--version"])))
    checks.append(DoctorCheck("npx", bool(npx), (npx or "not found")))
    if npx:
        checks.append(DoctorCheck("npx.version", True, _run_version([npx, "--version"])))

    return checks


def print_doctor(checks: list[DoctorCheck]) -> int:
    failed = 0
    for c in checks:
        status = "OK" if c.ok else "FAIL"
        if not c.ok:
            failed += 1
        print(f"[Doctor] {status:4} {c.name}: {c.detail}")
    return 0 if failed == 0 else 2
