# Step 3: Playwright·POM·테스트 데이터 구축 (playwright)

[← 공통](common.md) · [인덱스](README.md) · 이전 단계: [step-02-testcases.md](step-02-testcases.md)

---

## 1. 이 단계가 하는 일

Step 3은 **Step 2에서 확정한 `test_cases.md`**를 실제로 **실행 가능한 자동화**로 옮기는 단계다.  
산출물은 **`output/{ticket}/playwright/`** 아래에 두며, 일반적으로 다음을 포함한다.

| 구분 | 설명 |
|------|------|
| **POM (Page Object Model)** | `pages/` — 화면·영역별로 **로케이터와 행동**을 모아, 스펙이 비즈니스 단어로 읽히게 한다. |
| **테스트 스펙** | `tests/*.spec.ts` — **TC ID**와 대응하는 시나리오·assert |
| **테스트 데이터** | `fixtures/test-data.ts` 등 — **DATA-xxx**와 동일한 구조로 두면 추적이 쉽다 |
| **설정** | `playwright.config.ts`, `package.json` |

**제3자가 이 단계만 읽어도** 알 수 있어야 하는 것:

- **어떤 TC가 어떤 파일에 구현되는지**  
- **playwright-cli**로 페이지를 분석한 뒤, **생성된 코드·스냅샷**을 어떻게 POM에 흡수하는지  
- **Robust / NFR** TC가 **모킹·타이밍 assert**로 어떻게 뒷받침되는지

---

## 2. 파이프라인에서의 위치

| 항목 | 설명 |
|------|------|
| **입력** | `output/{ticket}/test_cases.md` (필수), `output/{ticket}/qa_plan.md` (참고) |
| **출력** | `output/{ticket}/playwright/` (TypeScript 프로젝트) |
| **다음 단계** | Step 4에서 `npx playwright test`로 실행·`test_results.json` 생성 |

**스크립트**는 `steps/step3_playwright_generator.py`가 동작한다. **디렉터리 구조·POM·스펙 코드**는 Claude Code·개발자가 작성한다.

---

## 3. 선행 조건

1. `test_cases.md`에 **TC ID**, **데이터 ID(DATA-xxx)**, **Robust/NFR** 요구가 정의되어 있다.  
2. 대상 **기준 URL**(또는 API 베이스)이 TC 또는 계획서에 명시되어 있다.  
3. (로컬) Node.js·`npx` 사용 가능. `npx playwright-cli` 및 `npx playwright`는 [common.md](common.md) Environment 참고.

---

## 4. playwright-cli 스킬 (Claude Code)

CLI 자체는 `npx playwright-cli`로 실행하지만, **Claude Code가 명령·워크플로를 일관되게 쓰도록** 저장소에 **에이전트 스킬**을 둘 수 있다.

### 4.1 설치 (최초 1회·재설치 시)

저장소 루트에서:

```bash
npx playwright-cli install --skills
```

성공 시 워크스페이스가 초기화되고, 스킬이 **`.claude/skills/playwright-cli`** 아래에 설치된다. (로컬 `npm install playwright-cli`는 필수 아님.)

### 4.2 스킬 폴더 구성

| 경로 | 역할 |
|------|------|
| `.claude/skills/playwright-cli/SKILL.md` | 스킬 메타·**전체 CLI 명령** 요약, 스냅샷·세션·로컬 설치 안내 |
| `.claude/skills/playwright-cli/references/test-generation.md` | CLI 조작 시 **생성되는 Playwright TS 코드**·테스트 파일 조립 |
| `.claude/skills/playwright-cli/references/session-management.md` | **이름 있는 세션** `-s`, 영속 프로필, `close-all` / `kill-all` |
| `.claude/skills/playwright-cli/references/storage-state.md` | `state-save` / `state-load`, 쿠키·storage |
| `.claude/skills/playwright-cli/references/request-mocking.md` | `route`·`unroute`, 고급 `run-code` 모킹 |
| `.claude/skills/playwright-cli/references/running-code.md` | `run-code` (대기, iframe, 지오로케이션, 미디어 에뮬 등) |
| `.claude/skills/playwright-cli/references/tracing.md` | `tracing-start` / `tracing-stop`, 트레이스 산출물 |
| `.claude/skills/playwright-cli/references/video-recording.md` | `video-start` / `video-stop` |

