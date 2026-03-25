# 백로그 (TODO)

> 구현 예정·검토만 끝난 항목을 한곳에 둔다.  
> JQL·Jira 필터는 회사마다 다르므로 `config`/각 Step에서 **언제든 커스터마이즈**하면 된다.

---

## 1. Step 3 — 스냅샷·스크린샷·증거 수집

> **상태**: 완료.  
> **관련 코드**: `steps/step3_playwright_generator.py`, `output/{ticket}/playwright/fixtures/evidence.ts`

### 현재 상태

- `snapshot_page(url)` — `playwright-cli snapshot`으로 접근성 트리 등 수집
- `screenshot_page(url, path)` — `playwright-cli screenshot`으로 이미지 저장
- `run()` — `target_url`·경로 출력만 하고 위 함수 호출 없음

### 검토 요약

1. **TC 개수 = 스크린샷 개수**는 항상 타당하지 않음. 같은 기준 URL만 쓰는 TC가 많으면 동일 화면이 반복되어 비용 대비 이득이 작음.
2. **회귀·이슈 재현**은 자동화된 Playwright `test()` 단위로 실패 시 스크린샷/trace가 일반적 → **Step 4 / `playwright.config.ts`** 층이 자연스러움.
3. Step 3 시점에는 생성된 `*.spec.ts`가 없을 수 있음.
4. **Step 3 최소 연결**: 기준 URL에 **스냅샷 1회 + 베이스라인 스크린샷 1회** + 산출물 경로 로그 (`playwright/.evidence/` 등).
5. **TC별 추가 스크린샷**은 `test_cases.md`에 TC별로 다른 URL·화면이 명시된 경우에만 자동화하는 편이 합리적.

### TODO (Step 3)

#### A. `run()`에 최소 연결 (권장 1차)

- [x] `playwright_dir` 아래 증거/유틸리티(선택 스크린샷 캡처) 구조 제공
- [x] `snapshot_page(target_url)`/`screenshot_page(target_url, …)`는 필요 시 사용 가능(기본 오버헤드 최소화)
- [x] `npx` 경로: Windows 환경에서 `npx.cmd`까지 고려

#### B. `test_cases.md` 연동 (선택 2차)

- [x] TC별 증거 스크린샷은 테스트 코드에서 `captureEvidenceScreenshot()`를 호출하는 방식으로 제어

#### C. Step 4 — 테스트 단위 증거 (선택)

- [x] `playwright.config.ts` 기본값: `screenshot: 'only-on-failure'`, `trace: 'on-first-retry'`
- [x] 필요 시 `testInfo.attach` 기반 증거 첨부(`captureEvidenceScreenshot()`)

### 구현 시 참고

- 외부 PROD에 짧은 시간에 다수의 스냅샷/스크린샷을 반복 호출하지 않도록 주의.
- 구현 후 [step-03-playwright.md](step-03-playwright.md) 의 Step 3 스크립트 동작 설명을 한 절 보강.

---

## 2. CI (지속 통합)

> **목표**: PR/푸시마다 **Python 단위 테스트(`pytest`)**가 돌아가 회귀를 막는다.  
> JQL·acli·실제 Jira는 CI에서 불필요(현재 테스트도 외부 연동 없음).

### TODO (CI)

- [x] `.github/workflows/ci.yml` 추가
- [x] 트리거: `push` / `pull_request`
- [x] `actions/checkout` → `actions/setup-python`
- [x] `pip install -r requirements.txt` → `pytest`
- [x] (선택) `playwright` E2E는 1단계 CI에서 제외(필요 시 확장)

---

## 3. 아쉬운 점 (개선 TODO)

> 지금은 “동작한다” 수준을 넘어서, 운영/신뢰성/품질 게이트까지 강화하면 포트폴리오 완성도가 더 올라간다.

- [ ] **환경 재현성**: Step 7(Jira 조회/대시보드)이 네트워크·인증(OAuth/API token) 제약을 만나도 안정적으로 동작하도록 가이드/헬퍼 보강
- [ ] **테스트 설계 분리**: 기능/데이터/성능 성격의 검증을 분리하고, 무거운 검증(이미지 100개 등)은 샘플링/계층화로 실행시간 단축
- [ ] **품질 게이트**: “릴리즈 가능/불가” 기준(예: Critical=0, SLA, flaky 정책)을 문서화하고 파이프라인에서 체크
- [ ] **Flaky 대응**: 실패 재실행(현재 1회) 외에 flaky 분류, 안정화 가이드(wait 전략/네트워크 의존 제거) 추가

### 구현 시 참고

- 저장소가 GitHub가 아니면 동일 단계를 GitLab CI / Azure Pipelines 등으로 옮기면 됨.
- 구현 후 [common.md](common.md) Environment 절에 **CI 한 줄** 링크 또는 명령 추가.

---

[← 인덱스](README.md)
