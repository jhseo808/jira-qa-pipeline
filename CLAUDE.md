# CLAUDE.md

Claude Code (claude.ai/code) 는 **이 파일을 진입점**으로 삼고, 상세 가이드는 **`docs/claude/`** 아래로 분리되어 있다.

## 프로젝트 요약

Jira QA 요청부터 QA 계획서 → 테스트케이스 → Playwright → 보고 → 버그 티켓 → 대시보드 → 사이드이펙트까지 **8단계 파이프라인**. Claude Code는 문서·POM·테스트 생성에 참여하고, Claude API는 사용하지 않는다.

**데모·학습용 타깃**: 예시 명령·산출물에 쓰는 공개 URL(예: Melon 차트)은 **독자가 맥락을 이해하기 위한 샘플**이다. 본 저장소와 해당 **서비스 운영사(본사)는 무관**이며, 공식 검증·제휴·내부 승인을 의미하지 않는다. 실제 운영·부하를 주지 않도록 호출 빈도·환경(STG 등)은 각자 정책에 맞게 조정한다.

## 최근 반영된 실행 규칙(요약)

- 스크린샷: 기본은 `screenshot: 'only-on-failure'`이며, 필요한 테스트에서만 `fixtures/evidence.ts`의 `captureEvidenceScreenshot()`로 증거를 남긴다.
- Step 4: 1차 실행 후 실패가 있으면 `failed_tests.txt` + `rerun_failed.ps1`를 생성하고, 실패 케이스만 1회 재실행 결과(`test_results_rerun.json`)를 남긴다.
- 병렬 실행: `config.yaml`의 `playwright.workers`, `playwright.fully_parallel`로 속도를 조절한다(현재 기본값 `workers=2`, `fully_parallel=true`).
- 보고서: `qa_report.md`는 실패 요약에 테스트케이스 ID를 포함하고, 8.1(1차 실패 원인 분석) + 8.2(실패만 1회 재테스트 결과/판단 근거) 히스토리를 남긴다.

## 문서 맵

| 문서 | 역할 |
|------|------|
| [docs/claude/common.md](docs/claude/common.md) | 환경, Jira, 저장소 구조, `workflow_runner`, 역할 표, state 수동 갱신, 계획서 13섹션·템플릿 링크 |
| [docs/claude/step-01-plan.md](docs/claude/step-01-plan.md) | Step 1: QA 계획서 |
| [docs/claude/step-02-testcases.md](docs/claude/step-02-testcases.md) | Step 2: 테스트케이스 |
| [docs/claude/step-03-playwright.md](docs/claude/step-03-playwright.md) | Step 3: Playwright / playwright-cli |
| [docs/claude/step-04-run.md](docs/claude/step-04-run.md) | Step 4: 테스트 실행 |
| [docs/claude/step-05-report.md](docs/claude/step-05-report.md) | Step 5: QA 결과서 |
| [docs/claude/step-06-bugs.md](docs/claude/step-06-bugs.md) | Step 6: Jira 버그 생성 |
| [docs/claude/step-07-dashboard.md](docs/claude/step-07-dashboard.md) | Step 7: 대시보드 |
| [docs/claude/step-08-sideeffects.md](docs/claude/step-08-sideeffects.md) | Step 8: 사이드이펙트 |
| [docs/claude/current-ticket.md](docs/claude/current-ticket.md) | 진행 중 티켓·다음 액션 (자주 갱신) |
| [docs/claude/README.md](docs/claude/README.md) | 위 문서 인덱스 |

**산출물 마스터 템플릿**: [templates/README.md](templates/README.md)

## 한 줄 명령 (예시)

```bash
python workflow_runner.py --ticket PA-21 --step all --url https://www.melon.com/chart/index.htm
```

전체 CLI 옵션은 [docs/claude/common.md](docs/claude/common.md) 를 본다.
