"""
Step 2: QA plan → Live page analysis → Test cases markdown.

Flow:
  1. QA 계획서에서 URL, 리스크, Exit Criteria를 추출한다.
  2. playwright-cli로 대상 URL을 직접 방문하여 페이지를 분석한다.
     - 네트워크 요청(API endpoint, 필드명)
     - DOM 구조(주요 선택자, 텍스트, 이미지, 링크, 배지)
     - 상태 표시, 날짜/시간, 가격 등 신뢰 신호
  3. 관찰 결과 + 계획서 정보를 결합하여 test_cases.md를 생성한다.
"""

from pathlib import Path

from lib.state import mark_step_complete, save_state


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────

def read_qa_plan(state: dict) -> str:
    """Read and return the QA plan content."""
    qa_plan_path = Path(state["artifacts"]["qa_plan"])
    if not qa_plan_path.exists():
        raise RuntimeError(f"QA plan not found at {qa_plan_path}. Run step 'plan' first.")
    return qa_plan_path.read_text(encoding="utf-8")


def write_testcases(state: dict, config: dict, content: str) -> dict:
    """Write Claude-generated test cases to output file."""
    output_path = Path(state["artifacts"]["test_cases"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"[Step 2] Test cases written to {output_path}")
    mark_step_complete(state, "testcases")
    save_state(state, config["output"]["base_dir"])
    return state


def build_analysis_prompt(state: dict, qa_plan: str) -> str:
    """
    Build the full prompt that instructs Claude to:
      1. Analyze the live page with playwright-cli
      2. Answer the 6 trust questions based on observation
      3. Generate test cases from the 8 trust axes
    """
    target_url = state.get("target_url", "")
    ticket = state["ticket"]
    output_path = state["artifacts"]["test_cases"]

    url_section = (
        f"대상 URL: {target_url}" if target_url
        else "⚠️  target_url이 비어 있습니다. --url 옵션으로 URL을 지정하세요."
    )

    return f"""
# Step 2 — TC 생성 지시 (티켓: {ticket})

{url_section}
출력 경로: {output_path}

---

## Phase 0 — 실제 페이지 분석 (playwright-cli 사용)

> **이 단계를 건너뛰지 않는다. 문서만 보고 TC를 작성하지 않는다.**
> playwright-cli로 페이지를 직접 방문하여 아래 항목을 모두 관찰하고 기록한다.

### 0-1. 네트워크 분석
playwright-cli로 `{target_url}` 에 접근하면서:
- 발생하는 **XHR/Fetch 요청 URL** 목록을 기록한다
- 주요 API 응답의 **JSON 구조와 필드명**을 확인한다
  - 어떤 필드가 표시 데이터(제목, 가격, 순위, 점수 등)를 담는가
  - 상태를 나타내는 필드(isNew, isOutOfStock, status, rankChange 등)가 있는가
  - 날짜/시간 필드가 있는가
  - 계산된 값(할인가, 합계 등)이 있는가

### 0-2. DOM 구조 분석
- **목록 컨테이너 선택자**: 반복 항목을 감싸는 요소
- **항목 행 선택자**: 각 row/card의 선택자
- **핵심 텍스트 선택자**: 제목, 가격, 순위, 날짜 등이 담긴 요소
- **이미지 선택자**: `<img>` 또는 CSS background 이미지
- **링크 선택자**: 상세 페이지로 이동하는 `<a>` 요소
- **상태 배지/태그 선택자**: 신규, 품절, HOT, 할인 등의 뱃지 요소
- **날짜/시간 표시 선택자**: 기준 시각, 갱신 시각 등

### 0-3. 사용자 인터랙션 포인트 확인
- 클릭 가능한 주요 요소 목록 (버튼, 탭, 필터, 드롭다운 등)
- 폼/검색창이 있는가
- 무한 스크롤 또는 페이지네이션이 있는가
- 스크롤 시 지연 로드(lazy load)되는 이미지가 있는가

### 0-4. 신뢰 신호 확인
- 화면에 날짜/시간이 표시되는가? 어디에, 어떤 형식으로?
- 가격이 있다면 원가/할인가/최종가 구조인가?
- 항목 수(N개), 카운트 등이 표시되는가?
- 특정 상태(품절, 인기, 신규 등) 배지가 있는가?

### 0-5. 관찰 결과 요약 작성
위 분석 결과를 `test_cases.md`의 **Phase 0 관찰 결과** 섹션에 기록한다.
이 정보가 이후 모든 TC의 선택자·필드명·assert값의 근거가 된다.

---

## Phase 1-A — 변경사항 추출 (Change Impact Analysis)

QA 계획서에서 이번 릴리즈의 모든 변경사항을 추출하여 표를 채운다.

| 변경 ID | 변경 영역 | 이전(Before) | 이후(After) | 영향 범위 |
|---------|----------|-------------|------------|----------|
| C-001 | ... | ... | ... | ... |

각 변경사항(C-xxx)에 대해 반드시 두 종류 TC를 생성한다:
- [변경 검증]: After 상태를 직접 측정·수치로 확인
- [변경 회귀]: 변경 영향 범위의 기존 기능이 정상 동작하는지 확인

변경 검증 TC 기대 결과 기준:
  ❌ "변경이 적용되었다"
  ✅ "Cache-Control: max-age=180 (TTL 3분 = 180초 반영)"
  ✅ "score = streaming×0.6 + likes×0.2 + shares×0.2 (fixture 비교)"

---

## Phase 1-B — 서비스 분석 질문 (관찰 결과 기반 답변)

Phase 0 관찰 결과를 바탕으로 아래 6가지 질문에 답한다.
**추측이 아닌 실제 관찰한 내용으로 답해야 한다.**

Q1. 이 서비스에서 사용자가 가장 믿어야 하는 핵심 데이터는?
  → Phase 0에서 확인한 API 필드명을 명시한다.

Q2. 사용자가 수행하는 핵심 액션 3가지는?
  → Phase 0에서 확인한 실제 인터랙션 요소 기반으로 답한다.

Q3. 상태를 사용자에게 어떻게 알려주는가?
  → Phase 0에서 확인한 배지/태그 요소와 API 필드를 연결한다.

Q4. 이 서비스의 데이터는 언제 기준인가? 사용자가 알 수 있는가?
  → Phase 0에서 날짜 표시 요소를 관찰한 결과를 답한다.

Q5. 금전적·법적·안전 책임이 있는 데이터는?
  → Phase 0에서 가격·합계·계산값 필드를 확인한 결과를 답한다.

Q6. 외부 의존성(API, 캐시, CDN) 실패 지점은?
  → Phase 0에서 확인한 XHR 요청 목록 기반으로 답한다.

---

## Phase 2 — TC 목록 생성

`templates/test_cases.md` 구조를 따라 TC를 작성한다.
**TC는 그룹 A (변경 검증)를 먼저, 그룹 B (신뢰 축)를 이후에 배치한다.**

그룹 A: Phase 1-A의 각 C-xxx에 대해
  - [변경 검증] TC: After 값을 직접 측정, Before/After 표 포함
  - [변경 회귀] TC: 영향 범위의 기존 기능 정상 동작 확인

그룹 B: Phase 1-B 답변 기반 8대 신뢰 축 TC

**공통 핵심 규칙:**
- Phase 0에서 관찰한 **실제 선택자·API 필드명·DOM 구조**를 TC의 절차와 assert에 직접 사용한다
  - 예: "`.lst50 .checkT` 체크박스 요소" (추측 선택자 금지)
  - 예: "`rank` 필드" (API 분석에서 확인한 실제 필드명)
- 기대 결과는 **수치·DOM 조건**으로 명시한다 ("일치한다" 금지)
- 자동화 매핑의 assert 예시는 Phase 0에서 확인한 실제 선택자를 사용한다

8대 신뢰 축을 커버하는 TC를 작성한다:
  축 1 진실성 — API값 = UI값 (실제 필드명으로 비교)
  축 2 완전성 — 항목 수·누락 없음 (실제 선택자로 count)
  축 3 정확성 — 계산·정렬·매핑 (Phase 0에서 확인한 계산 필드 기반)
  축 4 신뢰 신호 — 상태·날짜·배지 (Phase 0에서 관찰한 요소 기반)
  축 5 안정성 — 브라우저·기기·새로고침
  축 6 복원력 — 5xx·빈결과·null·오프라인·이미지·JS에러
  축 7 성능 — SLA 수치·LCP
  축 8 접근성 — 키보드·포커스·alt

---

## Phase 3 — 검증 및 저장

1. 추적성 매트릭스: 계획서의 모든 리스크·Exit Criteria가 TC에 연결되었는지 확인
2. 기대 결과 품질: "일치한다", "정상 표시된다" 등의 모호한 표현 제거
3. 자동화 매핑: 스펙 파일명·POM 메서드명·assert 예시 기입 완료
4. 우선순위 요약 테이블 작성

완료 후 `{output_path}` 에 저장한다.

---

## 참고: QA 계획서 내용

{qa_plan}
"""


# ──────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────

def run(state: dict, config: dict) -> dict:
    """
    Step 2 entry point.

    Prints a structured prompt that instructs Claude Code to:
      - Use playwright-cli to analyze the target URL
      - Answer 6 trust questions based on live observation
      - Generate test cases from 8 trust axes using actual selectors/field names
    """
    ticket = state["ticket"]
    target_url = state.get("target_url", "")

    print(f"[Step 2] Ticket: {ticket}")
    print(f"[Step 2] Target URL: {target_url or '(없음 — --url 옵션 필요)'}")
    print(f"[Step 2] QA plan: {state['artifacts']['qa_plan']}")
    print(f"[Step 2] Output: {state['artifacts']['test_cases']}")

    if not target_url:
        print("[Step 2] ⚠️  target_url 없음. playwright 분석을 건너뛰고 계획서 기반으로만 진행됩니다.")
        print("[Step 2] 권장: python workflow_runner.py --ticket {ticket} --step testcases --url <URL>")

    qa_plan = read_qa_plan(state)

    prompt = build_analysis_prompt(state, qa_plan)
    print("\n" + "=" * 60)
    print(prompt)
    print("=" * 60)

    return state
