"""
Config loader with portability in mind.

Goals:
  - Keep existing config.yaml compatible.
  - Allow environment variable overrides for CI / different machines.
  - Resolve relative paths against the project root.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml


def _set_nested(cfg: dict, dotted_key: str, value) -> None:
    cur = cfg
    parts = dotted_key.split(".")
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


def _get_nested(cfg: dict, dotted_key: str, default=None):
    cur = cfg
    for p in dotted_key.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def _normalize_path(value: str, project_root: Path, *, allow_bare_name: bool = False) -> str:
    # Expand env vars like %USERPROFILE% and ~
    expanded = os.path.expandvars(value)
    p = Path(expanded).expanduser()

    # If it's just an executable name (e.g. "acli.exe"), keep it as-is so PATH lookup works.
    if allow_bare_name:
        raw = str(p)
        if raw and ("/" not in raw) and ("\\" not in raw):
            return raw

    if not p.is_absolute():
        p = (project_root / p).resolve()
    return str(p)


def load_config(config_path: str = "config.yaml", project_root: Path | None = None) -> dict:
    """
    Load config.yaml with:
      - utf-8 encoding (Windows-safe)
      - environment overrides
      - relative path resolution

    Env overrides (if set, they win over yaml):
      - QA_PIPELINE_CONFIG
      - QA_PIPELINE_ACLI_PATH
      - QA_PIPELINE_ACLI_TOKEN_PATH
      - QA_PIPELINE_ACLI_SITE
      - QA_PIPELINE_ACLI_EMAIL
      - QA_PIPELINE_OUTPUT_DIR
    """
    root = project_root or Path(__file__).resolve().parent.parent

    env_cfg = os.environ.get("QA_PIPELINE_CONFIG", "").strip()
    if env_cfg:
        config_path = env_cfg

    cfg_path = Path(config_path)
    if not cfg_path.is_absolute():
        cfg_path = (root / cfg_path).resolve()

    # If the caller uses the default config.yaml, prefer config.local.yaml when present.
    # This keeps local absolute paths/secrets out of the portable config.yaml.
    try:
        default_cfg = (root / "config.yaml").resolve()
        local_cfg = (root / "config.local.yaml").resolve()
        if (not env_cfg) and cfg_path == default_cfg and local_cfg.exists():
            cfg_path = local_cfg
    except Exception:
        pass

    cfg: dict = {}
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8", errors="replace") as f:
            cfg = yaml.safe_load(f) or {}

    # Defaults
    if "output" not in cfg or not isinstance(cfg.get("output"), dict):
        cfg["output"] = {}
    if not cfg["output"].get("base_dir"):
        cfg["output"]["base_dir"] = str((root / "output").resolve())

    # Environment variable overrides (portable, CI-friendly)
    env_overrides = {
        "acli.path": os.environ.get("QA_PIPELINE_ACLI_PATH", "").strip(),
        "acli.token_path": os.environ.get("QA_PIPELINE_ACLI_TOKEN_PATH", "").strip(),
        "acli.site": os.environ.get("QA_PIPELINE_ACLI_SITE", "").strip(),
        "acli.email": os.environ.get("QA_PIPELINE_ACLI_EMAIL", "").strip(),
        "output.base_dir": os.environ.get("QA_PIPELINE_OUTPUT_DIR", "").strip(),
    }
    for k, v in env_overrides.items():
        if v:
            _set_nested(cfg, k, v)

    # Normalize paths (only for keys that represent filesystem paths)
    # Normalize paths (only for keys that represent filesystem paths)
    v = _get_nested(cfg, "acli.path")
    if isinstance(v, str) and v.strip():
        _set_nested(cfg, "acli.path", _normalize_path(v.strip(), root, allow_bare_name=True))

    for key in ("acli.token_path", "output.base_dir"):
        v = _get_nested(cfg, key)
        if isinstance(v, str) and v.strip():
            _set_nested(cfg, key, _normalize_path(v.strip(), root))

    # Keep loader metadata for downstream modules (e.g. Step 7 dynamic import).
    cfg.setdefault("_meta", {})
    if isinstance(cfg["_meta"], dict):
        cfg["_meta"].setdefault("project_root", str(root))
        cfg["_meta"].setdefault("config_path", str(cfg_path))

    return cfg
