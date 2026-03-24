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

## 오케스트레이터

```bash
python workflow_runner.py --ticket PA-21 --step run
```
