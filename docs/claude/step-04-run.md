# Step 4: 테스트 실행 (run)

[← 공통](common.md) · [인덱스](README.md)

## 스크립트

- `steps/step4_test_runner.py`
- `npx playwright test` → `output/{ticket}/test_results.json`

## Claude Code

- 없음 (자동 실행)

## Playwright 테스트 실행 (`@playwright/test`)

```bash
cd output/PA-21/playwright
npm install
npx playwright install chromium
npx playwright test --reporter=json
```

티켓이 다르면 `PA-21` 경로를 해당 티켓으로 바꾼다.

## 스크린샷 산출물

- 기본은 `playwright.config.ts`의 `screenshot: 'only-on-failure'`로 **실패 케이스만** 자동 캡처한다.
- “필요한 기능만” 증거 스크린샷이 필요하면 Step 3에서 제공하는 `fixtures/evidence.ts`의 `captureEvidenceScreenshot()`를 **해당 테스트에서만** 호출한다.
- 산출물은 Step 4 실행 시 `--output=test-results`로 지정된 폴더(예: `output/{ticket}/playwright/test-results/`) 아래에 저장된다.

## 실패 케이스만 1회 재실행 (권장 플로우)

Step 4의 1차 실행에서 실패가 발생하면, **원인 분석 후 실패 케이스만 1회 재실행**한다.

- 1차 실패 목록: `output/{ticket}/failed_tests.txt`
- 재실행 스크립트(자동 생성): `output/{ticket}/rerun_failed.ps1`
- 2차 재실행 결과(JSON): `output/{ticket}/test_results_rerun.json`
- 2차 재실행 산출물: `output/{ticket}/playwright/test-results-rerun/`

> 목표: 전체를 다시 돌리지 않고, 실패만 재확인하여 오버헤드를 줄이고 히스토리를 남긴다.

## 오케스트레이터

```bash
python workflow_runner.py --ticket PA-21 --step run
```

## 실행이 느릴 때(속도 단축 옵션)

Step 4는 `config.yaml`(또는 env)로 아래 옵션을 전달해 병렬화/디버그 속도를 조절할 수 있다.

- `playwright.workers`: 워커 수(병렬 수). 예: `4`
- `playwright.fully_parallel`: 스펙 파일 내부도 병렬 실행. 예: `true`
- `playwright.max_failures`: 디버그 시 빠르게 멈추기. 예: `1`

PowerShell 예시:
```powershell
$env:QA_PIPELINE_PW_WORKERS=4
$env:QA_PIPELINE_PW_FULLY_PARALLEL=1
python workflow_runner.py --ticket PA-21 --step run
```
