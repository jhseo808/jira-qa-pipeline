# 공통: 환경 · Jira · 구조 · 오케스트레이션

[← 인덱스](README.md)

---

## 프로젝트 한 줄

**QA 자동화 전체 워크플로우** — Jira QA 요청 티켓에서 시작하여 QA 계획서 → 테스트케이스 → Playwright 자동화 테스트 → 결과 보고서 → 버그 티켓 생성 → 버그 트래킹 대시보드 → 사이드이펙트 감지까지의 8단계 파이프라인.

**Claude Code가 AI 생성 역할 담당** (Claude API 미사용). playwright-cli로 페이지를 직접 분석하고 테스트 코드를 생성한다.

---

## Environment

- Python 3.13.12 virtual environment in `.venv/`
- Activate: `.venv/Scripts/activate` (Windows)
- Dependencies: `pyyaml`, `pytest` (`pip install -r requirements.txt`)
- 단위 테스트: 프로젝트 루트에서 `python -m pytest tests` 또는 `.\scripts\run_tests.ps1`
- 환경 점검(권장): `python workflow_runner.py --doctor` (acli, node/npm/npx, output 경로 확인)
- 설정 검증(권장): `python workflow_runner.py --validate-config` (필수 경로/쓰기 가능 여부 빠른 검증)
- 초기화(권장): `python workflow_runner.py --init` (`.env`, `config.local.yaml` 템플릿 생성. 기존 파일은 덮어쓰지 않음)
- Node.js v23.7.0 / npm 10.9.2
- `npx playwright-cli` v1.59.0-alpha (Playwright MCP CLI — 페이지 분석용)
- `npx playwright` v1.58.2 (테스트 실행용)
- CI(선택): GitHub Actions `.github/workflows/ci.yml` (pytest + ruff(advisory))

**Claude Code용 playwright-cli 스킬** (선택, 권장): 저장소 루트에서 `npx playwright-cli install --skills` 실행 시 `.claude/skills/playwright-cli/` 에 `SKILL.md` 및 `references/*.md` 가 설치된다. 상세는 [step-03-playwright.md](step-03-playwright.md) 의 **§4** 를 본다.

---

## Jira Connection

- CLI tool: `D:\jhseo\project\AtlassianCLI\acli.exe` (v1.3.14)
- Site: `jhseo.atlassian.net`, Email: `jhseo808@gmail.com`
- Token: `D:\jhseo\project\AtlassianCLI\token.txt`
- Severity 커스텀 필드: `customfield_10058` (Critical / Major / Medium / Minor)
- 티켓 조회: `acli.exe jira workitem view PA-21` (plain text)
- JSON 조회: `acli.exe jira workitem view PA-21 --json`
- `config.yaml` 로딩 시 반드시 `encoding='utf-8'` 명시 (Windows cp949 오류 방지)
- **환경변수 오버라이드(이식성)**: 다른 PC/CI에서는 아래를 설정하면 `config.yaml`을 수정하지 않아도 된다.
  - `QA_PIPELINE_CONFIG`: 사용할 설정 파일 경로
  - `QA_PIPELINE_ACLI_PATH`: `acli.exe` 경로
  - `QA_PIPELINE_ACLI_TOKEN_PATH`: token 파일 경로
  - `QA_PIPELINE_ACLI_SITE`: Atlassian site (예: `xxx.atlassian.net`)
  - `QA_PIPELINE_ACLI_EMAIL`: 이메일
  - `QA_PIPELINE_OUTPUT_DIR`: `output/` 기본 경로
- **설정 파일 분리(권장)**: `config.yaml`은 공유 가능한 기본값으로 두고, 개인 PC 전용 값(절대경로, 토큰 경로 등)은 `config.local.yaml`에 둔다. 기본 실행은 `config.local.yaml`이 존재하면 자동으로 우선 사용한다.
- **Step 7 대시보드**: `config.yaml`의 `dashboard.bug_summary_contains`에 문자열을 넣으면 JQL에 `summary ~ "…"`가 붙고, 응답도 제목에 해당 문자열이 있는 이슈만 집계한다. 비우거나 키를 생략하면 프로젝트 버그 전체. 검증 기간·축 날짜는 `output/{ticket}/qa_plan.md`의 `총 검증 기간: YYYY-MM-DD ~ YYYY-MM-DD` 줄을 `generate_dashboard.py`가 파싱한다(없으면 이슈 등록일 범위로 보정).

---

## 저장소 파일 구조

```
D:\jhseo\project\atlassian-builer\
├── workflow_runner.py              # 메인 오케스트레이터 CLI
├── config.yaml                    # 전역 설정
├── requirements.txt               # pyyaml
├── generate_dashboard.py          # 버그 트래킹 대시보드 (독립 실행 가능)
├── qa_plan_template.md            # → templates/qa_plan.md 안내 (하위 호환)
│
├── templates/                     # 산출물 작성용 마스터 템플릿
│   ├── README.md
│   ├── qa_plan.md
│   ├── qa_report.md
│   └── dashboard/
│       ├── README.md
│       └── dashboard_spec.md
│
├── docs/claude/                   # 본 가이드 (common + step별)
│
├── lib/
│   ├── acli.py
│   ├── state.py
│   ├── scheduler.py
│   └── jira_rest.py
│
├── steps/
│   ├── step1_plan_generator.py
│   ├── step2_testcase_generator.py
│   ├── step3_playwright_generator.py
│   ├── step4_test_runner.py
│   ├── step5_report_generator.py
│   ├── step6_bug_creator.py
│   ├── step7_dashboard.py
│   └── step8_sideeffect_detector.py
│
└── output/{ticket}/               # 티켓별 산출물
    ├── pipeline_state.json
    ├── qa_plan.md
    ├── test_cases.md
    ├── playwright/
    │   ├── package.json
    │   ├── playwright.config.ts
    │   ├── pages/
    │   ├── tests/
    │   └── fixtures/test-data.ts
    ├── test_results.json
    ├── qa_report.md
    ├── created_bugs.json
    ├── dashboard.html
    └── side_effects.md
```

