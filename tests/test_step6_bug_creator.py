"""steps.step6_bug_creator — 실패 테스트 추출 로직."""

from __future__ import annotations

from steps.step6_bug_creator import extract_failed_tests


def test_extract_failed_tests_empty_suites() -> None:
    assert extract_failed_tests({"suites": []}) == []


def test_extract_failed_tests_one_failure() -> None:
    data = {
        "suites": [
            {
                "title": "Chart",
                "specs": [
                    {
                        "title": "should load",
                        "ok": False,
                        "file": "tests/a.spec.ts",
                        "tests": [
                            {
                                "status": "failed",
                                "error": {"message": "timeout"},
                            }
                        ],
                    }
                ],
            }
        ]
    }
    failed = extract_failed_tests(data)
    assert len(failed) == 1
    assert failed[0]["title"] == "should load"
    assert failed[0]["suite"] == "Chart"
    assert "timeout" in failed[0]["error"]


def test_extract_failed_tests_skips_ok() -> None:
    data = {
        "suites": [
            {
                "title": "S",
                "specs": [{"title": "ok spec", "ok": True, "tests": []}],
            }
        ]
    }
    assert extract_failed_tests(data) == []
