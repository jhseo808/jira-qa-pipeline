# Claude Code 가이드 (인덱스)

저장소 루트의 [`CLAUDE.md`](../../CLAUDE.md)에서 시작한다. 상세는 아래로 분리되어 있다.

| 문서 | 내용 |
|------|------|
| [common.md](common.md) | 환경, Jira, 저장소 구조, `workflow_runner`, 역할 표, state 갱신, 계획서 13섹션 요약 |
| [step-01-plan.md](step-01-plan.md) | Step 1: QA 계획서 |
| [step-02-testcases.md](step-02-testcases.md) | Step 2: 테스트케이스 |
| [step-03-playwright.md](step-03-playwright.md) | Step 3: Playwright / playwright-cli |
| [step-04-run.md](step-04-run.md) | Step 4: 테스트 실행 |
| [step-05-report.md](step-05-report.md) | Step 5: QA 결과서 |
| [step-06-bugs.md](step-06-bugs.md) | Step 6: Jira 버그 생성 |
| [step-07-dashboard.md](step-07-dashboard.md) | Step 7: 대시보드 |
| [step-08-sideeffects.md](step-08-sideeffects.md) | Step 8: 사이드이펙트 |
| [current-ticket.md](current-ticket.md) | 진행 중 티켓 스냅샷 (자주 갱신) |
| [todo-backlog.md](todo-backlog.md) | **백로그**: Step 3 스크린샷·증거, CI 등 (구현 예정) |

**TC 마스터 템플릿**: [`templates/test_cases.md`](../../templates/test_cases.md) — Step 2 산출물 `output/{ticket}/test_cases.md` 작성 시 복사해 사용한다.  
Step 2·3의 **제3자용 상세 프로세스**는 [step-02-testcases.md](step-02-testcases.md), [step-03-playwright.md](step-03-playwright.md) 를 본다.

**playwright-cli 스킬**: 저장소 루트에서 `npx playwright-cli install --skills` → `.claude/skills/playwright-cli/` 설치. 설치 방법·폴더 구성·쓰임은 [step-03-playwright.md](step-03-playwright.md) 의 **§4 playwright-cli 스킬** 절을 본다.
