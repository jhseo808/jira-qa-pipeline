# 진행 중 티켓 스냅샷

> **갱신**: 수시로 바뀌는 내용이므로 세션 시작 시 확인하고 필요 시 수정한다.

## PA-21 (예시) — 2026-03-24 기준

- **티켓**: `[QA요청] Melon v1.2.3 | Chart TOP100 DB 변경 및 순위 로직 수정 검증 요청`
- **대상 URL**: `https://www.melon.com/chart/index.htm`
- **API Endpoint**: `GET /api/chart/top100`

| 단계 | 상태 | 산출물 |
|------|------|--------|
| Step 1: QA 계획서 | 완료 | `output/PA-21/qa_plan.md` |
| Step 2: 테스트케이스 | 완료 | `output/PA-21/test_cases.md` |
| Step 3: Playwright 생성 | 완료 | `output/PA-21/playwright/` |
| Step 4: 테스트 실행 | 완료 | `output/PA-21/test_results.json` |
| Step 5: QA 보고서 | 완료 | `output/PA-21/qa_report.md` |
| Step 6: Jira 버그 생성 | 완료 (실패 0건 → 버그 0건) | `output/PA-21/created_bugs.json` |
| Step 7: 대시보드 | 완료 | `output/PA-21/dashboard.html` |
| Step 8: 사이드이펙트 | 완료 | `output/PA-21/side_effects.md` |

### QA 계획서 핵심 (PA-21)

- **변경사항**: DB 구조 변경(집계→실시간 로그), 순위 로직 변경(가중치 기반), Redis TTL 10분→3분
- **주요 리스크**: 순위 정확성(R1), DB 부하(R2), 캐시 미스(R3), 동점 정렬(R4), API 구조 변경(R5)
- **검증 기간**: 2026-03-26 ~ 2026-04-08 (10 working days)
- **Exit Criteria**: Critical=0, 순위 정확성 통과, API SLA(<1초) 통과, 실시간 반영 3분 이내

### 대시보드 (Step 7) 구현 요약

| 구분 | 내용 |
|------|------|
| HTML 생성 | `generate_dashboard.py` — `build_html()`, `aggregate()`, `parse_qa_period_from_plan()` 등 |
| 필터·JQL | `config.yaml` → `dashboard.bug_summary_contains` (예: `멜론`) → `AND summary ~ "멜론"` + 제목 재필터 |
| 검증 기간·축 | `output/PA-21/qa_plan.md`의 `총 검증 기간: …` 파싱, 최초 이슈 등록일이 더 이르면 추이 축 시작일을 당김 |
| 스펙 문서 | `templates/dashboard/dashboard_spec.md`, `templates/dashboard/README.md` |
| 산출물 | `output/PA-21/dashboard.html` |

**HTML만 재생성**

```bash
cd D:\jhseo\project\atlassian-builer
python workflow_runner.py --ticket PA-21 --step dashboard --from-step dashboard --url https://www.melon.com/chart/index.htm
```

`--from-step dashboard`가 없으면 이미 `dashboard` 완료 시 Step 7이 스킵된다.

---

### 백로그 (다음 TODO)

- Step 3 스냅샷·스크린샷·증거, **CI(pytest)**: 검토·작업 항목은 [todo-backlog.md](todo-backlog.md) 에 저장됨.

### 참고: 전체 파이프라인 재점검

```bash
cd D:\jhseo\project\atlassian-builer
python workflow_runner.py --ticket PA-21 --step all
```

[← 인덱스](README.md)