스킬의 `allowed-tools`는 **`Bash(playwright-cli:*)`** 형태로, 에이전트가 **CLI를 통해** 브라우저를 조작하는 흐름과 맞춘다.

### 4.3 Step 3에서의 쓰임

- **SKILL.md**: `open`·`snapshot`·`network`·`route`·`tracing` 등 **명령 레퍼런스**  
- **references**: Robust/NFR·로그인 상태·모킹·트레이스 등 **세부 워크플로**  
- Step 3에서는 이를 **탐색·스냅샷·네트워크 관찰·(필요 시) 요청 모킹·증거 수집**에 활용하고, **회귀 실행**은 Step 4의 `@playwright/test`로 한다.

### 4.4 Step 3 수행 시 스킬 적용 (누가·언제)

| 구분 | 설명 |
|------|------|
| **적용 대상** | **Claude Code**(또는 동일 스킬을 읽는 에이전트)가 Step 3 작업을 할 때 |
| **적용 내용** | 저장소에 설치된 **`playwright-cli` 스킬**(`SKILL.md` + `references/`)을 **준수**하여, 브라우저 조작은 **`npx playwright-cli …`** 명령 체계로 수행한다. |
| **포함되는 활동** | TC에 맞는 **페이지 탐색**, **스냅샷 기반 요소 파악**, **네트워크·모킹·세션·트레이스** 등 스킬 문서에 정의된 워크플로, 그리고 이를 바탕 한 **POM·스펙·테스트 데이터 작성** |
| **적용되지 않는 것** | Step 4의 **`npx playwright test`** 회귀 실행은 **@playwright/test**이며, 스킬 파일이 직접 “실행”되지는 않는다. 스킬은 **CLI 탐색·코드 생성 보조**에 쓰인다. |

즉, “Step 3에서 테스트한다”를 **브라우저로 검증·기록하면서 자동화 코드를 만드는 과정**으로 볼 때, 그 **CLI 쪽 작업은 이 스킬을 적용한 흐름**으로 맞추는 것이 문서상의 기대다.

**참고**: `.claude/`는 팀 정책에 따라 **Git에 포함하지 않을 수 있다.** 이 경우 새 클론 후 위 **install --skills** 를 다시 실행한다.

---

## 5. 권장 구축 프로세스 (순서)

### 5.1 TC와 폴더 구조를 맞춘다

- `test_cases.md`의 **TC ID**를 스펙 파일 상단 주석 또는 `test.describe('TC-001 …')`에 넣는다.  
- **기능 영역**이 많으면 `tests/chart.spec.ts`처럼 **영역별 파일**로 나누고, 표로 “TC ID ↔ 파일”을 `test_cases.md`의 자동화 매핑란에 적어 둔다.

### 5.2 playwright-cli로 페이지를 이해한다

Claude Code가 이 절을 수행할 때는 **§4.4** 에 따라 **`playwright-cli` 스킬**을 적용한 CLI 워크플로를 따른다.

1. 대상 URL을 연다: `npx playwright-cli open <URL>`  
2. **스냅샷**으로 요소 ref·역할을 확인한다: `npx playwright-cli snapshot`  
3. **네트워크**로 API 호출 패턴을 본다: `npx playwright-cli network`  
4. 세션을 나누어야 하면 **이름 있는 세션** `-s` 옵션을 쓴다 (로그인·비로그인 분리 등).

