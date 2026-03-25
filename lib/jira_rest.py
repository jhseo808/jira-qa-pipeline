"""
Jira REST client (no external deps).

Why:
  - Atlassian CLI (acli) requires OAuth login (interactive).
  - This project already stores an API token (token.txt) + email/site in config.local.yaml.
  - Step 7 dashboard should be able to fetch issues non-interactively using Jira Cloud REST API.

Auth:
  - Jira Cloud supports Basic auth with email + API token.
  - https://{site}/rest/api/3/...
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


def _normalize_site(site: str) -> str:
    s = (site or "").strip()
    if not s:
        return ""
    if s.startswith("http://") or s.startswith("https://"):
        return s.rstrip("/")
    return f"https://{s}".rstrip("/")


def _read_token_file(path: str) -> str:
    # token.txt is typically a single-line API token; avoid printing the content.
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        token = (f.read() or "").strip()
    return token


@dataclass(frozen=True)
class JiraRestClient:
    site: str
    email: str
    api_token: str

    @classmethod
    def from_config(cls, config: dict) -> "JiraRestClient":
        acli_cfg = config.get("acli") or {}
        site = _normalize_site(acli_cfg.get("site") or "")
        email = (acli_cfg.get("email") or "").strip()
        token_path = (acli_cfg.get("token_path") or "").strip()
        if not (site and email and token_path):
            raise ValueError("Missing acli.site/acli.email/acli.token_path for Jira REST auth.")
        api_token = _read_token_file(token_path)
        if not api_token:
            raise ValueError("API token file is empty.")
        return cls(site=site, email=email, api_token=api_token)

    def _auth_header(self) -> str:
        raw = f"{self.email}:{self.api_token}".encode("utf-8")
        return "Basic " + base64.b64encode(raw).decode("ascii")

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = self.site + path
        if params:
            url = url + "?" + urllib.parse.urlencode(params, doseq=True)
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, method=method, data=data)
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", self._auth_header())

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw) if raw.strip() else {}
        except urllib.error.URLError as e:
            # Some Windows environments block Python's socket usage (WinError 10013),
            # while PowerShell web requests still work. Fall back to PowerShell.
            if sys.platform == "win32" and "10013" in str(e):
                return self._request_json_powershell(method, url, body=body)
            raise
        except urllib.error.HTTPError as e:
            raw = ""
            try:
                raw = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            raise RuntimeError(f"Jira REST HTTP {e.code}: {raw[:400]}") from e

    def _request_json_powershell(
        self, method: str, url: str, *, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Windows fallback for environments where Python sockets are blocked.
        Keeps token out of the command line by passing auth via env var.
        """
        env = dict(os.environ)
        env["JIRA_URL"] = url
        env["JIRA_METHOD"] = method
        env["JIRA_AUTH_HEADER"] = self._auth_header()
        env["JIRA_BODY_JSON"] = json.dumps(body) if body is not None else ""

        ps = r"""
$ErrorActionPreference = 'Stop'
$headers = @{
  Authorization = $env:JIRA_AUTH_HEADER
  Accept = 'application/json'
  'Content-Type' = 'application/json'
}
$uri = $env:JIRA_URL
$method = $env:JIRA_METHOD
if ($method -eq 'GET' -or [string]::IsNullOrWhiteSpace($env:JIRA_BODY_JSON)) {
  $resp = Invoke-RestMethod -Method $method -Uri $uri -Headers $headers
} else {
  $resp = Invoke-RestMethod -Method $method -Uri $uri -Headers $headers -Body $env:JIRA_BODY_JSON
}
$resp | ConvertTo-Json -Depth 50
""".strip()

        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"PowerShell Jira REST failed (exit={result.returncode}): {result.stderr.strip()}"
            )
        out = (result.stdout or "").strip()
        return json.loads(out) if out else {}

    def search_issues(
        self,
        jql: str,
        *,
        fields: list[str],
        max_results: int = 200,
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        start_at = 0

        while True:
            chunk = min(100, max_results - len(issues))
            if chunk <= 0:
                break
            payload = self._request_json(
                "GET",
                "/rest/api/3/search",
                params={
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": chunk,
                    "fields": ",".join(fields),
                },
            )
            got = payload.get("issues") or []
            if not got:
                break
            issues.extend(got)
            start_at += len(got)
            total = payload.get("total")
            if isinstance(total, int) and start_at >= total:
                break

        return issues
