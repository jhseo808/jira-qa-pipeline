"""generate_dashboard.py 순수 로직 단위 테스트 (acli 미사용)."""

from __future__ import annotations

from pathlib import Path

import generate_dashboard as gd


def _bug(
    key: str = "PA-1",
    summary: str = "[멜론_Web] 샘플",
    created: str = "2026-03-22T10:00:00.000+0900",
    status: str = "해야 할 일",
    severity: str = "Major",
    area: str = "Web",
    labels: list[str] | None = None,
) -> dict:
    return {
        "key": key,
        "summary": summary,
        "created": created,
        "status": status,
        "severity": severity,
        "area": area,
        "labels": labels or [],
    }


class TestDetectArea:
    def test_bracket_melon_web(self) -> None:
        assert gd.detect_area("[멜론_Web] 제목") == "Web"

    def test_bracket_api(self) -> None:
        assert gd.detect_area("[멜론_API] 응답") == "API"

    def test_keyword_fallback(self) -> None:
        assert gd.detect_area("Redis 캐시 TTL 오류") == "Cache"

    def test_default_etc(self) -> None:
        assert gd.detect_area("알 수 없는 제목") == "기타"


class TestExtractLabels:
    def test_jira_labels_first(self) -> None:
        out = gd.extract_labels("순위", ["custom-label"])
        assert "custom-label" in out

    def test_max_four(self) -> None:
        long_labels = ["a", "b", "c", "d", "e"]
        out = gd.extract_labels("순위 가중치 점수", long_labels)
        assert len(out) <= 4


class TestAggregate:
    def test_counts_and_daily(self) -> None:
        bugs = [
            _bug("PA-1", created="2026-03-22T10:00:00.000+0900", severity="Critical", area="Web"),
            _bug(
                "PA-2",
                created="2026-03-23T10:00:00.000+0900",
                severity="Critical",
                area="Web",
                status="완료",
            ),
        ]
        agg = gd.aggregate(bugs)
        assert agg["total"] == 2
        assert agg["resolved"] == 1
        assert agg["open"] == 1
        assert agg["rate"] == 50
        assert agg["sev_count"]["Critical"] == 2
        assert agg["daily_reg"]["2026-03-22"] == 1
        assert agg["daily_reg"]["2026-03-23"] == 1

    def test_empty(self) -> None:
        agg = gd.aggregate([])
        assert agg["total"] == 0
        assert agg["rate"] == 0


class TestBuildQaWeekdayIsos:
    def test_skips_weekend(self) -> None:
        # 2026-03-20 Fri ~ 2026-03-23 Mon → 금·월 (토일 제외)
        isos = gd.build_qa_weekday_isos("2026-03-20", "2026-03-23")
        assert "2026-03-20" in isos
        assert "2026-03-21" not in isos
        assert "2026-03-22" not in isos
        assert "2026-03-23" in isos

    def test_invalid_range_returns_empty(self) -> None:
        assert gd.build_qa_weekday_isos("not-a-date", "2026-01-01") == []


class TestParseQaPeriodFromPlan:
    def test_parses_line(self, tmp_path: Path) -> None:
        p = tmp_path / "plan.md"
        p.write_text(
            "총 검증 기간: 2026-03-26 ~ 2026-04-08 (10 working days)\n",
            encoding="utf-8",
        )
        start, end = gd.parse_qa_period_from_plan(p)
        assert start == "2026-03-26"
        assert end == "2026-04-08"

    def test_missing_file(self, tmp_path: Path) -> None:
        assert gd.parse_qa_period_from_plan(tmp_path / "none.md") == ("", "")


class TestInferPeriodBounds:
    def test_min_max_from_bugs(self) -> None:
        bugs = [
            _bug("PA-1", created="2026-03-25T00:00:00.000+0900"),
            _bug("PA-2", created="2026-03-20T00:00:00.000+0900"),
        ]
        mn, mx = gd.infer_period_bounds_from_bugs(bugs)
        assert mn == "2026-03-20"
        assert mx == "2026-03-25"


class TestEarliestBugIso:
    def test_none_when_empty(self) -> None:
        assert gd.earliest_bug_iso([]) is None


class TestCumulativeCountUptoDate:
    def test_includes_weekend_registrations(self) -> None:
        dm = {"2026-03-21": 2, "2026-03-24": 1}
        assert gd.cumulative_count_upto_date(dm, "2026-03-20") == 0
        assert gd.cumulative_count_upto_date(dm, "2026-03-21") == 2
        assert gd.cumulative_count_upto_date(dm, "2026-03-24") == 3

    def test_invalid_upto_returns_zero(self) -> None:
        assert gd.cumulative_count_upto_date({"2026-01-01": 1}, "bad") == 0


class TestCountResolvedFiledUpto:
    def test_resolved_only(self) -> None:
        bugs = [
            _bug("PA-1", created="2026-03-20T00:00:00.000+0900", status="완료"),
            _bug("PA-2", created="2026-03-25T00:00:00.000+0900", status="해야 할 일"),
        ]
        resolved_only = [b for b in bugs if b["status"] in gd.RESOLVED_STATUSES]
        assert gd.count_resolved_filed_upto(resolved_only, "2026-03-19") == 0
        assert gd.count_resolved_filed_upto(resolved_only, "2026-03-20") == 1
        assert gd.count_resolved_filed_upto(resolved_only, "2026-03-30") == 1


class TestBuildHtmlSmoke:
    """HTML 문자열 생성 스모크 (브라우저·acli 없음)."""

    def test_contains_stats_and_charts(self) -> None:
        bugs = [
            _bug(
                "PA-100",
                summary="[멜론_Web] 테스트",
                created="2026-03-24T12:00:00.000+0900",
                severity="Critical",
                area="Web",
            )
        ]
        agg = gd.aggregate(bugs)
        cfg = {
            "qa_ticket": "PA-21",
            "project": "Melon QA",
            "version": "v1",
            "description": "설명",
            "period_start": "2026-03-24",
            "period_end": "2026-03-28",
        }
        html = gd.build_html(bugs, agg, cfg)
        assert "PA-100" in html
        assert "chartTrend" in html
        assert "Melon QA" in html
        assert "2026-03-24" in html or "3/24" in html
