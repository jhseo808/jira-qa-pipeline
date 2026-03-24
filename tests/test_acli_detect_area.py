"""lib.acli.AcliClient.detect_area — generate_dashboard와 동일 규칙."""

from __future__ import annotations

from lib.acli import AcliClient


def test_detect_area_bracket() -> None:
    assert AcliClient.detect_area("[멜론_DB] 슬로우 쿼리", []) == "DB"


def test_detect_area_labels() -> None:
    assert AcliClient.detect_area("제목", ["android"]) == "Android"
