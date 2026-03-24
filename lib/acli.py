"""
AcliClient - Generalized wrapper around acli.exe for Jira operations.
Patterns extracted from generate_dashboard.py (exact subprocess + encoding approach).
"""

import json
import os
import re
import subprocess

# ── Constants ─────────────────────────────────────────────────────────────────
SEVERITY_FIELD = "customfield_10058"
RESOLVED_STATUSES = {"완료", "Done", "Resolved", "해결됨", "Closed"}

AREA_KEYWORDS = {
    "Web": ["web", "웹", "ui", "프론트", "front", "browser", "브라우저", "페이지"],
    "API": ["api", "endpoint", "rest", "응답", "response", "서버"],
    "Engine": ["engine", "엔진", "로직", "logic", "배치", "batch", "스케줄러", "scheduler"],
    "DB": ["db", "database", "테이블", "table", "쿼리", "query", "sql"],
    "Android": ["android", "안드로이드", "앱"],
    "iOS": ["ios", "아이폰", "swift"],
    "Security": ["보안", "security", "auth", "인증", "token", "매크로", "어뷰징"],
    "Cache": ["cache", "캐시", "redis", "ttl", "cdn"],
    "Infra": ["infra", "인프라", "서버", "deploy", "배포", "cluster"],
}


class AcliClient:
    """
    Wrapper around acli.exe for Jira interactions.
    Uses the exact same subprocess patterns as generate_dashboard.py:
      - capture_output=True, text=True
      - encoding="utf-8", errors="replace"
      - env={**os.environ, "LANG": "en_US.UTF-8"}
    """

    def __init__(self, config: dict):
        acli_cfg = config.get("acli") or {}
        self.acli_path = (acli_cfg.get("path") or "").strip()
        self.token_path = (acli_cfg.get("token_path") or "").strip()
        self.site = (acli_cfg.get("site") or "").strip()
        self.email = (acli_cfg.get("email") or "").strip()
        self.severity_field = config.get("jira", {}).get("severity_field", SEVERITY_FIELD)
        self.resolved_statuses = set(
            config.get("jira", {}).get("resolved_statuses", list(RESOLVED_STATUSES))
        )
        self.bug_issue_type = config.get("jira", {}).get("bug_issue_type", "버그")

        if not self.acli_path:
            raise ValueError(
                "Missing Jira CLI config: set 'acli.path' in config.yaml "
                "or env QA_PIPELINE_ACLI_PATH."
            )

    # ── Core subprocess helpers ────────────────────────────────────────────────

    def run_json(self, args: list) -> dict | list | None:
        """Run acli with --json flag, return parsed JSON or None on error."""
        cmd = [self.acli_path] + args + ["--json"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env={**os.environ, "LANG": "en_US.UTF-8"},
            )
            if result.returncode != 0:
                return None
            return json.loads(result.stdout)
        except Exception:
            return None

    def run_text(self, args: list) -> str:
        """Run acli without --json, return raw stdout text."""
        result = subprocess.run(
            [self.acli_path] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "LANG": "en_US.UTF-8"},
        )
        return result.stdout

    # ── Jira operations ────────────────────────────────────────────────────────

    def get_issue(self, key: str) -> dict | None:
        """Fetch a single Jira issue with all fields. Returns raw API dict."""
        return self.run_json(["jira", "workitem", "view", key])

    def search_issues(self, jql: str, project_key: str) -> list[str]:
        """Search Jira using JQL, return list of issue keys (deduplicated, ordered)."""
        text = self.run_text(
            [
                "jira",
                "workitem",
                "search",
                "--jql",
                jql,
                "--limit",
                "200",
            ]
        )
        pattern = rf"{re.escape(project_key)}-\d+"
        keys = re.findall(pattern, text)
        return list(dict.fromkeys(keys))  # deduplicate, preserve order

    def get_issue_detail(self, key: str) -> dict | None:
        """
        Fetch issue and return a normalized dict with keys:
        key, summary, status, severity, created, resolved_date, labels, area
        """
        raw = self.run_json(
            [
                "jira",
                "workitem",
                "view",
                key,
                "--fields",
                f"summary,created,resolutiondate,status,labels,{self.severity_field}",
            ]
        )
        if not raw:
            return None

        fields = raw.get("fields", {})
        severity_obj = fields.get(self.severity_field) or {}
        status_obj = fields.get("status") or {}
        summary = fields.get("summary", "")
        jira_labels = fields.get("labels") or []

        area = self.detect_area(summary, jira_labels)

        return {
            "key": raw.get("key", key),
            "summary": summary,
            "status": status_obj.get("name", "해야 할 일"),
            "severity": severity_obj.get("value", "Unknown"),
            "created": fields.get("created", ""),
            "resolved_date": fields.get("resolutiondate", ""),
            "labels": jira_labels,
            "area": area,
        }

    def create_bug(
        self,
        project: str,
        summary: str,
        description: str,
        severity: str = "Medium",
        components: list = None,
    ) -> str | None:
        """
        Create a Jira bug ticket. Returns the created issue key (e.g. 'PA-42') or None.
        severity must be one of: Critical / Major / Medium / Minor
        """
        if components is None:
            components = []

        args = [
            "jira",
            "workitem",
            "create",
            "--project",
            project,
            "--issuetype",
            self.bug_issue_type,
            "--summary",
            summary,
            "--description",
            description,
            "--custom-fields",
            f"{self.severity_field}:{severity}",
        ]

        if components:
            args += ["--components", ",".join(components)]

        raw = self.run_json(args)
        if not raw:
            return None

        # acli returns {"key": "PA-42", ...} on success
        key = raw.get("key")
        if key:
            return key

        # Some versions wrap in a list
        if isinstance(raw, list) and raw:
            return raw[0].get("key")

        return None

    # ── Static helpers ────────────────────────────────────────────────────────

    @staticmethod
    def detect_area(summary: str, labels: list = None) -> str:
        """
        Detect functional area from ticket summary and labels.
        Mirrors generate_dashboard.py detect_area() logic exactly:
          1. [Product_Area] bracket pattern takes priority
          2. Falls back to keyword scan of summary
        """
        if labels is None:
            labels = []

        # [제품_영역] pattern: [멜론_Web], [SmartAuth_API] etc.
        match = re.search(r"\[.+?_(.+?)\]", summary)
        if match:
            tag = match.group(1).strip()
            tag_lower = tag.lower()
            for area, keywords in AREA_KEYWORDS.items():
                if tag_lower in [k.lower() for k in keywords] or tag_lower == area.lower():
                    return area
            return tag  # unmapped tag returned as-is

        # Keyword scan of summary
        summary_lower = summary.lower()
        for area, keywords in AREA_KEYWORDS.items():
            if any(k in summary_lower for k in keywords):
                return area

        # Check labels
        for label in labels:
            label_lower = label.lower()
            for area, keywords in AREA_KEYWORDS.items():
                if any(k in label_lower for k in keywords):
                    return area

        return "기타"
