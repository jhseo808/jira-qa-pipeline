---
ticket: {JIRA_KEY}
project: {PROJECT_NAME}
version: {VERSION}
report_date: {YYYY-MM-DD}
qa_owner: {NAME}
---

# QA Summary Report

## 1. 개요

| 항목 | 내용 |
|------|------|
| QA 요청 티켓 | {JIRA_KEY} |
| 제품 / 버전 | {PROJECT_NAME} / {VERSION} |
| 보고 일자 | {YYYY-MM-DD} |
| 검증 범위 요약 | {한 줄 요약} |

---

## 2. 테스트 범위 및 기준

- **계획서** (`output/{ticket}/qa_plan.md`) 대비 수행 범위: {일치 / 부분 수행 / 범위 조정 사유}
- **Exit Criteria** 충족 여부: {충족 / 미충족} — 근거: {요약}

---

## 3. 자동화 실행 결과

> `test_results.json` 및 Playwright 리포트를 반영합니다.

| 구분 | 건수 |
|------|------|
| Passed | {N} |
| Failed | {N} |
| Skipped | {N} |
| 총 실행 | {N} |

### 실패 요약

| TC | 스펙 위치 | 테스트 | 실패 원인 (한 줄) |
|---|---|---|---|
| {TC-xxx} | {spec.ts:line} | {테스트명} | {원인} |

(실패가 없으면 "해당 없음"으로 표기)

---

## 4. 결함 요약

| 심각도 | 신규 | 잔여 | 해결 |
|--------|------|------|------|
| Critical | | | |
| Major | | | |
| Medium | | | |
| Minor | | | |

- **차단 이슈 여부**: {없음 / 있음 — 키 나열}
- **Jira 버그 티켓** (`created_bugs.json` 연동): {키 목록 또는 N/A}

---

## 5. 품질 판정

| 항목 | 결과 |
|------|------|
| 릴리즈 권고 | {Go / No-Go / 조건부 Go} |
| 조건 | {조건부일 때만 필수 조건 나열} |

---

## 6. 리스크 및 잔여 이슈

- {미해결 저항 이슈, 모니터링 항목, 기술 부채}

---

## 7. 부록

- **QA 계획서**: `output/{ticket}/qa_plan.md`
- **테스트케이스**: `output/{ticket}/test_cases.md`
- **자동화 결과**: `output/{ticket}/test_results.json`
- **대시보드**: `output/{ticket}/dashboard.html` (생성 시)

---

## 8. 히스토리 (1차 실패 분석 → 2차 재테스트)

### 8.1 1차 실행(전체) 실패 원인 분석

| TC | 스펙 위치 | 테스트 | 원인 분류(초안) | 메시지(첫 줄) | 분석/조치(초안) |
|---|---|---|---|---|---|
| {TC-xxx} | {spec.ts:line} | {테스트명} | {Timeout/Assertion/테스트 결함/...} | {메시지} | {조치} |

### 8.2 2차 재테스트(실패 케이스만 1회)

| TC | 실패 원인(첫 줄) | 버그 등록 판단 | 판단 근거 |
|---|---|---|---|
| {TC-xxx} | {메시지} | {등록 비권장/조건부/...} | {근거} |