---

## workflow_runner.py 사용법

```bash
# 개별 단계 실행
python workflow_runner.py --ticket PA-21 --step plan
python workflow_runner.py --ticket PA-21 --step testcases
python workflow_runner.py --ticket PA-21 --step playwright --url https://www.melon.com/chart/index.htm
python workflow_runner.py --ticket PA-21 --step run
python workflow_runner.py --ticket PA-21 --step report
python workflow_runner.py --ticket PA-21 --step bugs
python workflow_runner.py --ticket PA-21 --step dashboard
python workflow_runner.py --ticket PA-21 --step sideeffects

# 전체 파이프라인
python workflow_runner.py --ticket PA-21 --step all --url https://www.melon.com/chart/index.htm

# 특정 단계부터 재시작
python workflow_runner.py --ticket PA-21 --step all --from-step testcases

# 일일 자동화 (모든 활성 티켓 dashboard + sideeffects)
python workflow_runner.py --daily

# Windows Task Scheduler 등록
python workflow_runner.py --ticket PA-21 --schedule

# dry-run 확인
python workflow_runner.py --ticket PA-21 --step all --dry-run
```

---

## 단계별 역할 (스크립트 vs Claude Code)

| 단계 | 스크립트 역할 | Claude Code 역할 |
|------|-------------|----------------|
| Step 1 (plan) | Jira 티켓 fetch, state 캐시 | `output/{ticket}/qa_plan.md` 직접 작성 |
| Step 2 (testcases) | QA 계획서 로드 확인 | `output/{ticket}/test_cases.md` 직접 작성 |
| Step 3 (playwright) | playwright-cli 페이지 분석 보조 | 스냅샷 분석 후 POM TypeScript 파일 생성 |
| Step 4 (run) | `npx playwright test` 자동 실행 | 실패 스크린샷(`only-on-failure`), 실패 목록(`failed_tests.txt`) + 재실행 스크립트(`rerun_failed.ps1`) 생성 |
| Step 5 (report) | 결과 JSON 로드 | `qa_report.md`에 실패 TC 포함 + 1차/2차(재실행) 히스토리 기록 |
| Step 6 (bugs) | acli로 Jira 버그 티켓 생성 | — |
| Step 7 (dashboard) | generate_dashboard.py 재사용 | — |
| Step 8 (sideeffects) | 최근 버그 fetch | `side_effects.md` + TC 추가 작성 |

스텝별 상세는 [step-01-plan.md](step-01-plan.md) … [step-08-sideeffects.md](step-08-sideeffects.md) 를 본다.

---

## 단계 완료 후 state 수동 업데이트

```bash
.venv/Scripts/python -c "
import yaml, sys; sys.path.insert(0, '.')
from lib.state import load_state, mark_step_complete, save_state
with open('config.yaml', encoding='utf-8') as f:
    import yaml; config = yaml.safe_load(f)
state = load_state('PA-21', config['output']['base_dir'])
mark_step_complete(state, 'plan')  # 또는 'testcases', 'playwright' 등
save_state(state, config['output']['base_dir'])
print(state['steps_completed'])
"
```

---

## 산출물 템플릿 (마스터)

| 산출물 | 마스터 파일 |
|--------|-------------|
| QA 계획서 | [`templates/qa_plan.md`](../../templates/qa_plan.md) |
| 테스트케이스 | [`templates/test_cases.md`](../../templates/test_cases.md) |
| QA 결과서 | [`templates/qa_report.md`](../../templates/qa_report.md) |
| 대시보드 스펙 | [`templates/dashboard/dashboard_spec.md`](../../templates/dashboard/dashboard_spec.md) |

---

## QA Plan Template Structure (13 sections)

섹션별 본문 골격은 **`templates/qa_plan.md`** 를 사용한다.  
테스트케이스 명세는 **`templates/test_cases.md`** 를 사용한다.  
QA 결과서(Summary Report) 골격은 **`templates/qa_report.md`** 를 사용한다.

| Section | Purpose |
|---------|---------|
| 1. Overview | Test item, module versions, summary |
| 2. Scope | In/out of scope features |
| 3. Test Basis | ISTQB-based foundations (Jira, PRD, API Spec) |
| 4. Risk Analysis | Change and dependency risks (3-5개, 발생가능성·영향도·대응 포함) |
| 5. Test Strategy | Risk-based, change-impact, priority-based |
| 6. Test Approach | Functional/Regression, Manual+Automation |
| 7. Entry/Exit Criteria | Start/completion gates (Critical=0, High resolved) |
| 8. Traceability | Jira + Testcase links |
| 9. Test Environment | Server, DB, Android, iOS, Browser specs |
| 10. Schedule | Design/Execution/Regression phases with 실제 날짜 |
| 11. Defect Management | Jira-based, severity: Critical/Major/Medium/Minor |
| 12. Deliverables | Testcase, Defect List, QA Summary Report |
| 13. References | All links (Jira, Testcase, Automation repo, Dashboard) |
