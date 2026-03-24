---
project: {PROJECT_NAME}
version: {VERSION}
release_type: {Regular | Hotfix | Emergency}
qa_owner: {NAME}
test_level: {System | Integration | E2E}
---

# QA Plan

---

## 1. Overview

### 1.1 Test Item

| 항목 | 내용 |
|------|------|
| 제품명 | {PROJECT_NAME} |
| 제품버전 | {VERSION} |
| 릴리즈 유형 | {RELEASE_TYPE} |

---

### 1.2 Module Version

| Module | Version |
|--------|--------|
| Server | {VERSION} |
| Android | {VERSION} |
| iOS | {VERSION} |

---

### 1.3 Summary

본 QA는 {주요 변경사항 요약}에 대한 품질 검증을 목적으로 수행된다.  
주요 영향 범위는 {영향 시스템}이며, 변경사항 기반 검증을 중심으로 수행한다.

---

## 2. Scope

### In Scope
- {신규 기능}
- {변경 기능}
- 핵심 사용자 흐름

### Out of Scope
- 변경 없는 기존 기능
- 외부 시스템

---

## 3. Test Basis

- Jira / 요구사항
- PRD / 기획서
- API Spec (Swagger)
- 기존 테스트케이스

---

## 4. Risk Analysis

- {변경 영향 기반 리스크}
- {의존성 기반 리스크}

---

## 5. Test Strategy

- Risk-based Testing
- Change Impact 기반 테스트
- Priority 기반 수행
- 핵심 기능 우선 검증

---

## 6. Test Approach

| 구분 | 내용 |
|------|------|
| 테스트 유형 | Functional / Regression |
| 수행 방식 | Manual + Automation |
| 자동화 범위 | 핵심 기능 |

---

## 7. Entry / Exit Criteria

### Entry
- 요구사항 정의 완료
- 테스트 환경 준비 완료
- 빌드 배포 완료

### Exit
- Critical Defect = 0
- High Defect 승인 또는 해결
- 주요 기능 정상 동작

---

## 8. Traceability

- Jira: {link}
- Testcase: {link}

---

## 9. Test Environment

| 구분 | 내용 |
|------|------|
| Server | {환경} |
| DB | {환경} |

### Client
- Android: {버전}
- iOS: {버전}
- Browser: Chrome 최신

---

## 10. Schedule

| Phase | Duration |
|------|----------|
| Test Design | Xd |
| Execution | Xd |
| Regression | Xd |

---

## 11. Defect Management

- Tool: Jira
- Severity: Critical / High / Medium / Low

---

## 12. Deliverables

- Testcase (link)
- Defect List (Jira)
- QA Summary Report

---

## 13. References

- Jira: {link}
- Testcase: {link}
- Automation: {repo}
- Dashboard: {link}

---