CLI에서 액션을 수행할 때 **출력되는 Playwright 코드**가 있으면, 그 패턴을 **POM의 메서드**와 **스펙의 단계**로 옮긴다. **assert는 TC에 맞게 수동으로 추가**한다.

### 5.3 POM을 먼저 쌓는다

- **BasePage**: 공통 대기·로깅·네비게이션  
- **Page 클래스**: 화면 단위로 `goto`, `getList`, `clickRow` 등 **의미 있는 메서드**로 노출  
- **로케이터**는 가능하면 **역할·접근성** 기반(`getByRole` 등). CLI가 생성한 코드가 그렇다면 그대로 따른다.

### 5.4 테스트 데이터를 연결한다

- `test_cases.md`의 **DATA-001** … 과 동일한 키를 **fixture 또는 객체**로 둔다.  
- TC가 “빈 응답·지연”이면 Step 3에서 **`route` 모킹** 또는 `run-code`로 구현 가능 여부를 판단하고, **TC에 “자동화 비고”**를 업데이트한다.

### 5.5 Robust / NFR TC를 구현할 때

- **Robust**: `page.route`로 실패·지연·빈 응답을 시뮬레이션하거나, 스테이징 데이터로만 가능하면 TC에 **수동**으로 표시한다.  
- **NFR (응답 시간 등)**: `waitForResponse` + 시간 측정, 또는 API `request`로 SLA assert. **TC에 적힌 임계값과 동일한 숫자**를 코드에 쓴다.

### 5.6 증거·디버깅 (선택)

- 재현 실패 시 **tracing**·**스크린샷**·**비디오**는 CLI로 수집할 수 있고, `@playwright/test` 설정에도 동일 개념을 넣을 수 있다.  
- 산출물 경로는 팀 규칙에 맞게 `output/{ticket}/` 또는 `playwright/test-results/`에 둔다.

#### “필요한 기능만” 스크린샷 남기기 (권장)

- 기본 설정은 `playwright.config.ts`에서 `screenshot: 'only-on-failure'`로 두고, **증거가 필요한 TC/기능에서만** 스크린샷을 찍는다.
- Step 3에서 `output/{ticket}/playwright/fixtures/evidence.ts`(스캐폴딩 파일)를 두고, 해당 테스트에서만 호출한다.

예:

```ts
import { test, expect } from '@playwright/test';
import { captureEvidenceScreenshot } from '../fixtures/evidence';

test('TC-0xx 로그인 성공', async ({ page }) => {
  // ... steps ...
  await captureEvidenceScreenshot(page, test.info(), 'tc-0xx-login-success');
  // ... asserts ...
});
```

### 5.7 test_cases.md 역갱신

- 스펙·파일명이 정해지면 **Step 2 산출물**인 `test_cases.md`의 **자동화 매핑** 테이블을 채워 **제3자가 TC ↔ 코드**를 추적할 수 있게 한다.

---

## 6. 오케스트레이터 실행

```bash
python workflow_runner.py --ticket PA-21 --step playwright --url https://www.melon.com/chart/index.htm
```

URL은 티켓·TC에 맞게 바꾼다.

---

## 7. 완료 판정 (체크리스트)

제3자가 **완료 여부**를 판단할 때 사용할 수 있는 목록이다.

- [ ] `test_cases.md`에 나열된 **자동화 대상 TC**에 대해 대응 스펙이 존재하거나, **수동 전용**으로 표시되었다.  
- [ ] `playwright/`에서 `npm install` 후 **로컬에서 최소 1회** 이상 테스트 실행이 가능하다 (Step 4 전 사전 확인).  
- [ ] **DATA-xxx**가 코드의 테스트 데이터와 대응한다.  
- [ ] **Robust / NFR** TC가 “모킹·assert·수동” 중 어떤 방식인지 문서와 일치한다.

---

## 8. 다음 단계

Step 4는 [step-04-run.md](step-04-run.md) — `npx playwright test` 및 `test_results.json` 생성.
