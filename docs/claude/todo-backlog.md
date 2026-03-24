# 백로그 (TODO)

> 구현 예정·검토만 끝난 항목을 한곳에 둔다.  
> JQL·Jira 필터는 회사마다 다르므로 `config`/각 Step에서 **언제든 커스터마이즈**하면 된다.

---

## 1. Step 3 — 스냅샷·스크린샷·증거 수집

> **상태**: 검토만 완료, 구현은 다음 작업에서 진행.  
> **관련 코드**: `steps/step3_playwright_generator.py` (`snapshot_page`, `screenshot_page`는 정의만 있고 `run()`에서 미호출)

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

- [ ] `playwright_dir` 아래 `.evidence/` (또는 `step3-evidence/`) 생성
- [ ] `snapshot_page(target_url)` 결과를 `snapshot.txt` (또는 `.yml`)로 저장
- [ ] `screenshot_page(target_url, baseline.png)` 성공 시 경로 출력, 실패 시 경고만 (파이프라인 전체 실패는 선택)
- [ ] `npx` 경로: Step 4와 동일하게 `shutil.which("npx")` 등 Windows 고려 (필요 시)

#### B. `test_cases.md` 연동 (선택 2차)

- [ ] TC ID(`TC-\d+`) + 관련 URL이 표에 있는 블록만 파싱해 URL이 서로 다를 때만 추가 스크린샷
- [ ] 파싱 실패 시 A만 수행하고 넘어가기

#### C. Step 4 — 테스트 단위 증거 (선택)

- [ ] `playwright.config.ts`에 `screenshot: 'only-on-failure'` 또는 `trace: 'on-first-retry'` 등
- [ ] 필요 시 `test.info().attach`로 TC ID와 파일 연결

### 구현 시 참고

- 외부 PROD에 짧은 시간에 다수의 스냅샷/스크린샷을 반복 호출하지 않도록 주의.
- 구현 후 [step-03-playwright.md](step-03-playwright.md) 의 Step 3 스크립트 동작 설명을 한 절 보강.

---

## 2. CI (지속 통합)

> **목표**: PR/푸시마다 **Python 단위 테스트(`pytest`)**가 돌아가 회귀를 막는다.  
> JQL·acli·실제 Jira는 CI에서 불필요(현재 테스트도 외부 연동 없음).

### TODO (CI)

- [ ] `.github/workflows/ci.yml` (또는 사용 중인 Git 저장소에 맞는 설정) 추가
- [ ] 트리거: `push` / `pull_request` (기본 브랜치만으로도 충분)
- [ ] 작업: `actions/checkout` → `actions/setup-python` (버전은 `common.md`의 Python과 맞추거나 3.12+ matrix)
- [ ] `pip install -r requirements.txt` → `python -m pytest tests` (또는 `pytest tests -v`)
- [ ] (선택) `playwright` E2E는 브라우저·시간이 필요하므로 **1단계에서는 제외**하고, 주석으로 “추후 `playwright install` + spec” 확장 가능함을 명시

### 구현 시 참고

- 저장소가 GitHub가 아니면 동일 단계를 GitLab CI / Azure Pipelines 등으로 옮기면 됨.
- 구현 후 [common.md](common.md) Environment 절에 **CI 한 줄** 링크 또는 명령 추가.

---

[← 인덱스](README.md)
